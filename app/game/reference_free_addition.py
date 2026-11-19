"""Opt-in reference-free addition preparation; no policy fitting or activation.

Resource observation trusts a reviewed integration adapter, just as GameRuntime
does. A matching fingerprint is consistency evidence, not scientific accuracy or
adapter authentication. Historical policies are never converted here.
"""
import re
from typing import Literal

from app.game.dependencies import FrozenModel
from app.game.models import PlanningContext, capture_context, content_id
from app.game.execution_contract import ExecutionContract
from app.game.resource_provenance import ResourceManifest
from app.game.strategies import enumerate_strategies


class ReferenceFreeAdditionContract(FrozenModel):
    version: Literal['reference_free_addition_v1'] = 'reference_free_addition_v1'
    maximum_question_chars: Literal[160] = 160
    maximum_absolute_operand: Literal[10000] = 10000
    context_contract: Literal['absent_only'] = 'absent_only'
    answer_contract: Literal['signed_integer_candidate_not_ground_truth'] = 'signed_integer_candidate_not_ground_truth'

    @property
    def contract_id(self):
        return content_id(self.model_dump(mode='json'))

    def operands(self, question, context=None):
        if context is not None:
            raise ValueError('reference-free addition requires absent context')
        if not isinstance(question,str) or len(question)>self.maximum_question_chars:
            raise ValueError('question outside reference-free addition bounds')
        # Reuse the native parser's grammar; never compute a reference here.
        from app.verifiers.rule_verifier import ARITHMETIC_PATTERNS, WORD_ARITHMETIC_PATTERNS
        operands=None
        for pattern in ARITHMETIC_PATTERNS:
            match=pattern.fullmatch(question.strip())
            if match and match.group(2)=='+':
                operands=(match.group(1),match.group(3));break
        if operands is None:
            for operator,pattern in WORD_ARITHMETIC_PATTERNS:
                match=pattern.fullmatch(question.strip())
                if operator=='+' and match:
                    operands=match.groups();break
        if operands is None or any(re.fullmatch(r'-?[0-9]+',v) is None for v in operands):
            raise ValueError('supported two-operand integer addition grammar required')
        values=tuple(int(v) for v in operands)
        if any(abs(v)>self.maximum_absolute_operand for v in values):
            raise ValueError('operand outside declared bounds')
        return values

    def validate_request(self, request):
        self.operands(request.question,request.context)
        if (not isinstance(request.answer,str) or len(request.answer)>160
            or re.fullmatch(r'-?[0-9]+',request.answer.strip()) is None):
            raise ValueError('signed integer candidate required')
        return request  # wrong answers stay eligible; no expected-answer field

    def analyze(self, question):
        """Question-only opt-in analyzer for the validated grammar, never labels."""
        self.operands(question)
        from app.analysis.task_analyzer import TaskQuestionAnalyzer
        from app.analysis.research_context import build_research_context
        analysis=TaskQuestionAnalyzer().analyze(question)
        analysis.verification_types=['arithmetic']
        analysis.research_context=build_research_context(analysis)
        analysis.research_context.scoring_version=self.version
        return analysis

    def prepare_context(self, selector, question, *, configuration):
        """Fresh pre-history planning only; empirical bindings come from new data.

        Caller supplies explicit costs/budget/reputation/resources and new study
        provenance. No old evaluation, task history or reliability certificate is
        silently inherited. This does not create a deployable artifact.
        """
        self.operands(question)
        forbidden={'offline_evaluation_id','clean_coverage_json','reliability_first_json',
                   'task_conditioning_json','pooling_contract_json'}
        if any(configuration.get(key) is not None for key in forbidden):
            raise ValueError('fresh study required; historical evaluation/history bindings forbidden')
        analysis=self.analyze(question)
        data=dict(configuration)
        current=capture_context(selector,analysis,context=None,**data)
        if current.provenance.matrix_version!=self.version:
            raise ValueError('separate reference-free study provenance required')
        if any(not getattr(current.provenance,key).startswith(self.version+'-')
               for key in ('history_dataset','development_dataset','final_test_dataset')):
            raise ValueError('new versioned dataset identities required; label independence still needs review')
        self.check_context(current)
        return current

    def check_context(self, current):
        current=PlanningContext.model_validate(current)
        if (current.provenance.matrix_version!=self.version or current.plan.reference_available
            or current.plan.scoring_version!=self.version
            or current.plan.requirements.requirements!=('arithmetic',)
            or current.plan.requirements.unsupported):
            raise ValueError('incompatible reference-free addition planning context')
        contract=ExecutionContract.model_validate_json(current.execution_contract_json or '{}')
        from app.selection.capabilities import BUILTIN_CAPABILITIES
        if {c.verifier_name for c in current.plan.candidates}!=set(BUILTIN_CAPABILITIES):
            raise ValueError('retain the full declared builtin planning roster')
        for row in current.plan.candidates:
            descriptor=BUILTIN_CAPABILITIES[row.verifier_name]
            if (row.expected_capabilities!=descriptor.expected_capabilities
                or row.requires_reference!=descriptor.requires_reference):
                raise ValueError('builtin capability/reference contract differs')
        if (contract.version!='offline_public_decision_v4'
            or contract.failure_contract!='all_selected_returned'
            or contract.contributor_version!='informative_history_influence_v1'
            or contract.coverage_version!='task_output_contract_v2'
            or contract.resource_manifest is None):
            raise ValueError('complete resource-bound informative task execution required')
        contract.resource_manifest.require_candidates(c.verifier_name for c in current.plan.candidates)
        return contract


def qualify_strategies(contract, current, *, selector=None, resource_observer=None):
    """Keep every planning-feasible row; mark resource blocks without reweighting.

    Actual-instance snapshot_for must be supplied by a reviewed resource adapter.
    No metadata-only selector readiness flag or caller-supplied manifest is an
    attestation. This function neither resolves verifiers nor executes/fits them.
    Integration remains responsible for authenticating its observer, and execution
    MUST re-observe resources and retain all GameRuntime guards.
    """
    contract=ReferenceFreeAdditionContract.model_validate(contract)
    execution=contract.check_context(current)
    enumeration=enumerate_strategies(current)
    expected={v.verifier_name:v for v in execution.resource_manifest.verifiers}
    observed={};failure=None;manifest_id=None
    try:
        if selector is None or not callable(getattr(resource_observer,'snapshot_for',None)):
            raise ValueError('actual-instance resource observer required')
        first=ResourceManifest.model_validate(resource_observer.snapshot_for(selector))
        second=ResourceManifest.model_validate(resource_observer.snapshot_for(selector))
        if first!=second:raise ValueError('resources changed during qualification')
        if any(v.verifier_name not in expected for v in first.verifiers):
            raise ValueError('unexpected resource candidate')
        observed={v.verifier_name:v for v in first.verifiers}
        manifest_id=first.manifest_id
    except (ValueError,TypeError,OSError) as exc:
        failure=str(exc)
    rows=[]
    for strategy in enumeration.strategies:
        reasons=([failure] if failure else [
            'missing or incompatible actual resources: '+name for name in strategy.verifiers
            if observed.get(name)!=expected[name]])
        rows.append(dict(strategy=strategy.model_dump(mode='json'),
            resource_status='blocked' if reasons else 'observed_compatible',reasons=reasons))
    return dict(version='reference_free_addition_resource_preparation_v1',contract_id=contract.contract_id,
        compatibility_id=current.compatibility_id,enumeration=enumeration.model_dump(mode='json'),
        resource_rows=rows,observed_manifest_id=manifest_id,
        qualification_scope='preparation only; not policy certification or deployment authorization')
