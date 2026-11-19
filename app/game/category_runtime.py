"""Separately versioned, opt-in category runtime; never selected by app settings.

Installation requires reviewed report bytes and newly scoped frozen artifacts.
Existing exact-question requests are delegated verbatim, even on failure. This
module performs no fitting, inference, factory construction or implicit fallback.
"""
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Literal

from pydantic import Field, StrictBool, model_validator
from app.game.dependencies import FrozenModel
from app.game.category_applicability import CategoryApplicability

VERSION = 'category_game_runtime_v2'
REQUIREMENTS = frozenset(('arithmetic', 'direct_fact', 'evidence_retrieval',
                          'semantic_comparison', 'consistency'))


class CategoryInputContract(FrozenModel):
    version: Literal['category_input_v2'] = 'category_input_v2'
    name: str = Field(min_length=1)
    # Trusted operator configuration; never read a pattern from a user request.
    question_pattern: str = Field(min_length=1, max_length=2000)
    maximum_question_chars: int = Field(gt=0, le=10000)
    requirements: tuple[str, ...]
    reference_required: StrictBool
    answer_contract: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    domain_status: Literal['clear', 'mixed', 'unknown']
    difficulty: Literal['easy', 'medium', 'hard']
    difficulty_score: float = Field(ge=0, le=1)

    @model_validator(mode='after')
    def check(self):
        re.compile(self.question_pattern)
        if (not self.requirements or tuple(sorted(set(self.requirements))) != self.requirements
                or not set(self.requirements) <= REQUIREMENTS):
            raise ValueError('require sorted unique implemented requirements')
        if 'semantic_comparison' in self.requirements and not self.reference_required:
            raise ValueError('semantic comparison requires an external reference')
        return self

    @property
    def contract_id(self):
        # Canonical encoding contains no inferred question/answer truth.
        value = self.model_dump(mode='json')
        if value['difficulty_score'] == 0:
            value['difficulty_score'] = 0.0
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
            ensure_ascii=False, allow_nan=False).encode()).hexdigest()

    @property
    def scoring_version(self):
        return 'category_input_v2:' + self.contract_id

    def matches(self, question):
        return (isinstance(question, str) and len(question) <= self.maximum_question_chars
                and re.fullmatch(self.question_pattern, question) is not None)

    def analyze(self, question):
        """Fixed, declared category profile, not empirical difficulty prediction.

        Contract hash enters task identity, so historical analyzer artifacts cannot
        be relabelled. Requirements describe obligations, never a selected team.
        """
        if not self.matches(question):
            raise ValueError('question outside declared category input contract')
        from app.analysis.models import QuestionAnalysis
        from app.analysis.research_context import build_research_context
        analysis = QuestionAnalysis(domain=self.domain, domain_status=self.domain_status,
            difficulty=self.difficulty, difficulty_score=self.difficulty_score,
            verification_types=list(self.requirements), analysis_method='heuristic')
        analysis.research_context = build_research_context(analysis)
        analysis.research_context.scoring_version = self.scoring_version
        return analysis

    def runtime_coverage_reason(self, coverage_version="task_output_contract_v2"):
        # The unchanged task_output_contract_v2 recognizes only these outputs.
        # In particular Confidence contributes influence but has no standalone
        # achieved-consistency contract. Do not waive unresolved coverage.
        supported = {'arithmetic', 'direct_fact', 'semantic_comparison'}
        if coverage_version == 'game_assessment_output_v3':
            supported.add('consistency')
        missing = set(self.requirements) - supported
        if missing:
            return 'existing finalization has no achieved-output contract for: ' + ', '.join(sorted(missing))
        return None

    def prerequisite_reason(self, reference):
        from app.selection.capabilities import BUILTIN_CAPABILITIES, prerequisite_status
        from app.verifiers.confidence_verifier import parse_judgment_list
        present = bool(reference and reference.strip())
        if present != self.reference_required:
            return 'reference presence differs from category contract'
        if parse_judgment_list(reference) is not None:
            return 'judgment-label context is outside native category execution contract'
        if self.reference_required:
            status, reason = prerequisite_status(BUILTIN_CAPABILITIES['semantic'], reference)
            if status == 'missing_reference':
                return reason
        # Additional factual/retrieval quality remains an execution obligation.
        return None


class ReviewedCategory(FrozenModel):
    version: Literal['reviewed_category_v2'] = 'reviewed_category_v2'
    inputs: CategoryInputContract
    declaration: CategoryApplicability

    def verify_reports(self, reports):
        """Check retained byte identities and scope binding, not scientific validity.

        reports maps raw SHA256 to bytes. Review/custody remains the operator's
        responsibility; arbitrary declarations alone cannot enable this runtime.
        """
        datasets = []
        for role, digest in (('development', self.declaration.development_report),
                             ('held_out', self.declaration.held_out_report),
                             ('baseline', self.declaration.baseline_report)):
            raw = reports.get(digest)
            if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError('missing or changed ' + role + ' report bytes')
            value = json.loads(raw)
            if (value.get('version') != 'category_evaluation_report_v2'
                    or value.get('role') != role
                    or value.get('artifact_id') != self.declaration.artifact_id
                    or value.get('input_contract_id') != self.inputs.contract_id):
                raise ValueError('report scope/role differs from reviewed category')
            if role != 'baseline':
                dataset = value.get('dataset_id')
                if not isinstance(dataset, str) or not dataset.strip():
                    raise ValueError('evaluation dataset identity required')
                datasets.append(dataset)
        if len(set(datasets)) != 2:
            raise ValueError('development and untouched held-out datasets must differ')


@dataclass(frozen=True)
class CategoryBinding:
    reviewed: ReviewedCategory
    artifact: object


class ExactFirstCategoryDispatcher:
    """Composition boundary: exact routes always win, including failures.

    exact_questions must be the complete immutable legacy registration set.
    Used internally by CategoryGameRuntime; no routing state is changed globally.
    """
    def __init__(self, legacy_runtime, exact_questions, category_runtime):
        self._legacy = legacy_runtime
        self._exact = frozenset(exact_questions)
        self._category = category_runtime

    def run(self, selector, analysis, request, validation_id, *, execution_journal=None):
        runtime = self._legacy if request.question in self._exact else self._category
        options = {} if execution_journal is None else {"execution_journal": execution_journal}
        return runtime.run(selector, analysis, request, validation_id, **options)


class CategoryGameRuntime:
    """Owned runtime engine, exposed through category_deployment adapter.

    No settings/default wiring is added. The caller supplies its actual selector
    and provenance observer. No singleton/factory substitution is inferred here.
    """
    def __init__(self, bindings, *, reports, rng, resource_observer, allow_synthetic_for_tests=False):
        from app.game.artifacts import DeploymentEpisode, InMemoryPolicyProvider
        from app.game.task_conditioning import TaskSnapshotBinding, TaskPolicyRouter
        if type(allow_synthetic_for_tests) is not bool:
            raise TypeError("test-only permission must be an explicit boolean")
        self._allow_synthetic_for_tests = allow_synthetic_for_tests
        captured, artifacts, routes = [], [], []
        for binding in bindings:
            reviewed = ReviewedCategory.model_validate(binding.reviewed)
            reviewed.verify_reports(reports)
            artifact = reviewed.declaration.validate_artifact(binding.artifact)
            coverage_reason = reviewed.inputs.runtime_coverage_reason(artifact.contract.coverage_version)
            if coverage_reason:
                raise ValueError(coverage_reason)
            if artifact.policy.provenance.evidence_kind != 'empirical' and not allow_synthetic_for_tests:
                raise ValueError('category runtime requires empirical policies')
            if (artifact.contract.version not in {'offline_public_decision_v4','offline_public_decision_v5'}
                    or artifact.contract.resource_manifest is None):
                raise ValueError('category runtime requires task-aware resource-bound execution')
            identity = TaskSnapshotBinding.model_validate_json(artifact.context.task_conditioning_json).identity
            inputs = reviewed.inputs
            if (identity.question_rules_version != inputs.scoring_version
                    or identity.subject_domain != inputs.domain
                    or identity.domain_status != inputs.domain_status
                    or identity.requirements != inputs.requirements):
                raise ValueError('artifact is not fitted under this category input contract')
            for digest in (reviewed.declaration.development_report,
                           reviewed.declaration.held_out_report,
                           reviewed.declaration.baseline_report):
                report = json.loads(reports[digest])
                if set(report.get('strategy_ids', ())) != {s.strategy_id for s in artifact.policy.strategies}:
                    raise ValueError('report must cover every frozen team/aggregation strategy')
            plan = artifact.context.plan
            if (plan.difficulty != inputs.difficulty or plan.difficulty_score != inputs.difficulty_score
                    or plan.reference_available != inputs.reference_required):
                raise ValueError('category profile differs from frozen planning profile')
            signature = (identity.task_id, plan.difficulty, plan.difficulty_score, plan.reference_available)
            episode = DeploymentEpisode(episode_id='category-v2-'+artifact.artifact_id,
                context=artifact.context, contract=artifact.contract,
                execution_configuration_id=artifact.execution_configuration_id)
            routes.append((signature, artifact.context.budget, True, episode, ''))
            captured.append((reviewed, artifact.context.budget))
            artifacts.append(artifact)
        if not captured:
            raise ValueError('category runtime requires at least one reviewed artifact')
        self._bindings = tuple(captured)
        self._router = TaskPolicyRouter(routes)
        self._provider = InMemoryPolicyProvider(artifacts)
        self._rng, self._observer = rng, resource_observer

    @staticmethod
    def compose(legacy_runtime, category_runtime):
        legacy_configuration = getattr(legacy_runtime, "_configuration", None)
        if legacy_configuration is None or legacy_configuration.allowlist is None:
            raise ValueError('cannot compose with an unbounded legacy registration')
        # Capture the actual runtime configuration, never a separately supplied list.
        return ExactFirstCategoryDispatcher(legacy_runtime, legacy_configuration.allowlist, category_runtime)

    def run(self, selector, analysis, request, validation_id, *, execution_journal=None):
        from app.game.component_execution import unavailable
        matches = [(reviewed, budget) for reviewed, budget in self._bindings
                   if reviewed.inputs.matches(request.question)]
        if len(matches) != 1:
            return unavailable('category_scope_unavailable: no unique reviewed category/budget')
        reviewed, budget = matches[0]
        reason = reviewed.inputs.prerequisite_reason(request.context)
        if reason:
            return unavailable('category_prerequisite: ' + reason)
        # Rule obligations are admitted only when the existing parser supports them.
        if 'arithmetic' in reviewed.inputs.requirements:
            from app.verifiers.rule_verifier import ARITHMETIC_PATTERNS, WORD_ARITHMETIC_PATTERNS
            patterns = tuple(ARITHMETIC_PATTERNS) + tuple(p for _, p in WORD_ARITHMETIC_PATTERNS)
            if not any(p.fullmatch(request.question.strip()) for p in patterns):
                return unavailable('category_capability: no implemented arithmetic pattern')
        actual_analysis = reviewed.inputs.analyze(request.question)
        result = self._router.run(selector, actual_analysis, request, validation_id,
            provider=self._provider, rng=self._rng, resource_observer=self._observer,
            budget=budget, allow_synthetic_for_tests=self._allow_synthetic_for_tests,
            execution_journal=execution_journal)
        result.summary.update(category_runtime_version=VERSION,
            category_input_contract_id=reviewed.inputs.contract_id,
            category_applicability_artifact_id=reviewed.declaration.artifact_id)
        return result
