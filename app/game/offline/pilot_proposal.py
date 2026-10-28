"""Prepare explicitly UNAPPROVED fitting inputs from the collected pilot, without LP fitting."""
import argparse
import json
import math
from pathlib import Path


def propose(directory):
    from app.game.offline.collection import RecordingBundle, export_training, completeness
    from app.game.offline.calibration import CalibrationArtifact, read_json
    from app.game.models import capture_context
    from app.game.execution_contract import ExecutionContract
    from app.game.offline.attacks import AttackSpecification
    from app.game.offline.evaluation import bind_evaluation
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.research.readiness import check_readiness
    from app.reputation.reputation_manager import ReputationManager
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.verifiers.base_verifier import BaseVerifier
    directory=Path(directory)
    # No custody path or final payload is opened in this command.
    bundle=RecordingBundle.model_validate(read_json(directory/'collection'/'recordings.json'))
    if not completeness(bundle)['complete']:
        raise ValueError('pilot collection incomplete; proposal export blocked')
    calibration=CalibrationArtifact.model_validate(read_json(directory/'calibration.json'))
    expected_measurements=read_json(directory/'collection'/'measurements.json')
    if calibration.request.measurements.model_dump(mode='json') != expected_measurements:
        raise ValueError('calibration is not from this exact collected measurement bundle')
    if (calibration.request.final_test_reservation != bundle.request.final_test_reservation
            or set(calibration.request.required_verifiers) != {c.verifier_name for c in bundle.request.candidates}
            or not calibration.request.include_warmups):
        raise ValueError('pilot calibration must match the reservation/roster and retain all attempts')
    budget=math.fsum(row['attempt_cost'] for row in calibration.result['estimates'])
    if budget <= 0:
        raise ValueError('measured positive total attempt cost is required')
    # Proposed priors only; this new in-memory manager has no production reference.
    manager=ReputationManager(prior_alpha=1.,prior_beta=1.)
    labels={e.run_id:e for e in bundle.request.examples if e.role=='history'}
    for row in bundle.attempts:
        if row.run_id in labels and row.attempt.state=='directional':
            e=labels[row.run_id]
            manager.update_from_ground_truth(row.candidate,e.analysis.domain,
                row.attempt.report.passed,e.label.answer_is_correct)
    class RecordedCandidateHandle(BaseVerifier):
        """Registration metadata only: no report or resource can be generated here."""
        def __init__(self,name): self._name=name
        @property
        def name(self): return self._name
        def verify(self,*args,**kwargs): raise RuntimeError('planning-only recorded candidate handle')
    names=tuple(c.verifier_name for c in bundle.request.candidates)
    selector=VerifierSelector(verifiers=[RecordedCandidateHandle(n) for n in names],
        reputation_manager=manager,capabilities={n:BUILTIN_CAPABILITIES[n] for n in names},
        difficulty_range={'easy':(2,2),'medium':(2,2),'hard':(2,2)})
    first=bundle.request.examples[0]
    attacks=AttackSpecification(version='report_corruption_v1',suppression='unavailable')
    datasets=dict(bundle.request.permitted_datasets)
    reservation=bundle.request.final_test_reservation
    context=capture_context(selector,first.analysis,context=first.reference,
        attempt_costs=tuple((r['verifier_name'],r['attempt_cost']) for r in calibration.result['estimates']),
        budget=budget,cost_units='ms',
        loss_configuration=dict(version='proposed-pilot-loss-v1',false_accept=1.,false_reject=1.,
            uncertain=.2,resource_weight=.1/budget,cost_units='ms'),
        dependencies=dict(version='proposed-pilot-dependencies-v1',dependencies=(),unresolved=names,
                          unknown_treatment='shared_unknown'),
        aggregation_versions=(('reputation_weighted','log_odds_v1'),('dependency_group','groups_v1')),
        provenance=dict(attack_specification=attacks.specification_id,history_dataset=datasets['history'],
            development_dataset=datasets['development'],final_test_dataset=reservation.dataset_id,
            matrix_version='constructed-pilot-development-v1',loss_configuration='proposed-pilot-loss-v1',
            category=first.analysis.domain,evidence_kind='empirical'))
    manifest=export_training(bundle,context)
    contract=ExecutionContract(version='offline_public_decision_v2',coverage_version='factual_output_contract_v1',
        contributor_version='baseline_log_odds_active_group_v1',threshold=.55,
        failure_contract='all_selected_returned',execution_configuration_id=bundle.request.execution_configuration_id,
        resource_manifest=bundle.observed_setup.resources,history_prior_alpha=1.,history_prior_beta=1.)
    bound=bind_evaluation(context,manifest,contract,attacks)  # independent history/resource validation; no solver
    resources=bundle.observed_setup.resources
    descriptions=[]
    for role in ('history','development','final_test'):
        descriptions.append(dict(role=role,dataset_id=manifest.partition(role).dataset_id,
            version='constructed_arithmetic_fraction_v1',source='Explicitly constructed engineering pilot; not an external benchmark',
            independent_label_provenance='Exact Fraction arithmetic/long division, not framework judgments; procedural holdout',
            declared_label_sources=('constructed_arithmetic_fraction_v1',),
            grouping_protocol='Seed42 shuffle of 60 expression groups; both answer variants remain in the same split'))
    spec=PolicyBuildSpecification(version='offline_policy_build_v1',study_id='constructed-arithmetic-pilot42',
        configuration_version='UNAPPROVED-proposal-v1',code_revision=bundle.observed_setup.code_revision,
        setting_role='primary',primary_specification_id=None,
        scientific_scope='Reference-assisted constructed one-operation arithmetic; real local rule/semantic adapters; no external benchmark or evidence robustness claim',
        primary_outcomes=('worst_case_expected_loss','decision_coverage'),
        sensitivity_plan=('No tuning in this engineering pilot; a later sensitivity study requires separate approval.',),
        matched_coverage_plan='Fixed proposed threshold 0.55; no matched-coverage target or superiority claim.',
        final_test_custody_and_freeze_protocol='Procedural holdout created in this workflow, not third-party custody. Freeze approved complete policy/configuration before any final collection/evaluation.',
        datasets=tuple(descriptions),recording=dict(execution_configuration_id=contract.execution_configuration_id,
            model_fingerprints=tuple((v.verifier_name+':'+r.resource_id,r.sha256)
                for v in resources.verifiers for r in v.resources if r.kind=='model'),
            corpus_fingerprints=(('not_applicable','No evidence/retrieval/corpus adapter in this narrower pilot'),),
            prompt_and_adapter_fingerprints=tuple((v.verifier_name+':'+r.kind+':'+r.resource_id,r.sha256)
                for v in resources.verifiers for r in v.resources if r.kind in {'implementation','configuration'}),
            collection_protocol='complete_team_independent_v1'),context=bound,manifest=manifest,contract=contract,attacks=attacks,
        unknown_dependency_treatment='shared_unknown',greedy_aggregation='reputation_weighted',
        policy_sampling_seeds=(42,),policy_sampling_repetitions=1,
        uncertainty=dict(method='paired_split_identity_cluster_percentile_v1',resamples=2000,confidence_level=.95,seed=42),
        optimizer_tolerance=1e-8)
    readiness=check_readiness(spec,actual_code_revision=bundle.observed_setup.code_revision)
    output=directory/'proposed'
    output.mkdir(exist_ok=False)
    (output/'training-manifest.json').write_text(manifest.model_dump_json(indent=2),encoding='utf-8')
    (output/'context.json').write_text(bound.model_dump_json(indent=2),encoding='utf-8')
    # Wrapper intentionally fails the builder schema. Extract the nested spec ONLY
    # after explicit user approval; no valid deployable PolicyArtifact is created.
    wrapper=dict(approval_status='UNAPPROVED; fitting must wait for user decision',policy_created=False,
        calibration_id=calibration.calibration_id,source_bundle_id=bundle.bundle_id,
        proposed_values=dict(false_accept=1.,false_reject=1.,uncertain=.2,resource_weight_per_ms=.1/budget,
            budget_ms=budget,threshold=.55,history_prior_alpha=1.,history_prior_beta=1.,minimum_participants=2,
            attack_version='report_corruption_v1',suppression='unavailable',unknown_treatment='shared_unknown'),
        readiness=readiness.model_dump(mode='json'),policy_build_specification=spec.model_dump(mode='json'))
    (output/'fitting-proposal.UNAPPROVED.json').write_text(json.dumps(wrapper,indent=2),encoding='utf-8')
    # Persist first/subsequent-call facts without pretending to measure cache warmth.
    counters={}
    annotations=[]
    for row in bundle.attempts:
        counters[row.candidate]=counters.get(row.candidate,0)+1
        annotations.append(dict(attempt_id=row.attempt_id,run_id=row.run_id,verifier_name=row.candidate,
            invocation_ordinal=counters[row.candidate],thermal_state=('first_measured_call_after_eager_initialization'
                if counters[row.candidate]==1 else 'subsequent_measured_call_cache_temperature_not_measured'),
            included_in_calibration=True,duration_ms=row.duration_ms))
    (directory/'attempt-temperature-annotations.json').write_text(json.dumps(dict(
        model_initialization_in_attempt_timer=False,warmups_excluded=0,attempts=annotations),indent=2),encoding='utf-8')
    return dict(policy_created=False,approval_required=True,calibration_id=calibration.calibration_id,
        proposed_values=wrapper['proposed_values'],readiness=readiness.ready,blockers=readiness.blockers,
        output=str(output/'fitting-proposal.UNAPPROVED.json'))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args(argv)
    print(json.dumps(propose(args.directory),indent=2))
    return 0


if __name__=='__main__': main()
