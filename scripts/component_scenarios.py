"""Diagnostic constituent-history scenarios; explicitly NOT compound training."""
from app.game.component_binding import question_plan, bind_answer
from app.game.component_execution import ComponentContract, Obligation
from app.game.models import PlanningContext, capture_context
from app.game.frozen_planning import FrozenPlanningReputation
from app.analysis.capability_probe_analyzer import CapabilityProbeAnalyzer
from app.game.question_routing import classify_question
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.game.execution_contract import ExecutionContract


def diagnostic_contract(question, reference, bases, verifiers):
    """Use unchanged weights in new explicitly untrained planning contexts.

    No correctness labels or true base values enter the component plan. The dummy
    supplied values below only provide numeric syntax for planning, not execution.
    """
    components = bind_answer(question_plan(question), '{"base":"0","derived":"0"}')
    obligations = []
    for component, family in zip(components, ('factual', 'arithmetic')):
        base = PlanningContext.model_validate(bases[family])
        selector = VerifierSelector(verifiers=verifiers,
            reputation_manager=FrozenPlanningReputation(base), capabilities=BUILTIN_CAPABILITIES)
        config = base.model_dump(exclude={'selection_json', 'analyzer_provenance'})
        config.update(offline_evaluation_id=None, pooling_contract_json=None,
            clean_coverage_json=None, reliability_first_json=None, task_conditioning_json=None)
        context = capture_context(selector, CapabilityProbeAnalyzer().analyze(component.question),
            context=reference, **config)
        obligations.append(Obligation(component_id=component.component_id, context=context,
            contract=ExecutionContract.model_validate_json(context.execution_contract_json)))
    return ComponentContract(category=question_plan(question).measure,
        question_signature=classify_question(question, reference)[1],
        obligations=tuple(obligations), budget=float(sum(o.context.budget for o in obligations)))
