"""Prepare this repository's ten-row factual feasibility proposal, never execute it.

This is a fixed study-package producer, not a new collector or policy builder.
Run once before custody approval. It ignores benchmark correctness flags and
writes no final labels, reports, timings, question/answer payloads or outcome paths.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from types import SimpleNamespace

from pydantic import ValidationError

from app.analysis.question_analyzer import QuestionAnalyzer
from app.benchmark.project_adapter import AdapterConfiguration, inspect_setup, file_digest, source_constants
from app.benchmark.prepare_collection import PreparationInput
from app.game.dependencies import DependencyRegistry
from app.game.execution_contract import ExecutionContract
from app.game.models import content_id
from app.game.offline.attacks import AttackSpecification
from app.game.offline.calibration import CalibrationRequest, MeasurementSetup, read_json
from app.game.offline.collection import Candidate, PreparationExample, RecordingRequest, collection_plan
from app.game.offline.records import FinalTestReservation, ReservedExample
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.game.research.specification import RecordingConfiguration

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261026
STUDY = 'factual-feasibility-draft-v1'
GROUPS = ('france_paris', 'germany', 'india', 'python', 'ai_ml', 'ai_ml', 'relativity', 'wwii', 'usa', 'france_paris')
# Evidence was inspected only for the six proposed preparation rows. These short
# excerpts are source evidence for draft adjudication, not retrieved verifier votes.
EVIDENCE = {
    'germany': dict(url='https://www.berlin.de/en/',
        excerpt='Capital of Germany',
        rationale='The city government identifies Berlin as Germany\'s capital.'),
    'ai': dict(url='https://www.ibm.com/think/topics/artificial-intelligence',
        excerpt='simulate human learning, comprehension, problem solving, decision making',
        rationale='The candidate is a broad paraphrase of the source definition of AI; approve the definitional correctness rubric.'),
    'ml': dict(url='https://www.ibm.com/think/topics/machine-learning',
        excerpt='make decisions or predictions without explicit, hard-coded instructions.',
        rationale='The source describes ML as a subset of AI learning patterns from data to predict without explicit instructions.'),
    'python': dict(url='https://www.python.org/doc/essays/blurb/',
        excerpt='high-level programming language with dynamic semantics',
        additional_source='https://www.python.org/about/',
        rationale='The PSF identifies a high-level language; its diverse application list independently supports general-purpose use.'),
    'india': dict(url='https://delhitourism.gov.in/aboutus/history_of_delhi.html',
        excerpt='New Delhi was officially declared as the Capital of India',
        rationale='The government tourism page directly supports the candidate\'s capital claim.'),
    'relativity': dict(url='https://www.nist.gov/atomic-clocks/a-powerful-tool-for-science/putting-einstein-test',
        excerpt='Albert Einstein published his world-changing special relativity theory',
        rationale='NIST attributes both special and general relativity to Einstein; the candidate makes only that attribution.'),
}
EVIDENCE_KEYS = {2: 'germany', 3: 'india', 4: 'python', 5: 'ai', 6: 'ml', 7: 'relativity'}
PREPARATION_CONTENTS = {
    2: '8c4285598e4e811f2a4e81c76b6700737fed6edc1e9368e9df4a6ad5f5835f70',
    3: 'cb62820602703285a888895ce202218ed87b4876ef9d0a7fbfc2ea074ddf0646',
    4: '50ee7082dad9665ee768e1018e59828253f78b5d2feca77d20bc2190c49b9eb3',
    5: '855fe38dcef2bf0299bfeb13a5bc11aafe22be5efc3e1ed1c1661051aaf71f77',
    6: '9273cc1932fa852d1b8a19dcfd25a38a37e735785846180ed7ba49bd09118e82',
    7: '2f253dcffc2588d838c1e0714a7ba5f98dd2b613ef8e5c1b0c23a43cff549222',
}


def draft_package(rows, adapter, *, source_digest):
    """Allow-list candidate input fields before assigning any draft roles."""
    if len(rows) != 10:
        raise ValueError('this fixed proposal requires the existing ten-row candidate inventory')
    clean = [{k: row[k] for k in ('question', 'answer', 'context')} for row in rows]
    for index, expected in PREPARATION_CONTENTS.items():
        row = clean[index-1]
        if content_id([row['question'], row['answer'], row['context']]) != expected:
            raise ValueError(f'preparation row {index} changed; independently re-adjudicate before attaching source evidence')
    groups = sorted(set(GROUPS))
    random.Random(SEED).shuffle(groups)
    allocation = {g: ('history' if i < 2 else 'development' if i < 5 else 'final_test')
                  for i, g in enumerate(groups)}
    analyzer = QuestionAnalyzer(mode='heuristic', environ={})
    candidates = tuple(Candidate(verifier_name=n, adapter=n+'_v1', registered=True,
        capability_source='builtin', capabilities=BUILTIN_CAPABILITIES[n])
        for n in ('semantic', 'evidence', 'rule', 'confidence'))
    roster, reserved, examples, labels, plans = [], [], [], [], []
    for index, (row, group) in enumerate(zip(clean, GROUPS), start=1):
        role = allocation[group]
        identity = dict(example_id=f'{STUDY}-e{index:02d}', split_identity=f'{STUDY}-group-{group}',
            question_id=content_id(['question', row['question']]),
            content_identity=content_id([row['question'], row['answer'], row['context']]),
            validation_id=f'{STUDY}-{role}-e{index:02d}-r1')
        ReservedExample.model_validate(identity)
        roster.append(dict(role=role, dataset_id=f'{STUDY}-{role}', **identity))
        if role == 'final_test':
            reserved.append(identity)
            continue  # No analyzer, labels, source lookup or final payload export.
        key = EVIDENCE_KEYS[index]
        support = EVIDENCE[key]
        audit = dict(example_id=identity['example_id'], status='draft_source_grounded_not_approved',
            proposed_answer_is_correct=True, method='independent_ground_truth',
            source_evidence=support, excerpt_sha256=hashlib.sha256(support['excerpt'].encode()).hexdigest(),
            accessed_date='2026-10-26', adjudicator='assistant source comparison, independent of framework verdicts',
            human_approval=None, benchmark_flags_used=False)
        labels.append(audit)
        example = PreparationExample(example_id=identity['example_id'], split_identity=identity['split_identity'],
            question_id=identity['question_id'], run_id=identity['validation_id'], dataset_id=f'{STUDY}-{role}',
            role=role, purpose='calibration', question=row['question'], answer=row['answer'], reference=row['context'],
            analysis=analyzer.analyze(row['question']), label=dict(answer_is_correct=True,
                label_source=f'{STUDY}-external-{key}', label_method='independent_ground_truth',
                provenance=json.dumps(dict(status='DRAFT: review required', evidence_id=content_id(audit),
                    source=support['url'], source_comparison=support['rationale'],
                    retrieved='2026-10-26', benchmark_flags_used=False), sort_keys=True)))
        examples.append(example.model_dump(mode='json'))
        plans.append(dict(example_id=example.example_id,
            **collection_plan(SimpleNamespace(candidates=candidates), example)))
    reservation = dict(version='final_test_reservation_v1', role='final_test',
        dataset_id=f'{STUDY}-final_test', custody_record=None, examples=reserved)
    request = dict(version='offline_recording_request_v1', intended_use='pilot', study_approval=None,
        preparation_authorization=None, cache_contract='complete_team_independent_v1',
        randomness_control=('Proposed one pass, no warmups/repeats. Split seed 20261026 only. Existing OllamaSampler '
            'uses generation seeds 0..4 per call, n_samples=5, temperature=0.8; provider/runtime determinism is not claimed.'),
        execution_configuration_id=None, factory='app.game.offline.recording_adapters:project_factory',
        expected_setup=None, final_test_reservation=reservation,
        permitted_datasets=[['history', f'{STUDY}-history'], ['development', f'{STUDY}-development']],
        candidates=[c.model_dump(mode='json') for c in candidates], examples=examples)
    preparation = dict(version='approved_collection_preparation_v1', final_test_reservation=reservation,
        preparation_authorization=None, permitted_datasets=request['permitted_datasets'], examples=[dict(
            **{k: e[k] for k in ('example_id', 'split_identity', 'question_id', 'run_id', 'dataset_id',
                                'role', 'purpose', 'question', 'answer')}, context=e['reference']) for e in examples])
    dependencies = DependencyRegistry(version=STUDY+'-dependencies-proposed', dependencies=(
        dict(resource_id='local-embedding-snapshot', compromise_pathway='shared embedding weights', verifiers=('semantic','evidence')),
        dict(resource_id='local-nli-snapshot', compromise_pathway='shared NLI weights', verifiers=('evidence','confidence'))),
        unresolved=('semantic','evidence','rule','confidence'))
    attacks = AttackSpecification(version='report_corruption_v1', suppression='unavailable')
    adapter = AdapterConfiguration.model_validate(adapter)
    resource_plan = dict(status='draft_not_authorized', corpus=adapter.corpus_path,
        index_target=adapter.index_dir, receipt_target=adapter.index_receipt,
        embedding_snapshot=adapter.embedding_snapshot, nli_snapshot=adapter.nli_snapshot,
        articles=10, source_words=216, chunk_size=500, expected_chunks=10,
        embedding_job='encode ten actual title/text chunks once on local CPU with existing EvidenceRetriever',
        old_index_preserved='data/evidence_index/test_evidence_corpus', downloads_planned=0,
        example_runs=len(examples), warmup_runs=0, repeat_passes=1, verifier_attempts=4*len(examples),
        generation_requests_if_all_reached=adapter.n_samples*len(examples),
        factory_metadata_get_requests=4, attempt_observer_metadata_get_requests=4*4*len(examples),
        total_intended_metadata_get_requests=4+4*4*len(examples),
        generation_timeout_upper_bound_seconds=adapter.timeout*adapter.n_samples*len(examples),
        timeout_bound_note='Not expected runtime or an enforced total deadline; model loads/NLI/hash overhead are additional.',
        pricing=None, pricing_note='Local loopback service; no approved price inputs; no monetary estimate inferred.',
        fingerprint_work='50 full model-directory hash passes: two factory inspections plus before/after 24 attempts; cache may reduce physical disk reads.')
    return {
        'roster.draft.json': dict(status='draft_not_approved', study_id=STUDY, seed=SEED,
            grouping_rationale='Group France/Paris and AI/ML together; all paraphrases/alternative answers must stay with their topic group. Custodian reviews broader overlap.',
            allocation=allocation, rows=roster, benchmark_flags_used=False, source_input_digest=source_digest),
        'final-reservation.draft.json': reservation,
        'label-review.draft.json': dict(status='draft_not_approved', preparation_labels=labels, final_labels_created=False),
        'preparation.draft.json': preparation,
        'recording-request.draft.json': request,
        'producer-plans.json': dict(status='observed_heuristic_outputs_and_builtin_descriptors_not_handwritten', examples=plans),
        'adapter.draft.json': adapter.model_dump(mode='json'),
        'resource-plan.json': resource_plan,
        'dependencies.proposed.json': dependencies.model_dump(mode='json'),
        'attacks.proposed.json': attacks.model_dump(mode='json'),
        'execution-contract.draft.json': dict(version='offline_public_decision_v2', coverage_version='factual_output_contract_v1',
            contributor_version='baseline_log_odds_active_group_v1', threshold=.55, failure_contract='all_selected_returned',
            execution_configuration_id=None, history_prior_alpha=1., history_prior_beta=1., resource_manifest=None),
        'calibration-settings.draft.json': dict(measurements=None, final_test_reservation=reservation,
            required_verifiers=['semantic','evidence','rule','confidence'], include_warmups=False, freeze_record=None),
        'loss-settings.proposed.json': dict(status='unapproved', version=STUDY+'-loss-v1',
            false_accept=1., false_reject=1., uncertain=.2, resource_weight=None, budget=None,
            cost_units='ms', history_prior_alpha=1., history_prior_beta=1., threshold=.55,
            minimum_participants=2, explanation='Equal directional-error penalties, uncertainty at one fifth of an error; budget and loss/ms chosen only after measured costs.'),
    }


def validate_package(package):
    validators = {'final-reservation.draft.json': FinalTestReservation,
        'preparation.draft.json': PreparationInput, 'recording-request.draft.json': RecordingRequest,
        'execution-contract.draft.json': ExecutionContract, 'calibration-settings.draft.json': CalibrationRequest,
        'dependencies.proposed.json': DependencyRegistry, 'attacks.proposed.json': AttackSpecification,
        'adapter.draft.json': AdapterConfiguration,
        'recording-config.draft.json': RecordingConfiguration}
    result = {}
    for name, schema in validators.items():
        if name not in package:
            continue
        try:
            schema.model_validate(package[name])
        except ValidationError as exc:
            result[name] = dict(valid=False, unresolved_fields=[dict(location=e['loc'], message=e['msg'])
                for e in exc.errors(include_input=False, include_url=False)])
        else:
            result[name] = dict(valid=True)
    return dict(status='draft_not_executable', contracts=result, verifier_calls=0, model_loads=0,
                labels_and_settings_approved=False, final_outcomes_accessed=False)


def observed_recording_references(inventory):
    """Copy only actually inspected resource references; never invent missing IDs."""
    models = [(key, 'sha256:'+inventory[key]['sha256']) for key in ('embedding_snapshot', 'nli_snapshot')
              if key in inventory]
    if 'service' in inventory:
        models.append(('ollama_model', inventory['service']['model_digest']))
    corpora = [('evidence_corpus', 'sha256:'+inventory['corpus']['sha256'])] if 'corpus' in inventory else []
    prompt = source_constants('app/verifiers/self_consistency.py', {'SHORT_ANSWER_PROMPT'})['SHORT_ANSWER_PROMPT']
    return dict(execution_configuration_id=None, model_fingerprints=models, corpus_fingerprints=corpora,
        prompt_and_adapter_fingerprints=[('self-consistency-short-answer', 'sha256:'+content_id(prompt)),
            ('project-adapter-source', 'sha256:'+file_digest(ROOT / 'app/benchmark/project_adapter.py')),
            ('recording-producer-source', 'sha256:'+file_digest(ROOT / 'app/game/offline/collection.py'))],
        collection_protocol='complete_team_independent_v1')


def bind_inspected_resources(package, preflight):
    """Fill actual resource fields in this draft; leave every approval unresolved."""
    package = deepcopy(package)
    package['recording-config.draft.json'] = observed_recording_references(preflight['inventory'])
    if preflight['ready']:
        setup = MeasurementSetup.model_validate(preflight['observed_setup'])
        execution_id = setup.resources.manifest_id
        package['recording-request.draft.json'].update(expected_setup=setup.model_dump(mode='json'),
            execution_configuration_id=execution_id)
        package['execution-contract.draft.json'].update(resource_manifest=setup.resources.model_dump(mode='json'),
            execution_configuration_id=execution_id)
        package['recording-config.draft.json']['execution_configuration_id'] = execution_id
    return package


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--adapter-config', type=Path, required=True)
    parser.add_argument('--candidate-input', type=Path, required=True, help='Initial custodian inventory before reservation freeze; never a fitting input')
    parser.add_argument('--index-dir', required=True)
    parser.add_argument('--index-receipt', required=True)
    args = parser.parse_args(argv)
    # Output must be new: never regenerate/overwrite an approved or witnessed study.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    raw = args.candidate_input.read_bytes()
    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    adapter = read_json(args.adapter_config)
    adapter.update(index_dir=args.index_dir, index_receipt=args.index_receipt)
    corpus = read_json(ROOT / adapter['corpus_path'])
    if len(corpus) != 10 or sum(len(a['text'].split()) for a in corpus) != 216:
        raise ValueError('corpus changed; revise the concrete resource proposal before proceeding')
    package = draft_package(rows, adapter, source_digest=hashlib.sha256(raw).hexdigest())
    preflight = inspect_setup(package['adapter.draft.json'])
    package = bind_inspected_resources(package, preflight)
    for name, data in package.items():
        (args.output_dir / name).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False), encoding='utf-8')
    validation = validate_package(package)
    validation['resource_preflight'] = preflight
    (args.output_dir / 'validation.json').write_text(json.dumps(validation, indent=2, sort_keys=True, allow_nan=False), encoding='utf-8')
    print(json.dumps(dict(status='draft_not_executable', output=str(args.output_dir),
        preparation_examples=6, final_metadata_rows=4, verifier_attempts_planned=24,
        generation_requests_planned=30, actual_attempts=0)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
