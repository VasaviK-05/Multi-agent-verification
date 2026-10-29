"""Prepare one bounded cost proposal; never initialize models or collect attempts."""
import argparse
from collections import Counter
from dataclasses import asdict
import copy
import json
from pathlib import Path
import random
from types import SimpleNamespace

from app.analysis.question_analyzer import QuestionAnalyzer
from app.benchmark.collect_costs import validate_preparation
from app.benchmark.project_adapter import inspect_setup
from app.game.models import content_id
from app.game.offline.calibration import CalibrationArtifact, read_json
from app.game.offline.collection import (
    DiagnosticExample, DiagnosticExclusionRoster, DiagnosticRecordingRequest,
    collection_plan, measurement_input,
)
from app.game.offline.collect import load_bundle


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--factual-bundle', type=Path, required=True)
    parser.add_argument('--arithmetic-bundle', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--adapter-config', type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.output_dir
    root.mkdir(exist_ok=True)
    if any(root.iterdir()):
        raise FileExistsError('proposal directory contains artifacts; use a fresh version')
    def save(name, value):
        with (root / name).open('x', encoding='utf-8') as f:
            json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)

    factual_path = args.factual_bundle
    factual = load_bundle(factual_path)
    try:
        measurement_input(factual)
    except ValueError as exc:
        diagnostic_blocker = str(exc)
    else:
        raise AssertionError('diagnostic export guard unexpectedly absent')
    arithmetic_path = args.arithmetic_bundle
    arithmetic = load_bundle(arithmetic_path)
    artifact_path = args.calibration
    artifact = CalibrationArtifact.model_validate(read_json(artifact_path))
    assert artifact.request.measurements == measurement_input(arithmetic)
    assert artifact.request.measurements.setup.evidence_kind == 'empirical'
    save('existing-calibration-validation.json', dict(
        valid=True, newly_created=False, path=str(artifact_path),
        calibration_id=artifact.calibration_id, input_digest=artifact.input_digest,
        setup_fingerprint=artifact.request.measurements.setup.fingerprint,
        result=artifact.result, abstentions={name: sum(
            a.candidate == name and a.attempt.state == 'abstention' for a in arithmetic.attempts
        ) for name in artifact.request.required_verifiers},
        diagnostic_export_blocker=diagnostic_blocker,
        note='Historical arithmetic setup only; do not pool with factual or new setup.'))

    config = read_json(args.adapter_config)
    save('adapter.json', config)
    preflight = inspect_setup(config)  # Local hashes and saved metadata only; zero HTTP.
    save('resource-preflight.json', preflight)
    if not preflight['ready']:
        raise ValueError(preflight['blockers'])
    from app.game.offline.calibration import MeasurementSetup
    setup = MeasurementSetup.model_validate(preflight['observed_setup'])
    request = copy.deepcopy(factual.request.model_dump(mode='json'))
    request.update(preparation_authorization=None, expected_setup=setup.model_dump(mode='json'),
        execution_configuration_id=setup.resources.manifest_id,
        randomness_control='One seeded shuffle, seed 20261028; fixed candidate order semantic/evidence/rule/confidence; confidence provider seeds 0..4 per call; no global determinism claim')
    reservation = copy.deepcopy(request['final_test_reservation'])
    reservation['dataset_id'] = 'broader-cost-v1-combined-final-exclusions'
    reservation['examples'] += [r.model_dump(mode='json') for r in arithmetic.request.final_test_reservation.examples]
    exclusions = DiagnosticExclusionRoster.model_validate(reservation)
    request['final_test_reservation'] = reservation
    request['permitted_datasets'] += [list(d) for d in arithmetic.request.permitted_datasets]
    analyzer = QuestionAnalyzer(mode='heuristic', environ={})
    rows = []
    for source, bundle in [('factual', factual), ('arithmetic', arithmetic)]:
        for e in bundle.request.examples:
            row = e.model_dump(mode='json')
            actual = asdict(analyzer.analyze(e.question))
            # Preserve actual analyzer outputs; a mismatch is a new setup issue, not a manual fix.
            row.update(label=None, analysis=actual, run_id='broader-cost-v1-' + e.run_id)
            rows.append(row)
    random.Random(20261028).shuffle(rows)
    request['examples'] = rows
    examples = tuple(DiagnosticExample.model_validate(r) for r in rows)
    validate_preparation(SimpleNamespace(examples=[SimpleNamespace(
        **{**e.model_dump(mode='json'), 'context': e.reference}) for e in examples],
        permitted_datasets=tuple(map(tuple, request['permitted_datasets'])),
        final_test_reservation=exclusions))
    # Validate all recording fields except the deliberately absent execution permission.
    errors = []
    try:
        DiagnosticRecordingRequest.model_validate(request)
    except ValueError as exc:
        errors = exc.errors(include_url=False)
    assert len(errors) == 1 and errors[0]['loc'] == ('preparation_authorization',)
    # Plan prerequisites without making an execution request or inventing permission.
    planning_request = SimpleNamespace(candidates=factual.request.candidates)
    plans = [collection_plan(planning_request, e) for e in examples]
    eligible = sum(c['eligible'] for p in plans for c in p['candidates'])
    assert len(rows) == 86 and eligible == 344
    save('recording-request.pending.json', request)
    save('roster.json', [dict(order=i+1, **r, answer_characters=len(r['answer']),
        answer_words=len(r['answer'].split()), category=('factual' if r['example_id'].startswith('factual-')
        else r['split_identity'].split('-')[1]), plan=p) for i, (r, p) in enumerate(zip(rows, plans))])
    save('workload.json', dict(status='pending_new_execution_authorization',
        example_runs=86, unique_examples=86, repetitions=1, warmups=0,
        candidate_order=['semantic', 'evidence', 'rule', 'confidence'], seed=20261028,
        verifier_attempts=eligible, attempts_per_verifier=86, max_local_generations=430,
        max_live_metadata_requests=1380, metadata_formula='4 factory + 4 per executed attempt',
        preparation_http_requests=0, downloads=0, paid_services=0,
        categories=dict(Counter('factual' if r['example_id'].startswith('factual-') else
            r['split_identity'].split('-')[1] for r in rows)),
        roles=dict(Counter(r['role'] for r in rows)),
        answer_character_range=[min(len(r['answer']) for r in rows), max(len(r['answer']) for r in rows)],
        answer_word_range=[min(len(r['answer'].split()) for r in rows), max(len(r['answer'].split()) for r in rows)],
        setup_fingerprint=setup.fingerprint,
        old_factual_setup_matches=setup == factual.observed_setup,
        old_arithmetic_setup_matches=setup == arithmetic.observed_setup,
        diagnostic_only=True, calibration_export_permitted=False,
        scientific_reservation_approved=False, freeze_approved=False,
        validation_errors=errors))
    cost_request = dict(setup=setup.model_dump(mode='json'),
        final_test_reservation={**reservation, 'version':'final_test_reservation_v1', 'custody_record':None},
        permitted_datasets=request['permitted_datasets'], preparation_authorization=None,
        factory='app.benchmark.project_adapter:create_verifiers', examples=[{
            k:v for k,v in {**r,'context':r['reference']}.items() if k in {
                'example_id','split_identity','question_id','run_id','dataset_id','role',
                'purpose','question','answer','context'}} for r in rows])
    save('cost-request.pending.json', cost_request)
    save('calibration-settings.pending.json', dict(measurements=None,
        final_test_reservation=cost_request['final_test_reservation'],
        required_verifiers=['semantic','evidence','rule','confidence'],
        include_warmups=True, freeze_record=None))
    print(json.dumps(dict(output=str(root), ready_for_approval=True,
        attempts=eligible, generations=430, metadata=1380,
        existing_calibration_id=artifact.calibration_id)))


if __name__ == '__main__':
    main()
