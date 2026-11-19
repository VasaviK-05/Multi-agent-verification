"""No native models, fitting or synthetic artifact certification.

Run with unittest when pytest is unavailable. Probe runtimes below exercise only
the explicit composition boundary, not policy retrieval or scientific validity.
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from pydantic import ValidationError
from app.game.category_runtime import (CategoryInputContract, ReviewedCategory,
    ExactFirstCategoryDispatcher, CategoryGameRuntime)
from app.game.category_applicability import CategoryApplicability

ROOT = Path(__file__).resolve().parents[1]


def inputs(**changes):
    return CategoryInputContract(**(dict(name='binary arithmetic',
        question_pattern=r'What is -?\d+ [+-] -?\d+\?', maximum_question_chars=100,
        requirements=('arithmetic',), reference_required=False, answer_contract='Decimal numeric candidate; invalid answers are evaluated, never routed away',
        domain='general', domain_status='unknown', difficulty='easy', difficulty_score=.1) | changes))


class ProbeRuntime:
    def __init__(self, value):
        self.value, self.calls = value, []

    def run(self, *args):
        self.calls.append(args)
        return self.value


class CategoryBoundaryTests(unittest.TestCase):
    def test_existing_source_policy_and_resource_bytes_are_preserved(self):
        before = json.loads((ROOT/'docs/category-generalization-v1/validation/preservation-before.json').read_text())
        self.assertEqual(len(before['files']), 661)
        import importlib.util
        spec = importlib.util.spec_from_file_location('category_preservation', ROOT/'docs/category-generalization-v1/validation/preservation.py')
        preservation = importlib.util.module_from_spec(spec); spec.loader.exec_module(preservation)
        self.assertEqual(preservation.preservation_changes(before, preservation.snapshot()), [])
        question_sets = [set(r['questions']) for r in before['registrations'] if 'questions' in r]
        self.assertEqual(len(question_sets), 3)
        self.assertTrue(all(q == question_sets[0] for q in question_sets))

    def test_every_published_exact_question_delegates_verbatim_without_category(self):
        questions = json.loads((ROOT/'reconciliation/policies.json').read_bytes())['allowed_questions']
        self.assertEqual(len(questions), 69)
        sentinel = object()
        legacy, category = ProbeRuntime(sentinel), ProbeRuntime(object())
        runtime = ExactFirstCategoryDispatcher(legacy, questions, category)
        for question in questions:
            args = (object(), object(), SimpleNamespace(question=question), 'same-validation-id')
            self.assertIs(runtime.run(*args), sentinel)
            self.assertEqual(legacy.calls[-1], args)
        self.assertEqual(category.calls, [])

    def test_exact_failure_is_returned_without_fallback(self):
        failed = SimpleNamespace(public_status='uncertain')
        legacy, category = ProbeRuntime(failed), ProbeRuntime(object())
        runtime = ExactFirstCategoryDispatcher(legacy, ['registered'], category)
        self.assertIs(runtime.run(None, None, SimpleNamespace(question='registered'), 'v'), failed)
        self.assertFalse(category.calls)

    def test_unseen_question_reaches_only_category_boundary(self):
        legacy, category = ProbeRuntime(object()), ProbeRuntime(object())
        runtime = ExactFirstCategoryDispatcher(legacy, ['What is 3 + 3?'], category)
        request = SimpleNamespace(question='What is 4 + 4?', answer='9')
        self.assertIs(runtime.run(None, None, request, 'v'), category.value)
        self.assertFalse(legacy.calls)

    def test_composition_uses_actual_legacy_configuration(self):
        legacy = ProbeRuntime(object())
        legacy._configuration = SimpleNamespace(allowlist=frozenset(['old']))
        category = ProbeRuntime(object())
        runtime = CategoryGameRuntime.compose(legacy, category)
        self.assertIs(runtime.run(None, None, SimpleNamespace(question='old'), 'v'), legacy.value)

    def test_unbounded_legacy_composition_rejected(self):
        for legacy in (ProbeRuntime(None), SimpleNamespace(_configuration=SimpleNamespace(allowlist=None))):
            with self.assertRaises(ValueError):
                CategoryGameRuntime.compose(legacy, ProbeRuntime(None))

    def test_input_contract_is_category_based_and_fail_closed(self):
        contract = inputs()
        self.assertTrue(contract.matches('What is 4 + 4?'))
        self.assertTrue(contract.matches('What is 234 - 97?'))
        self.assertFalse(contract.matches('What is 4 + 4? Explain why.'))
        self.assertFalse(contract.matches('What is 4 ** 4?'))
        self.assertFalse(contract.matches('x'*101))
        self.assertNotEqual(contract.contract_id, inputs(maximum_question_chars=101).contract_id)
        self.assertTrue(contract.scoring_version.startswith('category_input_v2:'))

    def test_semantic_requires_reference_and_all_four_requirements_can_be_declared(self):
        for requirement in ('arithmetic','direct_fact','semantic_comparison','consistency'):
            contract = inputs(requirements=(requirement,), reference_required=requirement=='semantic_comparison')
            self.assertEqual(contract.requirements, (requirement,))
        with self.assertRaises(ValidationError):
            inputs(requirements=('semantic_comparison',))
        with self.assertRaises(ValidationError):
            inputs(requirements=('arbitrary_fact_check',))

    def test_unimplemented_achieved_coverage_is_explicitly_blocked(self):
        self.assertIsNone(inputs().runtime_coverage_reason())
        self.assertIn('consistency', inputs(requirements=('consistency',)).runtime_coverage_reason())
        self.assertIn('evidence_retrieval', inputs(requirements=('evidence_retrieval',)).runtime_coverage_reason())

    def test_missing_changed_wrong_scope_or_reused_dataset_reports_rejected(self):
        contract = inputs()
        def review(dataset='test', scope=None):
            reports, digests = {}, {}
            for role in ('development','held_out','baseline'):
                raw = json.dumps(dict(version='category_evaluation_report_v2', role=role,
                    artifact_id='a'*64, input_contract_id=scope or contract.contract_id,
                    dataset_id='development' if role=='development' else dataset)).encode()
                digest = hashlib.sha256(raw).hexdigest()
                reports[digest], digests[role] = raw, digest
            declaration = CategoryApplicability(artifact_id='a'*64, task_id='b'*64,
                supported_distribution='fixture only', exclusions=(), reviewed_by='TEST ONLY',
                development_report=digests['development'], held_out_report=digests['held_out'],
                baseline_report=digests['baseline'], evaluated_scenarios=('correct','incorrect','uncertain','unsupported','resource_unavailable'),
                evaluated_teams=(('rule',),))
            return ReviewedCategory(inputs=contract, declaration=declaration), reports
        reviewed, reports = review()
        reviewed.verify_reports(reports)
        with self.assertRaises(ValueError):
            reviewed.verify_reports({})
        with self.assertRaises(ValueError):
            reviewed.verify_reports({key: b'changed' for key in reports})
        reviewed, reports = review(scope='f'*64)
        with self.assertRaises(ValueError):
            reviewed.verify_reports(reports)
        reviewed, reports = review(dataset='development')
        with self.assertRaises(ValueError):
            reviewed.verify_reports(reports)


if __name__ == '__main__':
    unittest.main()
