"""Synthetic fixtures only: no empirical performance claims or production state."""

from dataclasses import asdict, replace
import math

import pytest
from pydantic import ValidationError

from app.decision.coverage import factual_capabilities
from app.decision.vote_normalization import is_abstention, signed_mass
from app.game.models import PlanningContext, canonical_json
from app.game.policy import validate_policy
from app.game.strategies import enumerate_strategies
from app.game.offline.attacks import AttackSpecification, enumerate_attacks, transform
from app.game.offline.evaluation import (bind_evaluation, construct_payoffs, evaluate_final_test,
                                         fit_policy, summarize)
from app.game.offline.records import Attempt, Example, Partition, DatasetManifest, history_reputation
from app.game.offline.replay import ReplayContract, category_id, replay
from app.models.schemas import VerificationResult
from tests.test_game_foundation import make_context


def report(name="a", *, passed=True, strength=1., metadata=None):
    return VerificationResult(verifier_name=name, passed=passed, score=strength,
        metadata=metadata if metadata is not None else {"decision": "SUPPORT" if passed else "REJECT",
                                                       "rule_kind": "factual", "rule": "arithmetic_addition"})


def attempt(name="a", *, run="development", state="directional", row=None, adapter="generic_v1"):
    if row is None and state in {"directional", "abstention"}:
        row = report(name, metadata={"decision": "UNSURE"}) if state == "abstention" else report(name)
    return Attempt(verifier_name=name, state=state, report_json=None if row is None else row.model_dump_json(),
        execution_id=run, configuration_id="fixture-execution-v1", report_provenance="synthetic_recording",
        adapter=adapter)


def fixture(*, names=("a",), failure="all_selected_returned", labels=("arithmetic",)):
    specification = AttackSpecification(version="report_corruption_v1", suppression="unavailable")
    context = make_context(names=names, labels=labels)
    data = context.model_dump()
    data["provenance"]["attack_specification"] = specification.specification_id
    context = PlanningContext(**data)
    contract = ReplayContract(version="offline_public_decision_v1", coverage_version="factual_output_contract_v1",
        contributor_version="baseline_log_odds_active_group_v1", threshold=.55, failure_contract=failure,
        execution_configuration_id="fixture-execution-v1", history_prior_alpha=1., history_prior_beta=1.)
    parts = []
    for role, dataset in (("history", "history-v1"), ("development", "development-v1"), ("final_test", "test-v1")):
        example = Example(example_id=role, split_identity=role, question_id=role, question=role+" question",
            answer="fixture answer", reference=None, domain="general", planning_category=context.compatibility_id,
            answer_is_correct=True, label_source="fixture-independent-label", label_method="independent_ground_truth",
            validation_id=role, execution_configuration_id="fixture-execution-v1",
            cache_contract="complete_team_independent_v1",
            attempts=tuple(attempt(n, run=role, state="abstention" if role == "history" else "directional") for n in names))
        parts.append(Partition(role=role, dataset_id=dataset, examples=(example,)))
    manifest = DatasetManifest(version="fixture-v1", evidence_kind="synthetic_test_fixture", partitions=tuple(parts))
    bound = bind_evaluation(context, manifest, contract, specification)
    return bound, manifest, contract, specification


def change_example(manifest, role, **updates):
    data = manifest.model_dump()
    for part in data["partitions"]:
        if part["role"] == role:
            part["examples"][0].update(updates)
    return DatasetManifest(**data)


def unbind(context):
    return PlanningContext(**{**context.model_dump(), "offline_evaluation_id": None})


def test_development_matrix_hand_losses_cost_once_and_policy_final_test():
    context, manifest, contract, specification = fixture()
    policy, evaluation = fit_policy(context, manifest, contract, specification)
    assert evaluation.matrix.strategy_definitions == enumerate_strategies(context).strategies
    # Clean/support/inflation accept correctly; forced rejection fails; suppression uncertain.
    for row in evaluation.matrix.values:
        assert row == pytest.approx((.1, .1, 1.1, .1, .3))
    assert len(evaluation.outcomes) == 10
    assert all(o.estimated_attempt_cost == 1. for o in evaluation.outcomes)
    final = evaluate_final_test(policy, context, manifest, contract, specification)
    assert final.role == "final_test" and final.policy_id == policy.policy_id
    assert final.probabilities == policy.solution.probabilities
    assert {o.example_id for o in final.outcomes} == {"final_test"}
    assert final.attack_metrics[-1][1].decision_coverage == 0
    assert final.attack_metrics[-1][1].selective_risk is None
    assert final.attack_metrics[-1][1].mean_loss == pytest.approx(.3)
    assert policy.provenance.evidence_kind == "synthetic_test_fixture"


@pytest.mark.parametrize("field,value", [("split_identity", "history"), ("question_id", "history"),
    ("example_id", "history"), ("validation_id", "history")])
def test_cross_role_leakage_is_rejected(field, value):
    _, manifest, _, _ = fixture()
    with pytest.raises(ValueError):
        change_example(manifest, "development", **{field: value})


def test_duplicate_content_rejected_despite_distinct_names():
    _, manifest, _, _ = fixture()
    with pytest.raises(ValueError, match="leakage"):
        change_example(manifest, "development", question="history question")


def test_label_requires_explicit_boolean_and_independent_method():
    _, manifest, _, _ = fixture()
    for changes in ({"answer_is_correct": "true"}, {"label_method": "verifier_agreement"}, {"label_source": ""}):
        with pytest.raises(ValueError):
            change_example(manifest, "development", **changes)


def test_records_detach_and_preserve_returned_failure_missing_distinctions():
    row = report()
    record = attempt(row=row)
    row.metadata.clear()
    extracted = record.report
    extracted.metadata.clear()
    assert record.report.metadata["decision"] == "SUPPORT"
    for state in ("failed", "unavailable", "missing"):
        assert attempt(state=state).report is None
    with pytest.raises(ValueError, match="normalized"):
        attempt(state="abstention", row=report())
    with pytest.raises(ValueError):
        attempt(state="failed", row=report())


@pytest.mark.parametrize("name,adapter,row", [
    ("rule", "rule_v1", report("rule", passed=False, strength=0., metadata={"rule": "arithmetic_addition", "rule_kind": "factual", "decision": "REJECT"})),
    ("evidence", "evidence_v1", report("evidence", passed=False, strength=.7, metadata={"nli_label": "contradiction", "decision": "REJECT",
        "contradicting": [{"nli_label": "contradiction", "document": "fixture"}], "supporting": [], "claim_decisions": [{"decision": "REJECT"}]})),
    ("confidence", "confidence_v1", report("confidence", passed=False, strength=.7, metadata={"judgments": ["reject", "reject"], "majority_label": "reject"})),
    ("semantic", "semantic_v1", report("semantic", passed=False, strength=.7)),
    ("a", "generic_v1", report("a", passed=False, strength=.7)),
])
def test_verifier_aware_attack_postconditions_and_copied_state(name, adapter, row):
    context, _, _, specification = fixture(names=(name,))
    actions = enumerate_attacks(context.dependencies, specification)
    before = row.model_dump_json()
    record = attempt(name, row=row, adapter=adapter)
    for action in actions[1:4]:
        changed, audit = transform(record, action, specification)
        expected = 1. if action.kind == "forced_support" else -1.
        assert signed_mass(changed.report) == expected
        assert audit.experiment == "report_level_corruption"
        if name == "evidence":
            assert factual_capabilities(changed.report) == {"direct_fact"}
    assert row.model_dump_json() == before and record.report.model_dump() == row.model_dump()


@pytest.mark.parametrize("state", ["abstention", "unavailable", "failed", "missing"])
def test_directional_attacks_preserve_non_directional_outcomes(state):
    context, _, _, specification = fixture()
    for action in enumerate_attacks(context.dependencies, specification)[1:4]:
        before = attempt(state=state)
        changed, audit = transform(before, action, specification)
        assert changed == before and not audit.effective


@pytest.mark.parametrize("mode", ["unavailable", "abstention"])
def test_explicit_suppression_semantics(mode):
    context, _, _, old = fixture()
    spec = AttackSpecification(version=old.version, suppression=mode)
    action = enumerate_attacks(context.dependencies, spec)[-1]
    changed, audit = transform(attempt(), action, spec)
    assert changed.state == mode and audit.effective
    if mode == "abstention":
        assert is_abstention(changed.report)


def test_fixed_full_registry_actions_project_same_column_without_retargeting():
    from app.game.dependencies import Dependency, DependencyRegistry
    context, _, _, spec = fixture(names=("a", "b", "c"))
    data = context.model_dump(); data["dependencies"] = DependencyRegistry(version="fixture", dependencies=(
        Dependency(resource_id="ab", compromise_pathway="fixture service", verifiers=("a", "b")),
        Dependency(resource_id="bc", compromise_pathway="fixture service", verifiers=("b", "c")))).model_dump()
    registry = PlanningContext(**data).dependencies
    actions = enumerate_attacks(registry, spec)
    assert len(actions) == 5 and actions[1].members == ("a", "b", "c")
    assert registry.groups(("a",))[0].group_id == actions[1].group_id
    assert registry.groups(("c",))[0].group_id == actions[1].group_id
    for name in ("a", "c"):
        assert transform(attempt(name), actions[2], spec)[1].attack_id == actions[2].attack_id
    other, audit = transform(attempt("outside"), actions[2], spec)
    assert other.report.passed and audit.reason == "outside_target"


def test_missing_recordings_rejected_without_denominator_omissions():
    context, manifest, contract, spec = fixture()
    missing = change_example(manifest, "development", attempts=(attempt(state="missing"),))
    bound = bind_evaluation(unbind(context), missing, contract, spec)
    with pytest.raises(ValueError, match="missing recording"):
        construct_payoffs(bound, missing, contract, spec)


@pytest.mark.parametrize("state", ["unavailable", "failed"])
def test_failed_attempts_charged_and_public_coverage_overrides_score(state):
    context, manifest, contract, spec = fixture(names=("a", "b"))
    changed = change_example(manifest, "development", attempts=(attempt("a"), attempt("b", state=state)))
    context = bind_evaluation(unbind(context), changed, contract, spec)
    team = next(s for s in enumerate_strategies(context).strategies if s.verifiers == ("a", "b") and s.aggregation == "dependency_group")
    result = replay(context, team, enumerate_attacks(context.dependencies, spec)[0], spec, contract, changed.partition("development").examples[0])
    assert result.numerical_status == "passed" and result.public_status == "uncertain"
    assert "selected_execution_incomplete" in result.reasons and result.estimated_attempt_cost == 2.
    relaxed = ReplayContract(**{**contract.model_dump(), "failure_contract": "allow_failed_if_covered"})
    assert replay(context, team, enumerate_attacks(context.dependencies, spec)[0], spec, relaxed, changed.partition("development").examples[0]).public_status == "passed"


def test_numerical_result_cannot_invent_achieved_coverage():
    context, manifest, contract, spec = fixture()
    changed = change_example(manifest, "development", attempts=(attempt(row=report(metadata={"decision": "SUPPORT"})),))
    context = bind_evaluation(unbind(context), changed, contract, spec)
    result = construct_payoffs(context, changed, contract, spec).outcomes[0]
    assert result.numerical_status == "passed" and result.public_status == "uncertain"
    assert result.unresolved == ("arithmetic",)


def test_uncertifiable_requirement_remains_explicit():
    context, manifest, contract, spec = fixture(labels=("consistency",))
    # Existing fixture candidates only have arithmetic. Deliberately declare the
    # expected consistency capability, without fabricating an achieved certificate.
    plan = context.plan
    candidates = tuple(replace(c, expected_capabilities=("consistency",)) for c in plan.candidates)
    data = unbind(context).model_dump();data["selection_json"] = canonical_json(asdict(replace(plan, candidates=candidates)))
    context = PlanningContext(**data)
    parts = manifest.model_dump()
    for part in parts['partitions']:
        for example in part['examples']: example['planning_category'] = context.compatibility_id
    manifest = DatasetManifest(**parts);context = bind_evaluation(context, manifest, contract, spec)
    outcome = construct_payoffs(context, manifest, contract, spec).outcomes[0]
    assert outcome.unresolved == ("consistency",) and outcome.public_status == "uncertain"


@pytest.mark.parametrize("field,value", [("threshold", .7), ("failure_contract", "allow_failed_if_covered"),
                                         ("history_prior_alpha", 2.)])
def test_replay_configuration_incompatibility(field, value):
    context, manifest, contract, spec = fixture()
    policy, _ = fit_policy(context, manifest, contract, spec)
    changed = ReplayContract(**{**contract.model_dump(), field: value})
    with pytest.raises(ValueError):
        evaluate_final_test(policy, context, manifest, changed, spec)
    fresh = unbind(context)
    if field != "history_prior_alpha":
        rebound = bind_evaluation(fresh, manifest, changed, spec)
        assert rebound.compatibility_id != context.compatibility_id
        with pytest.raises(ValueError, match="incompatible"):
            validate_policy(policy, rebound)


def test_history_isolated_and_development_labels_never_train_snapshot():
    context, manifest, contract, spec = fixture()
    before = context.model_dump_json()
    one = history_reputation(manifest, prior_alpha=1., prior_beta=1.)
    changed = change_example(manifest, "development", answer_is_correct=False)
    two = history_reputation(changed, prior_alpha=1., prior_beta=1.)
    assert one.export_state() == two.export_state()
    one.update_reputation("a", "general", False)
    assert one.export_state() != two.export_state() and context.model_dump_json() == before
    changed_history = change_example(manifest, "history", attempts=(attempt(run="history"),))
    with pytest.raises(ValueError, match="history"):
        bind_evaluation(unbind(context), changed_history, contract, spec)


def test_mixed_metrics_are_expectations_and_zero_coverage_risk_undefined():
    context, manifest, contract, spec = fixture()
    evaluation = construct_payoffs(context, manifest, contract, spec)
    good, bad, uncertain = evaluation.outcomes[0], evaluation.outcomes[2], evaluation.outcomes[4]
    result = summarize(((good, .25), (bad, .75)), context.loss_configuration)
    assert result.correct_accept == .25 and result.false_reject == .75
    assert result.selective_risk == .75 and result.mean_loss == pytest.approx(.85)
    assert summarize(((uncertain, 1.),), context.loss_configuration).selective_risk is None


def test_manifest_order_and_attack_ids_are_stable_and_snapshot_immutable():
    context, manifest, contract, spec = fixture()
    reordered = DatasetManifest(**{**manifest.model_dump(), "partitions": tuple(reversed(manifest.partitions))})
    assert reordered.manifest_id == manifest.manifest_id
    assert bind_evaluation(unbind(context), reordered, contract, spec) == context
    with pytest.raises(ValidationError):
        context.offline_evaluation_id = "changed"


@pytest.mark.parametrize("value", [math.nan, math.inf, -.1, 1.1, True])
def test_invalid_threshold_rejected(value):
    _, _, contract, _ = fixture()
    with pytest.raises(ValueError):
        ReplayContract(**{**contract.model_dump(), "threshold": value})


def test_unsupported_adapter_and_recording_category_rejected():
    context, manifest, contract, spec = fixture(names=("evidence",))
    action = enumerate_attacks(context.dependencies, spec)[1]
    with pytest.raises(ValueError, match="adapter"):
        transform(attempt("evidence", row=report("evidence")), action, spec)
    context, manifest, contract, spec = fixture()
    changed = change_example(manifest, "development", planning_category="incompatible")
    context = bind_evaluation(unbind(context), changed, contract, spec)
    with pytest.raises(ValueError, match="planning category"):
        construct_payoffs(context, changed, contract, spec)


def test_coverage_extraction_matches_committed_baseline_function_without_database_import():
    import ast
    import subprocess
    from app.decision.vote_normalization import vote_confidence
    source = subprocess.check_output(['git', 'show', '566961f52346d490746231f9636851a6ddb403f4:app/orchestration/validation_orchestrator.py'], text=True)
    tree = ast.parse(source)
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_factual_capabilities'
             or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ARITHMETIC_RULES' for t in n.targets)]
    scope = dict(VerificationResult=VerificationResult, is_abstention=is_abstention, vote_confidence=vote_confidence)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<baseline-pure-coverage>', 'exec'), scope)
    for row in (report(), report(metadata={"decision": "SUPPORT"}), report(metadata={"decision": "UNSURE"}),
                report("evidence", metadata={"decision": "SUPPORT", "nli_label": "entailment",
                    "supporting": [{"nli_label": "entailment"}], "claim_decisions": [{"decision": "SUPPORT"}]})):
        assert factual_capabilities(row) == scope['_factual_capabilities'](row)


def test_all_declared_examples_contribute_and_incorrect_answer_losses_are_not_inferred():
    context, manifest, contract, spec = fixture()
    data = manifest.model_dump()
    for part in data['partitions']:
        if part['role'] == 'development':
            second = dict(part['examples'][0], example_id='development-2', question_id='other-question',
                          question='another independently labelled question', split_identity='other-group',
                          validation_id='development-2', answer_is_correct=False,
                          attempts=(attempt(run='development-2').model_dump(),))
            part['examples'] = (*part['examples'], second)
    manifest = DatasetManifest(**data)
    context = bind_evaluation(unbind(context), manifest, contract, spec)
    evaluation = construct_payoffs(context, manifest, contract, spec)
    assert evaluation.matrix.values[0] == pytest.approx((.6, .6, .6, .6, .3))
    assert evaluation.metrics[0][2].examples == 2
    assert evaluation.metrics[0][2].false_accept == 1
    assert len(evaluation.outcomes) == 20


def test_inflation_does_not_create_new_claim_coverage():
    context, _, _, spec = fixture(names=('evidence',))
    row = report('evidence', strength=.3, metadata={'decision': 'SUPPORT', 'nli_label': 'entailment',
        'supporting': [{'nli_label': 'entailment'}], 'claim_decisions': [{'decision': 'UNSURE'}]})
    changed, _ = transform(attempt('evidence', row=row, adapter='evidence_v1'),
                           enumerate_attacks(context.dependencies, spec)[3], spec)
    assert signed_mass(changed.report) == 1.
    assert factual_capabilities(row) == factual_capabilities(changed.report) == set()
    assert changed.report.metadata['claim_decisions'] == row.metadata['claim_decisions']


def test_attack_effectiveness_includes_changed_coverage_when_vote_mass_is_unchanged():
    context, _, _, spec = fixture(names=('evidence',))
    row = report('evidence', strength=1., metadata={'decision': 'SUPPORT', 'nli_label': 'entailment',
        'supporting': [{'nli_label': 'entailment'}], 'claim_decisions': [{'decision': 'UNSURE'}]})
    _, audit = transform(attempt('evidence', row=row, adapter='evidence_v1'),
                         enumerate_attacks(context.dependencies, spec)[1], spec)
    assert audit.before_mass == audit.after_mass == 1.
    assert audit.before_coverage == () and audit.after_coverage == ('direct_fact',)
    assert audit.effective


def test_final_test_evaluation_never_calls_optimizer_or_updates_reputation(monkeypatch):
    import app.game.policy as policies
    from app.reputation.reputation_manager import ReputationManager
    context, manifest, contract, spec = fixture()
    policy, _ = fit_policy(context, manifest, contract, spec)
    def forbidden(*args, **kwargs):
        pytest.fail('final test must not optimize or learn from development/test')
    monkeypatch.setattr(policies, 'solve_minimax', forbidden)
    monkeypatch.setattr(ReputationManager, 'update_from_ground_truth', forbidden)
    # History fixture abstains; final-test reports are directional but must not learn.
    result = evaluate_final_test(policy, context, manifest, contract, spec)
    assert result.policy_id == policy.policy_id


def test_attempt_adapter_refuses_unsupported_evidence_shape():
    context, _, _, spec = fixture(names=('evidence',))
    row = report('evidence', metadata={'decision': 'SUPPORT', 'supporting': ['bad row']})
    with pytest.raises(ValueError, match='unsupported evidence'):
        transform(attempt('evidence', row=row, adapter='evidence_v1'), enumerate_attacks(context.dependencies, spec)[2], spec)


def test_baseline_public_guard_and_contributor_parity_with_no_early_stop():
    from app.decision.decision_engine import DecisionEngine
    from app.decision.early_termination import AdaptiveEarlyTermination
    from app.game.decision_inputs import FrozenReputationSnapshot
    context, manifest, contract, spec = fixture(names=('a', 'b'))
    example = manifest.partition('development').examples[0]
    team = next(s for s in enumerate_strategies(context).strategies if s.verifiers == ('a', 'b') and s.aggregation == 'reputation_weighted')
    rows = [a.report for a in example.attempts]
    detail = DecisionEngine(threshold=contract.threshold).decide_detailed(rows, domain=example.domain,
        snapshot=FrozenReputationSnapshot.from_planning_context(context), team=team.verifiers,
        validation_id=example.validation_id)
    count = AdaptiveEarlyTermination.contributor_count(detail, rows)
    missing = set(context.plan.requirements.requirements) - set().union(*(factual_capabilities(r) for r in rows))
    expected = 'uncertain' if count < context.minimum_participant_count or missing else detail.status
    result = replay(context, team, enumerate_attacks(context.dependencies, spec)[0], spec, contract, example)
    assert result.public_status == expected and result.contributors == count
    assert result.execution_states == (('a', 'directional'), ('b', 'directional'))


def test_only_history_partition_may_train_an_isolated_manager():
    _, manifest, _, _ = fixture()
    manager = history_reputation(manifest.partition('history'), prior_alpha=1., prior_beta=1.)
    assert manager.observation_count('a', 'general') == 0
    with pytest.raises(ValueError, match='only history'):
        history_reputation(manifest.partition('development'), prior_alpha=1., prior_beta=1.)


def test_history_statistics_are_full_precision_and_must_match_captured_context():
    from tests.test_game_foundation import analysis
    from tests.test_verifier_selector import StubVerifier
    from app.selection.capabilities import CapabilityDescriptor
    from app.selection.verifier_selector import VerifierSelector
    context, manifest, contract, spec = fixture()
    manifest = change_example(manifest, 'history', attempts=(attempt(run='history'),))
    manager = history_reputation(manifest.partition('history'), prior_alpha=1., prior_beta=1.)
    selector = VerifierSelector(verifiers=[StubVerifier('a')], reputation_manager=manager,
        capabilities={'a': CapabilityDescriptor(('arithmetic',))}, difficulty_range={'hard': (1, 1)})
    a = analysis();a.difficulty = 'hard'
    captured = selector.plan(a)
    raw = unbind(context).model_dump();raw['selection_json'] = canonical_json(asdict(captured))
    fresh = PlanningContext(**raw)
    data = manifest.model_dump()
    for part in data['partitions']:
        for example in part['examples']: example['planning_category'] = fresh.compatibility_id
    manifest = DatasetManifest(**data)
    bound = bind_evaluation(fresh, manifest, contract, spec)
    assert bound.plan.reputation_statistics[0].posterior_mean == 2/3
    assert bound.plan.candidates[0].reputation == .666667
    before = bound.model_dump_json()
    construct_payoffs(bound, manifest, contract, spec)
    assert bound.model_dump_json() == before


def test_offline_imports_do_not_load_database_or_orchestrator():
    import subprocess
    import sys
    code = "import sys; import app.game.offline.evaluation; assert not any(n.startswith('app.database') or n == 'app.orchestration.validation_orchestrator' for n in sys.modules)"
    subprocess.run([sys.executable, '-c', code], check=True)


def test_legacy_compatibility_digest_is_preserved_without_offline_binding():
    import subprocess
    source = subprocess.check_output(['git', 'show', '566961f52346d490746231f9636851a6ddb403f4:app/game/models.py'], text=True)
    scope = {'__name__': 'baseline_game_models'}
    exec(compile(source, '<committed-game-models>', 'exec'), scope)
    context = make_context(names=('a',))
    data = context.model_dump();data.pop('offline_evaluation_id')
    baseline = scope['PlanningContext'](**data)
    assert baseline.compatibility_id == context.compatibility_id
