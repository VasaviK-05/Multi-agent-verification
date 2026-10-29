"""Construct seed-42 pilot inputs with independent exact-rational labels.

Preparation only: use the existing collector/calibrator CLIs to execute adapters.
Final labels are written to separate procedural-custody storage, never a fit input.
"""
import argparse
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random


def decimal_text(value):
    """Exact long division, independent of the verifier's Decimal implementation."""
    sign = '-' if value < 0 else ''
    numerator, denominator = abs(value.numerator), value.denominator
    whole, remainder = divmod(numerator, denominator)
    digits, seen = [], set()
    while remainder:
        if remainder in seen:
            raise ValueError('pilot answers must have a finite decimal representation')
        seen.add(remainder)
        digit, remainder = divmod(remainder*10, denominator)
        digits.append(str(digit))
    return sign + str(whole) + ('.' + ''.join(digits) if digits else '')


def constructed_groups():
    """Sixty distinct formal arithmetic tasks, two substantive variants each."""
    groups = []
    for operator in ('+', '-', '*', '/'):
        for index in range(15):
            if operator == '+':
                a, b = 17+3*index, 4+2*index
                value = Fraction(a)+Fraction(b)
            elif operator == '-':
                a, b = 100+7*index, 11+3*index
                value = Fraction(a)-Fraction(b)
            elif operator == '*':
                a, b = 3+index, 19+2*index
                value = Fraction(a)*Fraction(b)
            else:
                a, b = 11+2*index, (2,4,5,8)[index % 4]
                value = Fraction(a)/Fraction(b)
            name = {'+':'add','-':'subtract','*':'multiply','/':'divide'}[operator]
            groups.append(dict(group_id=f'arith-{name}-{index+1:02}', operand_a=a, operand_b=b,
                operator=operator, question=f'What is {a} {operator} {b}?',
                expected=decimal_text(value), expected_numerator=value.numerator,
                expected_denominator=value.denominator, incorrect=decimal_text(value+1)))
    return groups


def preparation_rows():
    groups = constructed_groups()
    random.Random(42).shuffle(groups)
    rows = []
    for index, group in enumerate(groups):
        role = ('history', 'development', 'final_test')[index//20]
        reference = (f"Exact arithmetic reference: {group['operand_a']} {group['operator']} "
                     f"{group['operand_b']} = {group['expected']}.")
        for variant in ('correct','incorrect'):
            answer = group['expected'] if variant == 'correct' else group['incorrect']
            truth = Fraction(answer) == Fraction(group['expected_numerator'],group['expected_denominator'])
            check = dict(method='stdlib Fraction exact arithmetic and independent long division',
                generator_version='constructed_arithmetic_fraction_v1',
                operands=[group['operand_a'],group['operand_b']], operator=group['operator'],
                expected_numerator=group['expected_numerator'], expected_denominator=group['expected_denominator'],
                candidate_numerator=Fraction(answer).numerator, candidate_denominator=Fraction(answer).denominator,
                equality=truth, framework_verifiers_used=False, source='constructed engineering pilot, not external benchmark')
            rows.append(dict(example_id=group['group_id']+'-'+variant, split_identity=group['group_id'],
                question_id=group['group_id'], run_id='pilot42-'+role+'-'+group['group_id']+'-'+variant,
                dataset_id='constructed-arithmetic-pilot42-'+role+'-v1', role=role, purpose='calibration',
                question=group['question'], answer=answer, reference=reference,
                label=dict(answer_is_correct=truth, label_source='constructed_arithmetic_fraction_v1',
                    label_method='independent_ground_truth', provenance=json.dumps(check,sort_keys=True))))
    return rows


def prepare(output, adapter_configuration, *, preparation_authorization, custody_record, freeze_record):
    from app.analysis.question_analyzer import QuestionAnalyzer
    from app.benchmark.project_adapter import AdapterConfiguration, inspect_setup
    from app.game.models import content_id
    from app.game.offline.collection import RecordingRequest
    from app.game.offline.records import FinalTestReservation
    from app.game.offline.recording_adapters import ArithmeticObserver
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    for name, value in dict(preparation_authorization=preparation_authorization,
                            custody_record=custody_record, freeze_record=freeze_record).items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'explicit nonblank {name} reference required')
    rows = preparation_rows()
    reservation = FinalTestReservation(version='final_test_reservation_v1',role='final_test',
        dataset_id='constructed-arithmetic-pilot42-final_test-v1',
        custody_record=custody_record,
        examples=tuple(dict(example_id=e['example_id'],split_identity=e['split_identity'],
            question_id=e['question_id'],validation_id=e['run_id'],
            content_identity=content_id([e['question'],e['answer'],e['reference']]))
            for e in rows if e['role']=='final_test'))
    analyzer = QuestionAnalyzer(mode='heuristic',environ={})
    training = [{**e,'analysis':asdict(analyzer.analyze(e['question']))}
                for e in rows if e['role'] != 'final_test']
    full_report = inspect_setup(AdapterConfiguration.model_validate(adapter_configuration))
    config = dict(embedding_snapshot=adapter_configuration['embedding_snapshot'],torch_num_threads=2)
    resources = ArithmeticObserver(config).snapshot()
    request = RecordingRequest(version='offline_recording_request_v1',intended_use='pilot',study_approval=None,
        preparation_authorization=preparation_authorization,
        cache_contract='complete_team_independent_v1',
        randomness_control='Split seed42; exact Fraction labels; eval-mode local embedding without sampling; explicit two CPU threads',
        execution_configuration_id=resources.manifest_id,expected_setup=None,
        factory='app.game.offline.recording_adapters:arithmetic_factory',final_test_reservation=reservation,
        permitted_datasets=tuple((role,'constructed-arithmetic-pilot42-'+role+'-v1') for role in ('history','development')),
        candidates=tuple(dict(verifier_name=n,adapter=n+'_v1',registered=True,capability_source='builtin',
            capabilities=asdict(BUILTIN_CAPABILITIES[n])) for n in ('rule','semantic')),examples=training)
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    (output/'inputs').mkdir()
    (output/'custody').mkdir()
    (output/'inputs'/'adapter.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    (output/'inputs'/'recording-request.json').write_text(request.model_dump_json(indent=2),encoding='utf-8')
    (output/'inputs'/'reservation.json').write_text(reservation.model_dump_json(indent=2),encoding='utf-8')
    (output/'inputs'/'calibration-settings.json').write_text(json.dumps(dict(measurements=None,
        final_test_reservation=reservation.model_dump(mode='json'),required_verifiers=['rule','semantic'],
        include_warmups=True,freeze_record=freeze_record),indent=2),encoding='utf-8')
    final_text=''.join(json.dumps(e,sort_keys=True)+'\n' for e in rows if e['role']=='final_test')
    (output/'custody'/'final-examples.jsonl').write_text(final_text,encoding='utf-8')
    (output/'full-project-preflight.json').write_text(json.dumps(full_report,indent=2),encoding='utf-8')
    summary=dict(origin='constructed_arithmetic_fraction_v1; not an external benchmark',seed=42,
        groups={r:20 for r in ('history','development','final_test')},
        examples={r:40 for r in ('history','development','final_test')},
        labelled_preparation_examples=80,held_out_examples=40,reservation_id=reservation.reservation_id,
        label_method='Exact rational arithmetic via Fraction; independent of RuleVerifier Decimal and all framework decisions',
        reference='Correct-result arithmetic reference shared by variants; reference-assisted task, not factual QA robustness',
        custody='Procedural holdout generated in this workflow; not independent third-party custody',
        fitting_inputs_contain_final_labels=False,full_project_ready=full_report['ready'],
        selected_verifiers=['rule','semantic'],excluded_verifiers=dict(evidence='Outside arithmetic-only roster; no retrieval/corpus adapter used',
            confidence='Outside rule/semantic roster; no generation/NLI used'),
        authorized_attempt_bound=160,provider_requests=0,model_downloads=0,torch_num_threads=2,
        fitting_settings_approved=False,policy_created=False,
        source_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (output/'dataset-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--project-adapter-config',type=Path,required=True)
    parser.add_argument('--preparation-authorization',required=True)
    parser.add_argument('--custody-record',required=True)
    parser.add_argument('--freeze-record',required=True)
    args=parser.parse_args(argv)
    configuration=json.loads(args.project_adapter_config.read_text(encoding='utf-8'))
    print(json.dumps(prepare(args.output_dir,configuration, preparation_authorization=args.preparation_authorization,
        custody_record=args.custody_record, freeze_record=args.freeze_record),indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
