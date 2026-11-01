"""Read-only repository audit; never collect data, load final outcomes, or fit fixtures."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ROWS = [
    dict(category='Missing recordings', input='Complete history/development attempts',
         fields='TrainingManifest: partitions[history,development]; each Example has attempts for every captured candidate; Attempt has verifier_name, state, report_json (returned states only), execution_id, configuration_id, report_provenance, adapter, observed_resources_json.',
         producer='No complete project recording/export command found. Produce app.game.offline.records.Partition/Example/Attempt; offline_benchmark.run_benchmark exports aggregate metrics only.',
         owner='Verifier recording/integration owner', blocks='Replay requires every candidate, including explicit failures/unavailability. Questions/answers and timing rows cannot substitute.'),
    dict(category='Missing recordings', input='Independent labels and provenance',
         fields='Example.answer_is_correct strict boolean; label_method independent_human or independent_ground_truth; label_source; DatasetDescription source/version, independent_label_provenance and declared_label_sources.',
         producer='Independent adjudication or approved external ground truth. AutomaticGroundTruthEvaluator.evaluate returns Wikidata source/label for supported questions but supplies no frozen dataset provenance or split permission.',
         owner='Independent adjudicator / dataset owner', blocks='The 10 benchmark flags have no provenance. They cannot be promoted to independent empirical labels or replaced with framework decisions.'),
    dict(category='Missing recordings', input='Preparation splits and final-test reservation',
         fields='Distinct history/development dataset IDs and example_id/split_identity/question_id/content_identity/validation_id; FinalTestReservation version, role=final_test, dataset_id, custody_record, nonempty ReservedExample roster.',
         producer='Dataset custodian supplies TrainingManifest and FinalTestReservation. ReservedExample.from_example is a custodian-side helper; never call on held-out payloads during fitting.',
         owner='Dataset custodian', blocks='No approved partition/group membership, permission or reservation exists. Collection could otherwise touch held-out examples or leak related questions.'),
    dict(category='Missing recordings', input='Observed resources and collection factory',
         fields='ResourceManifest per-candidate implementation/configuration SHA-256 and applicable model/corpus/index/prompt/service identities; matching Attempt observations. MeasurementSetup has environment, dependency_versions, code_revision and application_source_digest.',
         producer='CollectionRequest.factory module:function -> (verifier instances, actually observed MeasurementSetup). No concrete production factory found. collect_costs requires this adapter before any attempt.',
         owner='Verifier/resource adapter owners', blocks='No actual snapshots or factory exist. Hashing a model alias or copying a fixture would fabricate provenance.'),
    dict(category='Missing scientific decisions', input='Population, planning and eligibility configuration',
         fields='Approved scientific_scope; captured PlanningContext/selection_json with domain/category, requirements, candidates, registration/eligibility, capabilities, prerequisites, minimum_count and complete history statistics.',
         producer='Study owner approves scope; capture_context(selector, analysis, ...) and history_reputation(history, prior_alpha=..., prior_beta=...) construct/validate the snapshot.',
         owner='Study owner / selector configuration owner', blocks='The available examples are factual QA. No arithmetic-only population or category is approved, and evidence-bearing studies remain gated.'),
    dict(category='Missing scientific decisions', input='Dependency model and attacks',
         fields='DependencyRegistry version, dependencies(resource_id, compromise_pathway, verifiers), unresolved candidates and explicit shared_unknown; AttackSpecification version=report_corruption_v1 and suppression unavailable or abstention.',
         producer='Resource/security and study owners supply registry and attack declaration; enumerate_attacks is executable after approval.',
         owner='Resource/security owner / study owner', blocks='There is no approved registry or threat specification. Sharing resources is not grounds to invent independence or exclude verifiers.'),
    dict(category='Missing recordings', input='Measured compatible cost calibration',
         fields='MeasurementInput setup, permitted_datasets, preparation_authorization, complete AttemptMeasurement rows including duration_ms/status for each candidate; CalibrationRequest reservation, required_verifiers, include_warmups and freeze_record.',
         producer='.venv/Scripts/python.exe -m app.benchmark.collect_costs build/collection.json --output build/verifier-attempts.json; then -m app.game.offline.calibration build/calibration-settings.json --measurements build/verifier-attempts.json --output build/verifier-costs.json',
         owner='Benchmark measurement producer / dataset custodian', blocks='No measured bundle or compatible calibration artifact exists. docs/verifier_cost_missing_inputs.json and build reports are not cost measurements.'),
    dict(category='Missing scientific decisions', input='Budget, losses, execution and study settings',
         fields='Explicit attempt costs/units and budget, false_accept/false_reject/uncertain/resource_weight; calibrated budget_ms/resource_weight_per_ms/approved setup fingerprint if using ms; v2 ExecutionContract threshold/failure semantics/history priors; seeds/repetitions/optimizer tolerance, primary outcomes, sensitivity/coverage/uncertainty plans and freeze protocol.',
         producer='Complete PolicyBuildSpecification from docs/game_policy_build.template.json; optional calibrated settings from docs/verifier_cost_build_settings.template.json. Then -m app.game.offline.build build/policy-input.json --output-dir build/empirical-policy.',
         owner='Study owner', blocks='Only deliberately invalid null templates exist. There is no defensible objective, feasible set, threshold or reputation prior to fit without these choices.'),
    dict(category='Software/interface blocker', input='Replay-ready collection export is not implemented by available CLIs',
         fields='A recording producer must persist canonical VerificationResult plus explicit states, independent metadata and observed_resources_json into the existing Attempt/Example contracts.',
         producer='offline_benchmark CLI emits aggregate MethodReport; collect_costs emits duration/status measurements and propagates failure after preserving attempted rows, without serializing reports or continuing unattempted candidates.',
         owner='Offline recording/integration owner', blocks='Even a successful timing collection would not produce the full input needed by the fitter. Later unattempted candidates must remain explicitly incomplete, never invented failures.'),
    dict(category='Software defect', input='Existing evidence/public-coverage contract failures',
         fields='tests/test_adaptive_pipeline.py: test_actual_evidence_output_contract_is_consumed_without_models (support/rejection cases), test_actual_conflicting_evidence_cannot_cover_factual_request.',
         producer='Separately reviewed evidence producer repair; readiness.py EVIDENCE_FAILURES gate cannot be bypassed. An independently approved arithmetic-only study is a different population, not a repair.',
         owner='Evidence verifier/integration owner', blocks='Current tests return uncertainty for directional evidence and no_relevant_evidence instead of conflict. The existing readiness gate blocks evidence-bearing empirical fitting.'),
]

def main():
    rows = [json.loads(line) for line in (ROOT / 'data/test_benchmark.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    inventory = []
    # Only inventory filenames and bytes; never inspect an unknown outcome payload.
    for directory in ('data', 'build'):
        for p in sorted((ROOT / directory).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                inventory.append(dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size))
    report = dict(outcome='Empirical policy remains blocked', audit_date='2026-10-26',
        branch=subprocess.check_output(['git','branch','--show-current'], cwd=ROOT, text=True).strip(),
        code_revision=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        empirical_policy_created=False, real_collection_launched=False,
        final_test_payloads_read=False, benchmark=dict(path='data/test_benchmark.jsonl', examples=len(rows),
            boolean_labels=sum(type(r.get('answer_is_correct')) is bool for r in rows),
            label_provenance_present=False, partitions_present=False, verifier_recordings_present=False,
            digest=hashlib.sha256((ROOT/'data/test_benchmark.jsonl').read_bytes()).hexdigest()),
        complete_empirical_recording_manifests_found=0, empirical_cost_artifacts_found=0,
        inventory=inventory, missing_input_table=ROWS,
        scope=dict(db_api_touched_this_turn=False, production_state_writes=False, code_changes_this_turn=False))
    (ROOT/'docs/game_empirical_build_audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    # Reproduce evidence failures using pristine HEAD sources, without checkout or reset.
    archive = subprocess.check_output(['git','archive','--format=zip','HEAD'], cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix='head-evidence-', dir=OUT) as folder:
        zipfile.ZipFile(io.BytesIO(archive)).extractall(folder)
        cmd = [sys.executable,'-m','pytest','tests/test_adaptive_pipeline.py','-k',
            'test_actual_evidence_output_contract_is_consumed_without_models or test_actual_conflicting_evidence_cannot_cover_factual_request',
            '-q','-p','no:cacheprovider']
        result = subprocess.run(cmd, cwd=folder, capture_output=True, text=True)
        (OUT/'evidence-baseline.json').write_text(json.dumps(dict(source='git archive HEAD',
            code_revision=report['code_revision'], command=cmd, returncode=result.returncode,
            stdout=result.stdout, stderr=result.stderr), indent=2), encoding='utf-8')
        print(result.stdout)
    print(report['outcome'])

if __name__ == '__main__':
    main()
