"""Package approved existing policies byte-for-byte. Never fit or load models."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import json
import sys
import zipfile
from app.game.artifacts import PolicyArtifact,DeploymentEpisode
from app.game.prototype_bundle import PrototypeManifest,PrototypeEntry,BundleFile,safe_payload,load_prototype
from app.game.models import content_id
from app.game.task_conditioning import TaskSnapshotBinding
from app.game.offline.calibration import CalibrationArtifact
from scripts.multitask_policy42 import save,read

ROOT=Path('build/multitask-prototype42-v1')
SOURCE=Path('build/multitask-uncertainty-sweep42')
STUDY=Path('build/multitask-policy42')
APPROVAL='User packaging approval bff23d52-aafc-4be6-8adb-3c7e8f88836c: arithmetic existing50%, factual existing25% experimental; no activation'

def main():
    def guard(event,args):
        if event=='open' and isinstance(args[0],str) and any(p.casefold()=='custody' for p in Path(args[0]).parts):raise AssertionError('final payload forbidden')
    sys.addaudithook(guard)
    ROOT.mkdir(exist_ok=False);entries=[];originals={}
    for task,target in [('arithmetic',50),('factual',25)]:
        directory=ROOT/task;directory.mkdir()
        source=SOURCE/task/('coverage-'+str(target))
        raw=(source/'policy.json').read_bytes();safe_payload(raw)
        artifact=PolicyArtifact.model_validate_json(raw);c=artifact.context
        if json.loads(c.clean_coverage_json)['minimum']!=target/100:raise ValueError('approved target mismatch')
        originals[str(source/'policy.json')]=hashlib.sha256(raw).hexdigest()
        (directory/'policy.json').write_bytes(raw)
        episode=DeploymentEpisode(episode_id='prototype42-v1-'+task,context=c,contract=artifact.contract,execution_configuration_id=artifact.execution_configuration_id)
        save(directory/'episode.json',episode.model_dump(mode='json'))
        save(directory/'reputation.json',[asdict(s) for s in c.plan.reputation_statistics])
        calibration=CalibrationArtifact.model_validate(read(STUDY/task/'calibration.json')).model_dump(mode='json')
        if dict(c.attempt_costs)!={r['verifier_name']:r['attempt_cost'] for r in calibration['result']['estimates']}:
            raise ValueError('recorded calibration differs from approved costs')
        save(directory/'costs.json',dict(calibration_id=calibration['calibration_id'],calibration_input_digest=calibration['input_digest'],
            setup_fingerprint=content_id(calibration['request']['measurements']['setup']),budget=c.budget,units=c.cost_units,
            attempt_costs=c.attempt_costs,estimates=calibration['result']['estimates'],
            interpretation='All80 per-verifier first/subsequent measured attempts; summed verifier-attempt wall ms under shared-machine contention, not latency or money. Full calibration is external audit data, not bundled.'))
        save(directory/'resources.json',artifact.contract.resource_manifest.model_dump(mode='json'))
        report=read(source/'report.json')
        if report['artifact_id']!=artifact.artifact_id:raise ValueError('report identity mismatch')
        save(directory/'development-metrics.json',dict(artifact_id=artifact.artifact_id,source_report_id=content_id(report),
            groups=20,candidates=40,label_scope='Independent binary correctness; abstentions not relabelled',
            all_strategies=report['probabilities'],zero_clean_coverage_mass=report['zero_coverage_mass'],
            scenarios=report['scenarios'],worst_validation_loss=report['worst_validation_loss'],
            limitations='Development only, source-known constructed examples; one conservative shared compromise group; no unseen-question guarantee or superiority claim.'))
        # Read preparation only, never final reservation/payload or verifier reports.
        preparation=read(STUDY/task/'preparation.json')
        questions=tuple(sorted({e['question_id'] for e in preparation['examples']}))
        binding=TaskSnapshotBinding.model_validate_json(c.task_conditioning_json)
        entries.append(PrototypeEntry(task=task,experimental=task=='factual',artifact_path=task+'/policy.json',episode_path=task+'/episode.json',
            reputation_path=task+'/reputation.json',costs_path=task+'/costs.json',resources_path=task+'/resources.json',metrics_path=task+'/development-metrics.json',
            artifact_id=artifact.artifact_id,compatibility_id=c.compatibility_id,task_id=binding.identity.task_id,reputation_snapshot_id=c.reputation_snapshot_id,
            execution_configuration_id=artifact.execution_configuration_id,calibration_id=calibration['calibration_id'],expected_clean_coverage=target/100,allowed_question_ids=questions))
    config=read(STUDY/'adapter.json')
    for key in ('embedding_snapshot','nli_snapshot','index_receipt','service_observation'):config[key]='REQUIRED_EXTERNAL_'+key.upper()
    save(ROOT/'resource-adapter.template.json',config)
    save(ROOT/'runtime-requirements.json',dict(
        source_revision=read(STUDY/'arithmetic/fit-provenance.json')['code_revision'],
        application_source_digest=content_id([(p.as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(Path('app').rglob('*.py'))]),
        prototype_packager_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        solver_environment=read(STUDY/'arithmetic/fit-provenance.json')['environment'],
        recording_dependency_versions=calibration['request']['measurements']['setup']['dependency_versions'],
        execution_contract='offline_public_decision_v4',bundle_loader='bounded_task_policy_bundle_v1',
        note='Source revision plus dirty source digest identifies required owned implementation. External runtime/model resources must be observed separately; no model weights or machine paths included.'))
    (ROOT/'README.md').write_text('''# Bounded task prototype v1

Approved for engineering packaging only; not activated. Arithmetic target50%, factual target25% experimental. Semantic equivalence is unsupported; no semantic diagnostic policy is included.

Load from the repository with the owned game modules and recorded dependencies installed:

```powershell
.venv/Scripts/python.exe -m app.game.offline.prototype validate --bundle build/multitask-prototype42-v1
```

Python: `from app.game.prototype_bundle import load_prototype`; `bundle=load_prototype("build/multitask-prototype42-v1")`; use `bundle.router()` and `bundle.provider()` with the actual TaskQuestionAnalyzer, legitimate selector, caller RNG and live resource observer. No API wiring is supplied. The loader verifies package hashes, policy certificates, episodes, frozen reputation, costs and compatibility; it does not attest live resources.

Scope: explicit_task_questions_v1 arithmetic addition or source-snapshot population/currency/area contexts at exactly captured difficulty/settings and only the prepared history/development question identities listed in the manifest. Other questions fail study_scope_mismatch. Both policies require usable reference context; absent/blank/judgment-list context has no compatible route. Semantic and unknown tasks have no deployed policy and fail explicitly. No no-reference fallback exists. New answers/references have no empirical performance guarantee. The supplied reference is available, not automatically proven true or relevant.

Keep every strategy probability, including zero and tiny values, unchanged. Materially used types across policies are Rule, Evidence and Confidence; requests do not all run three verifiers. Arithmetic also retains a tiny positive Semantic-containing strategy. Probability on zero-clean-coverage plans is intentional policy behavior, disclosed in development-metrics.json. Coverage is an expected development-population measurement, not runtime confidence.

External resources are NOT included: installed all-MiniLM-L6-v2 embedding weights, nli-deberta-v3-small NLI weights, local llama3.2:3b service/model and original service observation, the isolated57-document source corpus, index-v2 and observed build receipt, compatible adapter/verifier implementation bytes and dependencies. resources.json binds exact hashes; template values are not an executable approved setup. Fill excluded local snapshot/receipt/observation locations without silently changing bound configuration. Original corpus/index relative layout is retained in the template because it contributes to its configuration identity. Changed resources/configuration/service identities must fail existing provenance checks, not be rebound to these artifacts.

History-only Beta(1,1), threshold +/-0.55, informative minimum-two, achieved capability and all-selected-returned protections remain unchanged. Missing checks, weak/conflicting signals, unknown/incompatible contexts and failures may correctly yield uncertainty. Raw Rule scores are correctness bits for supported arithmetic; Semantic scores are uncalibrated cosine resemblance, Evidence scores NLI-class strength, Confidence scores judgment agreement. Signed aggregate scores are not calibrated correctness probabilities. Numerical details are in each policy and existing public finalization audit.

Metrics are development-only on20 groups/40 candidates per task. Report errors separately from uncertainty and selective risk only among decisions. All informative verifiers are connected by shared models/conservative unknown assumptions: one group compromise may corrupt them together. Zero errors through abstention are not perfect accuracy. Summed attempt wall ms are not end-to-end latency or money.

Integration owner: pin this package and source/runtime versions; supply external resources with exact observed identities, explicit question/task/reference routing, legitimate selector, RNG and resource observer; preserve safe failures and three-outcome semantics. Do not activate APIs, change probabilities or expand task scope without a separate decision. Full calibration/recordings remain external audit inputs; no recordings, labels, model weights or credentials are bundled. New live inference and final evaluation require separate authorization.
''',encoding='utf-8')
    files=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file():
            raw=p.read_bytes();safe_payload(raw);files.append(BundleFile(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(raw).hexdigest()))
    manifest=PrototypeManifest(version='bounded_task_policy_bundle_v1',approval=APPROVAL,entries=tuple(entries),files=tuple(files))
    save(ROOT/'manifest.json',manifest.model_dump(mode='json'));loaded=load_prototype(ROOT)
    for p,digest in originals.items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=digest:raise ValueError('original artifact changed')
    archive=ROOT.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
    print(json.dumps(dict(bundle=str(ROOT),bundle_id=loaded.manifest.bundle_id,archive=str(archive),original_bytes_preserved=True),indent=2))

if __name__=='__main__':main()
