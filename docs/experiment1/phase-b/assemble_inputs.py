"""Readiness-only Phase B assembly. Never replay, optimize, or read final payloads.

Canonical inputs are referenced and checked, never reconstructed from redactions.
Outputs live only beside this file. Historical/expanded comparisons stay separate.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from app.game.artifacts import PolicyArtifact, artifact_version
from app.game.component_execution import ComponentPolicy, enumerate_component_strategies
from app.game.execution_contract import ExecutionContract
from app.game.models import PlanningContext, content_id
from app.game.offline.attacks import AttackSpecification, enumerate_attacks
from app.game.offline.collection import RecordingBundle, completeness
from app.game.offline.compound import JointRecordings
from app.game.offline.evaluation import bind_evaluation
from app.game.offline.records import FinalTestReservation, TrainingManifest
from app.game.research.comparison import deterministic_id
from app.game.research.experiment1.manifest import (
    ExperimentManifest, BlockedEntry, InfeasibleEntry, source_fingerprint,
)
from app.game.resource_provenance import ResourceManifest, validate_recorded_resources
from app.game.strategies import enumerate_strategies

OUT = Path(__file__).resolve().parent
READS = {}

# No catch-all dataset loader. All accepted data paths have an explicit role.
EXACT = {
    'artifacts/publication-v1/owned-files.json',
    'artifacts/publication-v1/publication-record.json',
    'artifacts/publication-v1/file-hashes-v3.json',
    'artifacts/compound-study-36-v1/execution-source-custody.json',
    'artifacts/compound-study-36-v1/preparation/predeclared-intent.json',
    'artifacts/compound-study-36-v1/attacks.json',
    'artifacts/compound-study-36-v1/history/joint.json',
    'artifacts/compound-study-36-v1/development/joint.json',
    'artifacts/remaining-category-studies-v1/scoped-er-v1/transfer.json',
    'artifacts/remaining-category-studies-v1/compound-85/amendment.json',
    'artifacts/remaining-category-studies-v1/compound-85/candidate/policy.json',
    'artifacts/remaining-category-studies-v1/compound-85/candidate/inventory.json',
    'artifacts/remaining-category-studies-v1/reference-50-v1/fit/policy.json',
    'artifacts/remaining-category-studies-v1/reference-50-v1/training/reference/bundle.json',
    'artifacts/remaining-category-studies-v1/reference-50-v1/fit/training-manifest.json',
    'artifacts/remaining-category-studies-v1/reference-50-v1/fit/development-evaluation.json',
    'artifacts/remaining-category-studies-v1/reference-50-v1/fit/contract.json',
    'artifacts/remaining-category-studies-v1/reference-50-v1/protocol.json',
    'artifacts/remaining-category-studies-v1/reference-50-v1/amendment.json',
    'artifacts/remaining-category-studies-v1/reference-50-v1/reserved-seal.json',
    'artifacts/remaining-category-studies-v1/reference-50-v1/fit-report-note.json',
    'artifacts/flexible-heldout-v1/evaluation-specification.json',
    'artifacts/flexible-heldout-v1/evaluation-code-seal.json',
    # This view supplies LOCATORS only. It never satisfies canonical custody.
    'artifacts/publication-v1/public-audit/artifacts/flexible-heldout-v1/freeze-manifest.json',
}
for cohort in ('arithmetic', 'factual'):
    EXACT.update(f'artifacts/flexible-heldout-v1/{cohort}/{f}.json' for f in
        ('policy', 'context', 'contract', 'attacks', 'reservation', 'baselines'))
    EXACT.add(f'artifacts/flexible-heldout-v1/{cohort}/collection/observed-setup.json')
EXACT.update(f'artifacts/flexible-teams-v1/semantic-minimum-1/{f}.json' for f in
    ('matrix', 'solution', 'context', 'contract', 'summary'))


def load(relative):
    if relative not in EXACT:
        raise ValueError('not an allowed readiness input: ' + relative)
    data = (ROOT / relative).read_bytes()
    READS[relative] = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
        role='noncanonical_locator_only' if '/public-audit/' in relative else 'canonical_metadata_or_training')
    return json.loads(data)


def digest(relative):
    """Only hash extra declared SOURCE files, never final data or arbitrary paths."""
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or path.suffix != '.py':
        raise ValueError('extra digest must be repository Python source')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def missing(relative, registry):
    item = dict(path=relative, exists=(ROOT / relative).is_file(),
        expected_original_sha256=None, expected_hash_source=None)
    if relative in registry:
        record = registry[relative]
        item.update(expected_original_sha256=record['original_sha256'],
            expected_hash_source='artifacts/publication-v1/owned-files.json',
            redacted_view=record['public_path'], redacted_view_sha256=record['public_sha256'],
            replacement_permitted=False, rule=record['effects'])
    return item


def actions(context, attacks):
    return [a.model_dump(mode='json') | {'attack_id': a.attack_id}
            for a in enumerate_attacks(context.dependencies, attacks)]


def artifact_summary(artifact):
    c, p, k = artifact.context, artifact.policy, artifact.contract
    return dict(policy_id=p.policy_id, artifact_id=artifact.artifact_id, context_id=c.compatibility_id,
        matrix_id=p.matrix.matrix_id, resource_id=artifact.execution_configuration_id,
        contract_content_id=content_id(k.model_dump(mode='json')), reputation_id=c.reputation_snapshot_id,
        provenance=c.provenance.model_dump(mode='json'), team_requirements=k.team_requirements.model_dump(mode='json'),
        threshold=k.threshold, coverage_floor=p.matrix.clean_coverage.minimum,
        budget=c.budget, cost_units=c.cost_units, attempt_costs=c.attempt_costs,
        loss=c.loss_configuration.model_dump(mode='json'), dependencies=c.dependencies.model_dump(mode='json'),
        execution_contract=k.model_dump(mode='json'), aggregation_versions=c.aggregation_versions,
        feasible_strategies=[s.model_dump(mode='json') for s in p.strategies],
        probabilities=p.solution.probabilities, solver_certificate_status='validated_without_optimizer')


def assemble():
    READS.clear()
    registry_doc = load('artifacts/publication-v1/owned-files.json')
    registry = {r['original_path']: r for r in registry_doc['derived_public_views']}
    publication = load('artifacts/publication-v1/publication-record.json')
    publication_inventory=load('artifacts/publication-v1/file-hashes-v3.json')
    specification = load('artifacts/flexible-heldout-v1/evaluation-specification.json')
    locator = load('artifacts/publication-v1/public-audit/artifacts/flexible-heldout-v1/freeze-manifest.json')
    evidence = {}
    for cohort in ('arithmetic', 'factual'):
        folder = f'artifacts/flexible-heldout-v1/{cohort}'
        c = PlanningContext.model_validate(load(folder + '/context.json'))
        k = ExecutionContract.model_validate(load(folder + '/contract.json'))
        p = load(folder + '/policy.json')
        artifact = PolicyArtifact(version=artifact_version(c, __import__('app.game.policy', fromlist=['Policy']).Policy.model_validate(p)),
            policy=p, context=c, contract=k, execution_configuration_id=k.execution_configuration_id, applicable_domain=c.plan.domain)
        a = AttackSpecification.model_validate(load(folder + '/attacks.json'))
        r = FinalTestReservation.model_validate(load(folder + '/reservation.json'))
        baseline = load(folder + '/baselines.json')
        definitions = {s.strategy_id:s for s in enumerate_strategies(c).strategies}
        for name in ('development_best', 'greedy'):
            assert definitions[baseline[name]['strategy_id']].model_dump(mode='json') == baseline[name]
        chosen = deterministic_id(artifact.policy.matrix, clean=False, tolerance=artifact.policy.solution.tolerance)
        assert artifact.policy.matrix.strategy_ids[chosen] == baseline['development_best']['strategy_id']
        observed = load(folder + '/collection/observed-setup.json')
        assert ResourceManifest.model_validate(observed['resources']) == k.resource_manifest
        original = next(x for x in locator['candidates'] if x['cohort'] == cohort)
        expected = next(x for x in specification['cohorts'] if x['cohort'] == cohort)
        assert artifact.policy.policy_id == expected['policy_id'] == original['policy_id']
        assert r.reservation_id == expected['reservation_id']
        miss = [missing(path, registry) for path in (
            f'build/multitask-policy42/{cohort}/training-manifest.json',
            f'build/multitask-policy42/{cohort}/development-evaluation.json',
            'artifacts/flexible-heldout-v1/freeze-manifest.json',
            'artifacts/flexible-heldout-v1/precollection-seal.json',
            'artifacts/flexible-teams-v1/input-hashes.json')]
        evidence[cohort] = dict(**artifact_summary(artifact), paths={f:folder+'/'+f+'.json' for f in
            ('policy','context','contract','attacks','reservation','baselines')},
            partition_ids={role:getattr(c.provenance, role+'_dataset') for role in ('history','development','final_test')},
            grouping=dict(final_reserved_pairs=[(e.example_id,e.split_identity) for e in r.examples],
                final_examples=len(r.examples), final_groups=len({e.split_identity for e in r.examples}),
                history_binding=json.loads(c.task_conditioning_json),
                history_development_group_lists='unavailable_without_canonical_training_manifest'),
            reservation_id=r.reservation_id, custody_record=r.custody_record,
            recorded_collection_source_commit=observed['code_revision'],
            recorded_collection_source_digest=observed['application_source_digest'],
            recorded_final_resource_metadata_matches=True, live_resources='not_observed_or_used',
            freeze_id_from_internal_evaluation_specification=specification['freeze_id'],
            canonical_freeze_verified=False, missing=miss,
            locator_only_training_sha256=original['training_sha256'],
            locator_only_training_manifest_id=original['training_manifest_id'],
            historical_comparison=dict(classification='original_three_method_internal_freeze_documentation; canonical_custody_verification_blocked',
                methods=specification['primary_methods'], baselines=baseline, statistics=specification['uncertainty'],
                metric_definitions=specification['metrics'], source='artifacts/flexible-heldout-v1/evaluation-specification.json'),
            retrospective_comparison=dict(classification='expanded_methods_are_retrospective_not_preregistered',
                complete_comparison_freeze='missing', uniform='not_instantiated', restricted_games='no_saved_certificates_found; optimization_not_authorized_in_Phase_B'),
            blockers=['canonical_training_and_development_inputs_missing','canonical_internal_freeze_and_seals_missing',
                      'reviewed_training_only_research_specification_missing','expanded_frozen_comparison_missing'])
    # Reference: authentic training data and outcome-free reservation, never test bundle.
    folder = 'artifacts/remaining-category-studies-v1/reference-50-v1'
    artifact = PolicyArtifact.model_validate(load(folder+'/fit/policy.json'))
    training = TrainingManifest.model_validate(load(folder+'/fit/training-manifest.json'))
    bundle=RecordingBundle.model_validate(load(folder+'/training/reference/bundle.json'))
    assert completeness(bundle)['complete'] and bundle.observed_setup.resources==artifact.contract.resource_manifest
    assert {e.role for e in bundle.request.examples} == {'history','development'}
    protocol = load(folder+'/protocol.json')
    attack = AttackSpecification.model_validate(protocol['attacks'])
    assert bind_evaluation(artifact.context,training,artifact.contract,attack) == artifact.context
    contract = ExecutionContract.model_validate(load(folder+'/fit/contract.json'))
    assert contract == artifact.contract
    seal = load(folder+'/reserved-seal.json'); amendment=load(folder+'/amendment.json')
    assert seal['freeze_sha256'] == registry[folder+'/fit/freeze.json']['original_sha256']
    assert artifact.policy.matrix.clean_coverage.minimum == protocol['minimum_clean_development_coverage'] == amendment['new_minimum'] == .5
    weights = dict(artifact.policy.solution.probabilities)
    positive = [(s.verifiers,weights[s.strategy_id]) for s in artifact.policy.strategies if weights[s.strategy_id] > 0]
    assert positive == [(('semantic',), .16666666666666663), (('confidence','semantic'), .8333333333333334)]
    # Load original DEVELOPMENT evaluation for identity validation only; no replay/selection.
    from app.game.offline.evaluation import Evaluation
    development=Evaluation.model_validate(load(folder+'/fit/development-evaluation.json'))
    assert development.role=='development' and development.manifest_id==training.manifest_id
    assert development.contract==contract and development.attacks==attack
    greedy = [s.model_dump(mode='json') for s in artifact.policy.strategies
              if s.verifiers==tuple(sorted(artifact.context.plan.initial_selected)) and s.aggregation=='reputation_weighted']
    evidence['reference']=dict(**artifact_summary(artifact),
        paths=dict(policy=folder+'/fit/policy.json',training=folder+'/fit/training-manifest.json',
            development=folder+'/fit/development-evaluation.json',contract=folder+'/fit/contract.json',
            protocol=folder+'/protocol.json',reserved_seal=folder+'/reserved-seal.json'),
        training_manifest_id=training.manifest_id, recorded_resources_and_history_binding='validated_without_replay',
        partitions=[dict(role=p.role,dataset_id=p.dataset_id,examples=len(p.examples),groups=len({e.split_identity for e in p.examples}),
            example_groups=[(e.example_id,e.split_identity) for e in p.examples]) for p in (*training.partitions,training.final_test_reservation)],
        reservation_id=training.final_test_reservation.reservation_id, custody_record=training.final_test_reservation.custody_record,
        reserved_seal=seal, amendment=amendment, source_binding=artifact.context.provenance.model_dump(mode='json'),
        source_commit=bundle.observed_setup.code_revision,
        recorded_source_digest=bundle.observed_setup.application_source_digest,
        training_bundle_id=bundle.bundle_id if hasattr(bundle,'bundle_id') else content_id(bundle.model_dump(mode='json')),
        final_request_presence_only=dict(path=folder+'/reserved-request.json',exists=(ROOT/folder/'reserved-request.json').exists(),
            expected_sha256=seal['request_sha256'],hash_verified=False,opened=False),
        historical_comparison=dict(classification='original_reference_exploratory_post_development_floor',
            methods=['full_frozen_policy','development_best_fixed','captured_greedy'], fixed_rule=protocol['fixed_baseline'],
            fixed_strategy_identity='unverified_without_canonical_fit/freeze.json',captured_greedy=greedy,
            statistics=protocol['uncertainty']),
        retrospective_comparison=dict(classification='expanded_comparison_not_preregistered', complete_comparison_freeze='missing'),
        release_status='reserved-seal metadata only; final request/bundle/payload not opened',
        missing=[missing(folder+'/'+p,registry) for p in ('seal.json','fit/freeze.json')],
        blockers=['canonical_training_seal_and_policy_freeze_missing','reviewed_research_specification_missing','expanded_frozen_comparison_missing'])
    # Compound: pure policy, transfer and history/development bundle checks only.
    folder='artifacts/remaining-category-studies-v1/compound-85/candidate'
    policy=ComponentPolicy.model_validate(load(folder+'/policy.json'))
    inventory=load(folder+'/inventory.json')
    assert inventory['policy.json']==READS[folder+'/policy.json']['sha256']
    transfer=load('artifacts/remaining-category-studies-v1/scoped-er-v1/transfer.json')
    assert content_id({k:v for k,v in transfer.items() if k!='transfer_id'})==transfer['transfer_id']
    assert transfer['original_policy_id']==policy.policy_id
    full=policy.contract.actual_resources
    assert full.manifest_id==transfer['original_full_resource_id']
    scoped=ResourceManifest.model_validate(transfer['scoped_setup']['resources'])
    assert scoped.verifiers==tuple(v for v in full.verifiers if v.verifier_name in {'evidence','rule'})
    assert scoped.manifest_id==transfer['scoped_resource_id']
    source_checks={p:digest(p)==h for p,h in transfer['code_hashes'].items()}
    assert all(source_checks.values())
    partitions=[]; source_setups=[]
    for role in ('history','development'):
        relative=f'artifacts/compound-study-36-v1/{role}/joint.json'
        joint=JointRecordings.model_validate(load(relative));assert joint.role==role
        components=[]
        for cid,bundle in joint.bundles:
            assert completeness(bundle)['complete']
            assert bundle.observed_setup.resources == full
            obligation=next(o for o in policy.contract.obligations if o.component_id==cid)
            for attempt in bundle.attempts:
                if attempt.executed:
                    observation=next(v for v in full.verifiers if v.verifier_name==attempt.candidate)
                    assert json.loads(attempt.attempt.observed_resources_json)==observation.model_dump(mode='json')
            components.append(dict(component_id=cid, examples=len(bundle.request.examples),
                groups=len({e.split_identity for e in bundle.request.examples}),
                datasets=bundle.request.permitted_datasets,
                example_groups=[(e.example_id,e.split_identity) for e in bundle.request.examples]))
            source_setups.append(dict(commit=bundle.observed_setup.code_revision,digest=bundle.observed_setup.application_source_digest))
        partitions.append(dict(role=role,path=relative,components=components))
    amendment=load('artifacts/remaining-category-studies-v1/compound-85/amendment.json')
    intent=load('artifacts/compound-study-36-v1/preparation/predeclared-intent.json')
    custody=load('artifacts/compound-study-36-v1/execution-source-custody.json')
    assert policy.matrix.clean_coverage.minimum == policy.contract.fitting_configuration.minimum_clean_coverage == .85
    evidence['compound']=dict(policy_id=policy.policy_id, contract_id=policy.contract.compatibility_id,
        matrix_id=policy.matrix.matrix_id, probabilities=policy.solution.probabilities,
        full_resource_id=full.manifest_id, scoped_resource_id=scoped.manifest_id,
        transfer_id=transfer['transfer_id'], original_freeze_id=transfer['original_freeze_id'],
        transfer_authorization=transfer['authorization'], transfer_source_checks=source_checks,
        source_setups=source_setups, source_custody=dict(path='artifacts/compound-study-36-v1/'+custody['custody_archive'],
            expected_sha256=custody['archive_sha256'],exists=(ROOT/'artifacts/compound-study-36-v1'/custody['custody_archive']).exists()),
        joint_development=policy.joint_development.model_dump(mode='json'), partitions=partitions,
        coverage_floor=.85, threshold=[o.contract.threshold for o in policy.contract.obligations],
        obligations=[o.model_dump(mode='json') for o in policy.contract.obligations],
        strategies=[s.model_dump(mode='json') for s in enumerate_component_strategies(policy.contract)],
        paths=dict(policy=folder+'/policy.json',transfer='artifacts/remaining-category-studies-v1/scoped-er-v1/transfer.json'),
        amendment=amendment, historical_comparison=dict(classification='exploratory_post_development_85_percent',
            methods=['full_frozen_joint_policy','development_best_fixed_joint_plan'],
            statistics=dict(repetitions=intent['bootstrap_replicates'],seed=intent['bootstrap_seed']),
            greedy='excluded_no_independently_defined_comparable_component_executor'),
        retrospective_comparison=dict(classification='expanded_comparison_not_preregistered',complete_comparison_freeze='missing',greedy='unavailable'),
        missing=[missing(p,registry) for p in ('artifacts/compound-study-36-v1/preparation/study.json',
            'artifacts/compound-study-36-v1/preparation-seal.json',folder+'/freeze.json')],
        blockers=['canonical_study_and_preparation_seal_missing','canonical_candidate_freeze_missing','expanded_component_comparison_missing'])
    sem='artifacts/flexible-teams-v1/semantic-minimum-1'
    semantic=InfeasibleEntry(matrix=load(sem+'/matrix.json'),solution=load(sem+'/solution.json'),
        explanation='Original Semantic remains infeasible at 0.90; no substitute Reference policy.')
    sem_context=PlanningContext.model_validate(load(sem+'/context.json'))
    sem_contract=ExecutionContract.model_validate(load(sem+'/contract.json'))
    evidence['original_semantic']=dict(status='infeasible',minimum=.9,policy_id=None,
        provenance=sem_context.provenance.model_dump(mode='json'),
        resource_id=sem_contract.execution_configuration_id,threshold=sem_contract.threshold,
        history_binding=json.loads(sem_context.task_conditioning_json),
        partition_ids={role:getattr(sem_context.provenance,role+'_dataset') for role in ('history','development','final_test')},
        maximum_stored_development_coverage=max(v for _,v in semantic.matrix.clean_coverage.strategy_coverage),
        matrix_id=semantic.matrix.matrix_id, probabilities=semantic.solution.probabilities,
        paths=dict(matrix=sem+'/matrix.json',solution=sem+'/solution.json',context=sem+'/context.json',contract=sem+'/contract.json'),
        missing=[],blockers=[],comparison='excluded_no_qualifying_fitted_policy')
    missing_paths=sorted({record['path'] for item in evidence.values() for record in item.get('missing',[])})
    git_search={relative:subprocess.check_output(['git','log','--all','--format=%H','--',relative],cwd=ROOT,text=True).splitlines() for relative in missing_paths}
    publication_object=subprocess.run(['git','cat-file','-t',publication['content_commit']],cwd=ROOT,text=True,capture_output=True)
    for relative,record in READS.items():
        expected=publication_inventory.get(relative,{}).get('sha256')
        record['publication_sha256']=expected
        record['matches_publication_inventory']=record['sha256']==expected if expected else None
        if expected is not None:
            assert record['sha256']==expected, 'published input bytes changed: '+relative
    data=dict(version='experiment1_phase_b_input_inventory_v1',
        local_git_search=git_search, publication_content_commit_available=(publication_object.returncode==0),
        acquisition_attempts='local repository/ignored build paths and local Git refs only; no network requests',
        assembler_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        assembly_source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_fingerprint=source_fingerprint(ROOT), publication=publication,
        canonical_acquisition_rule=registry_doc['canonical_audit_acquisition'],
        input_files=READS.copy(), cohorts=evidence, semantic_disposition=semantic.model_dump(mode='json'),
        final_outcome_payloads_opened=[], final_scoring=False, optimization=False,
        note='Redacted view used only for unavailable training locators, never canonical substitution. Final requests, reports, bundles, outcomes and scored release files were not read.')
    return data


def write_outputs():
    data=assemble()
    identity=content_id(data)
    def save(name,value):
        (OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
    save('input-inventory.json',data | {'inventory_id':identity})
    historical={c:values.get('historical_comparison') for c,values in data['cohorts'].items() if 'historical_comparison' in values}
    save('historical-comparisons.json',dict(version='historical_comparisons_metadata_only_v1',inventory_id=identity,
        no_new_preregistration_claim=True, cohorts=historical))
    semantic=InfeasibleEntry.model_validate(data['semantic_disposition'])
    entries=[]
    for cohort in ('arithmetic','factual','compound','reference'):
        e=data['cohorts'][cohort]
        entries.append(BlockedEntry(cohort=cohort,expected_policy_id=e['policy_id'],
            reason=f"input-inventory.json#{identity}: "+'; '.join(e['blockers'])+
                '. Canonical records must be supplied; no fitting or redaction substitution is authorized.'))
    entries.append(semantic)
    manifest=ExperimentManifest(experiment_id='experiment1-real-cohort-phase-b-candidate',
        source_commit=data['assembly_source_commit'],source_fingerprint=data['source_fingerprint'],cohorts=tuple(entries))
    save('experiment1-candidate.json',manifest.model_dump(mode='json'))
    # Per-cohort candidates preserve all five dispositions (schema requires them).
    for cohort in data['cohorts']:
        candidate=ExperimentManifest(**{**manifest.model_dump(),'experiment_id':'experiment1-phase-b-'+cohort+'-candidate'})
        save(cohort+'-candidate.json',candidate.model_dump(mode='json'))
    save('readiness-inputs.json',dict(inventory_id=identity,
        candidates=['experiment1-candidate.json']+[c+'-candidate.json' for c in data['cohorts']],
        expected_disposition={c:'infeasible_excluded' if c=='original_semantic' else 'blocked' for c in data['cohorts']},
        no_final_payload_access=True))
    print(json.dumps(dict(inventory_id=identity,metadata_or_training_files_read=len(READS),final_payloads_read=0,
        cohorts={c:e.get('blockers',[]) for c,e in data['cohorts'].items()}),indent=2))


if __name__=='__main__':
    write_outputs()
