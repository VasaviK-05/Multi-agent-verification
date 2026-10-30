"""Stage 2 formula, identity and frozen-input tests; all dependencies are fixtures."""

from dataclasses import asdict, replace
import itertools
import json
import math

import pytest

from app.decision.decision_engine import DecisionDetail, DecisionEngine, log_odds_weight
from app.game.decision_inputs import FrozenReputationSnapshot
from app.game.dependencies import Dependency, DependencyRegistry
from app.game.models import PlanningContext, canonical_json
from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import ReputationManager
from app.selection.capabilities import CapabilityDescriptor
from app.selection.verifier_selector import VerifierSelector
from tests.test_game_foundation import make_context
from tests.test_verifier_selector import StubVerifier


def registry(*groups, unknown=()):
    return DependencyRegistry(version="fixture_dependencies_v1", unresolved=unknown, dependencies=[
        Dependency(resource_id=f"fixture:{i}", compromise_pathway="synthetic fixture resource failure",
                   verifiers=group) for i, group in enumerate(groups)])


def captured(counts=None, *, names=("a", "b", "c"), dependencies=None):
    manager = ReputationManager()
    state = manager.export_state()
    state["pairs"] = [dict(verifier_name=name, domain="general", successes=s, failures=f)
                      for name, (s, f) in (counts or {}).items()]
    manager.restore_state(state)
    selector = VerifierSelector(reputation_manager=manager, verifiers=[StubVerifier(n) for n in names],
        capabilities={n: CapabilityDescriptor(("arithmetic",)) for n in names})
    context = make_context(source=selector, dependencies=dependencies or registry(*((n,) for n in names)))
    return FrozenReputationSnapshot.from_planning_context(context), manager


def report(name, strength=1., *, decision=None, run=None, **metadata):
    direction = decision or ("SUPPORT" if strength >= 0 else "REJECT")
    if run is not None:
        metadata["validation_id"] = run
    return VerificationResult(verifier_name=name, score=abs(strength), passed=direction != "REJECT",
                              reasoning="test report", metadata={"decision": direction, **metadata})


def grouped(rows, snapshot, **kwargs):
    return DecisionEngine().decide_detailed(rows, aggregation="dependency_group", snapshot=snapshot, **kwargs)


def test_hand_calculated_weighted_member_and_weighted_group_formulas():
    snapshot, _ = captured({"a": (8, 0), "b": (2, 0), "c": (2, 1)}, dependencies=registry(("a", "b"), ("c",)))
    detail = grouped([report("a", .8), report("b", -.4), report("c", .6)], snapshot)
    assert detail.raw_score == pytest.approx(127/325)
    groups = {g.active_members: g for g in detail.groups}
    assert groups[("a", "b")].score == pytest.approx(22/65)
    assert groups[("a", "b")].reliability_sum == pytest.approx(1.3)
    assert groups[("a", "b")].influence == pytest.approx(.8)
    assert groups[("c",)].influence == pytest.approx(.2)
    assert detail.fallback is None and all(g.fallback is None for g in detail.groups)
    assert detail.status == "uncertain"


def test_both_zero_weight_fallbacks_use_group_means_not_a_flat_report_mean():
    snapshot, _ = captured({"b": (0, 2)}, dependencies=registry(("a", "b"), ("c",)))
    detail = grouped([report("a", 1), report("b", -.5), report("c", .5)], snapshot)
    assert detail.raw_score == .375
    assert detail.fallback == "unweighted_groups"
    assert all(g.fallback == "unweighted_members" and g.influence == 0 for g in detail.groups)
    assert {g.active_members: g.score for g in detail.groups} == {("a", "b"): .25, ("c",): .5}


def test_zero_reliability_groups_do_not_dilute_positive_influence():
    snapshot, _ = captured({"a": (0, 2), "c": (2, 0)}, dependencies=registry(("a", "b"), ("c",)))
    detail = grouped([report("a"), report("b"), report("c", -.7)], snapshot)
    assert detail.raw_score == -.7
    zero = next(g for g in detail.groups if g.active_members == ("a", "b"))
    assert zero.score == 1 and zero.influence == 0 and zero.fallback == "unweighted_members"
    assert detail.fallback is None


def test_zero_reliability_active_member_does_not_dilute_a_positive_group():
    snapshot, _ = captured({"a": (2, 0), "b": (0, 2)}, names=("a", "b"), dependencies=registry(("a", "b")))
    detail = grouped([report("a", .8), report("b", -1)], snapshot)
    assert detail.raw_score == .8
    assert detail.groups[0].active_members == ("a", "b")
    assert detail.groups[0].influence == detail.groups[0].reliability_sum == .5
    assert detail.votes[1].included and detail.votes[1].reliability_strength == 0


def test_correlated_reports_get_maximum_reliability_not_summed_group_influence():
    snapshot, _ = captured({n: (2, 0) for n in ("a", "b", "c")}, dependencies=registry(("a", "b"), ("c",)))
    detail = grouped([report("a", .9), report("b", .3), report("c", -.6)], snapshot)
    assert detail.raw_score == pytest.approx(0)
    assert [g.influence for g in detail.groups] == [.5, .5]
    assert next(g for g in detail.groups if len(g.active_members) == 2).reliability_sum == 1
    # A distinct report may change z_g; only exact duplicates have no effect.
    without_b = grouped([report("a", .9), report("c", -.6)], snapshot)
    assert without_b.raw_score != detail.raw_score


@pytest.mark.parametrize("excluded", ["absent", "abstention", "zero_confidence"])
def test_excluded_or_absent_high_reliability_cannot_increase_group_strength(excluded):
    snapshot, _ = captured({"a": (2, 1), "b": (98, 0), "c": (2, 0)}, dependencies=registry(("a", "b"), ("c",)))
    rows = [report("a"), report("c", -1)]
    if excluded != "absent":
        rows.append(report("b", 1 if excluded == "abstention" else 0,
                           decision="UNSURE" if excluded == "abstention" else "SUPPORT"))
    detail = grouped(rows, snapshot, team=("a", "b", "c"))
    assert detail.raw_score == pytest.approx(-3/7)
    group = next(g for g in detail.groups if "a" in g.active_members)
    assert group.active_members == ("a",) and group.influence == pytest.approx(.2)
    if excluded != "absent":
        vote = next(v for v in detail.votes if v.verifier_name == "b")
        assert not vote.included and vote.inclusion_reason == excluded
    else:
        assert detail.missing_reports == ("b",)


def test_below_chance_is_not_inverted_but_frozen_baseline_still_inverts():
    snapshot, _ = captured({"a": (0, 2)}, names=("a",))
    dependency = grouped([report("a", .9)], snapshot)
    baseline = DecisionEngine().decide_detailed([report("a", .9)], snapshot=snapshot)
    assert dependency.raw_score == .9 and dependency.status == "passed"
    assert dependency.votes[0].reliability_strength == 0
    assert baseline.raw_score == -.9 and baseline.status == "failed"
    assert baseline.votes[0].weight < 0


def test_connections_through_absent_bridges_and_shared_unknowns():
    deps = registry(("a", "b"), ("b", "c"), unknown=("d", "e"))
    snapshot, _ = captured(names=("a", "c", "d", "e"), dependencies=deps)
    detail = grouped([report("a", 1), report("c", -1), report("d", .8), report("e", .4)], snapshot)
    assert {g.active_members for g in detail.groups} == {("a", "c"), ("d", "e")}
    assert detail.raw_score == pytest.approx(.3)
    assert {g.group_id for g in detail.groups} == {g.group_id for g in deps.groups(("a", "c", "d", "e"))}


def test_report_and_registry_permutations_preserve_the_complete_explanation():
    deps = registry(("a", "b"), ("b", "c"))
    snapshot, _ = captured({"a": (3, 0), "b": (0, 2)}, dependencies=deps)
    reversed_registry = DependencyRegistry(version=deps.version, dependencies=list(reversed(deps.dependencies)))
    rows = [report("c", .2), report("a", .7), report("b", -.6)]
    expected = grouped(rows, snapshot).to_dict()
    for order in itertools.permutations(rows):
        assert grouped(order, snapshot, dependencies=reversed_registry).to_dict() == expected
    with pytest.raises(ValueError, match="registry differs"):
        grouped(rows, snapshot, dependencies=registry(("a",), ("b",), ("c",)))


def test_exact_duplicates_are_counted_once_and_all_metadata_is_used_for_equality():
    snapshot, _ = captured(names=("a",))
    row = report("a", .8, run="validation-1", extra={"x": [1, 2], "flag": True})
    before = row.model_dump_json()
    same = row.model_copy(deep=True)
    same.metadata = dict(reversed(list(same.metadata.items())))
    expected = grouped([row], snapshot).to_dict()
    assert grouped([row, same, row], snapshot).to_dict() == expected
    assert row.model_dump_json() == before
    changed = same.model_copy(deep=True)
    changed.metadata["extra"]["flag"] = 1  # Bool/int equality must not conceal distinct JSON payloads.
    with pytest.raises(ValueError, match="conflicting reports"):
        grouped([row, changed], snapshot)
    with pytest.raises(ValueError, match="conflicting reports"):
        grouped([row, row.model_copy(update={"reasoning": "different report"})], snapshot)


@pytest.mark.parametrize("field", ["score", "passed", "metadata"])
def test_conflicting_duplicate_zero_confidence_reports_are_not_discarded(field):
    snapshot, _ = captured(names=("a",))
    row = report("a", 0)
    update = {"score": .9} if field == "score" else {"passed": False, "metadata": {"decision": "REJECT"}} if field == "passed" else {"metadata": {"decision": "UNSURE"}}
    with pytest.raises(ValueError, match="conflicting reports"):
        grouped([row, row.model_copy(update=update)], snapshot)


@pytest.mark.parametrize("metadata", [
    {"decision": "SUPPORT", "judgments": ("support", "reject")},
    {"decision": "SUPPORT", "value": math.nan},
    {"decision": "SUPPORT", "value": {1, 2}},
    {"decision": "SUPPORT", 1: "non-string key"},
])
def test_duplicate_contract_rejects_json_coercions_and_nonfinite_metadata(metadata):
    snapshot, _ = captured(names=("a",))
    with pytest.raises(ValueError, match="native JSON"):
        grouped([report("a").model_copy(update={"metadata": metadata})], snapshot)


def test_identity_contract_infers_one_explicit_run_or_uses_a_call_local_legacy_batch():
    snapshot, _ = captured(names=("a", "b"))
    assert grouped([report("a"), report("b")], snapshot).validation_id is None
    detail = grouped([report("a", run="run-1"), report("b", run="run-1")], snapshot)
    assert detail.validation_id == "run-1" and all(v.validation_id == "run-1" for v in detail.votes)
    bound = grouped([report("a", run="run-1"), report("b")], snapshot, validation_id="run-1")
    assert bound.validation_id == "run-1"
    with pytest.raises(ValueError, match="ambiguous"):
        grouped([report("a", run="run-1"), report("b")], snapshot)
    with pytest.raises(ValueError, match="mixed"):
        grouped([report("a", run="run-1"), report("b", run="run-2")], snapshot)


@pytest.mark.parametrize("kwargs", [
    {"team": ("b",)}, {"team": ("a", "a")}, {"team": "a"},
    {"validation_id": "other"}, {"validation_id": " "},
])
def test_explicit_team_or_run_mismatches_are_rejected(kwargs):
    snapshot, _ = captured(names=("a", "b"))
    with pytest.raises(ValueError):
        grouped([report("a", run="run-1")], snapshot, **kwargs)


@pytest.mark.parametrize("rows,aggregation,status", [
    ([], "unknown", "unknown"),
    ([report("a", decision="UNSURE")], "abstentions", "uncertain"),
    ([report("a", 0)], "zero_confidence", "uncertain"),
    ([report("a", 0), report("b", decision="UNSURE")], "zero_confidence", "uncertain"),
])
@pytest.mark.parametrize("method", ["dependency_group", "reputation_weighted"])
def test_empty_abstention_and_zero_confidence_distinctions(rows, aggregation, status, method):
    snapshot, _ = captured(names=("a", "b"))
    detail = DecisionEngine().decide_detailed(rows, snapshot=snapshot, aggregation=method)
    assert (detail.aggregation, detail.status, detail.raw_score) == (aggregation, status, 0.)
    assert not detail.groups and all(not v.included for v in detail.votes)
    assert detail.aggregation_id == method


@pytest.mark.parametrize("raw,status", [
    (math.nextafter(.55, 0.), "uncertain"), (.55, "uncertain"),
    (math.nextafter(.55, 1.), "passed"), (math.nextafter(-.55, 0.), "uncertain"),
    (-.55, "uncertain"), (math.nextafter(-.55, -1.), "failed"),
])
@pytest.mark.parametrize("learned", [False, True])
def test_strict_raw_thresholds_for_group_fallback_and_weighted_formulas(raw, status, learned):
    snapshot, _ = captured({"a": (2, 0)} if learned else None, names=("a",))
    detail = grouped([report("a", raw)], snapshot)
    assert detail.raw_score == raw and detail.status == status
    assert detail.score == round(raw, 6)
    assert detail.threshold == .55
    assert detail.lower_cut == -.55 and detail.upper_cut == .55
    loose = DecisionEngine(threshold=.2).decide_detailed([report("a", .3)], snapshot=snapshot, aggregation="dependency_group")
    assert loose.status == "passed"


@pytest.mark.parametrize("aggregation", ["dependency_group", "reputation_weighted"])
def test_full_posterior_precision_no_live_reads_and_no_learning(monkeypatch, aggregation):
    snapshot, manager = captured({"a": (500001, 500000)}, names=("a", "b"))
    assert snapshot.context.plan.candidates[0].reputation == .5
    rows = [report("a", .9), report("b", -.7)]
    engine = DecisionEngine(manager)
    assert engine.decide_detailed(rows).raw_score == pytest.approx(.1)
    before = manager.export_state()
    for method in ("statistics_batch", "statistics", "get_reputation"):
        monkeypatch.setattr(manager, method, lambda *a, **kw: pytest.fail("live reputation read"))
    detail = engine.decide_detailed(rows, aggregation=aggregation, snapshot=snapshot)
    assert detail.raw_score == pytest.approx(.9)
    assert detail.votes[0].reputation == snapshot.context.plan.reputation_statistics[0].posterior_mean
    assert detail.reputation_snapshot_id == snapshot.snapshot_id
    assert manager.export_state() == before


@pytest.mark.parametrize("aggregation", ["dependency_group", "reputation_weighted"])
def test_live_updates_do_not_change_frozen_decisions_or_snapshot(aggregation):
    snapshot, manager = captured({"a": (2, 0)}, names=("a",))
    engine = DecisionEngine(manager)
    before_snapshot = snapshot.model_dump_json()
    first = engine.decide_detailed([report("a", .9)], snapshot=snapshot, aggregation=aggregation)
    for _ in range(10):
        manager.update_reputation("a", "general", False)
    second = engine.decide_detailed([report("a", .9)], snapshot=snapshot, aggregation=aggregation)
    assert first == second and snapshot.model_dump_json() == before_snapshot
    assert engine.decide_detailed([report("a", .9)]).raw_score == -.9


@pytest.mark.parametrize("aggregation", ["dependency_group", "reputation_weighted"])
def test_snapshot_requires_matching_domain_complete_participant_statistics_and_identifier(aggregation):
    snapshot, _ = captured(names=("a",))
    engine = DecisionEngine()
    with pytest.raises(ValueError, match="domain"):
        engine.decide_detailed([], snapshot=snapshot, aggregation=aggregation, domain="medical")
    with pytest.raises(ValueError, match="missing reputation"):
        engine.decide_detailed([report("unknown")], snapshot=snapshot, aggregation=aggregation)
    with pytest.raises(ValueError, match="identifier"):
        engine.decide_detailed([], snapshot=snapshot.model_copy(update={"snapshot_id": "forged"}), aggregation=aggregation)
    plan = replace(snapshot.context.plan, reputation_statistics=())
    invalid_context = snapshot.context.model_copy(update={"selection_json": canonical_json(asdict(plan))})
    with pytest.raises(ValueError, match="complete captured reputation"):
        engine.decide_detailed([], snapshot=snapshot.model_copy(update={"context": invalid_context}), aggregation=aggregation)


@pytest.mark.parametrize("aggregation", ["dependency_group", "reputation_weighted"])
def test_snapshot_rejects_inconsistent_statistics_and_aggregation_versions(aggregation):
    snapshot, _ = captured(names=("a",))
    plan = snapshot.context.plan
    invalid = replace(plan, reputation_statistics=(replace(plan.reputation_statistics[0], observation_count=-1),))
    invalid_context = snapshot.context.model_copy(update={"selection_json": canonical_json(asdict(invalid))})
    with pytest.raises(ValueError, match="statistics"):
        DecisionEngine().decide_detailed([report("a")], snapshot=snapshot.model_copy(update={"context": invalid_context}), aggregation=aggregation)
    data = snapshot.context.model_dump()
    data["aggregation_versions"] = [(name, "future" if name == aggregation else version)
                                    for name, version in data["aggregation_versions"]]
    future = FrozenReputationSnapshot.from_planning_context(PlanningContext(**data))
    with pytest.raises(ValueError, match="version is incompatible"):
        DecisionEngine().decide_detailed([], snapshot=future, aggregation=aggregation)


def test_dependency_method_requires_a_snapshot_even_for_no_reports():
    with pytest.raises(ValueError, match="FrozenReputationSnapshot"):
        DecisionEngine().decide_detailed([], aggregation="dependency_group")


def test_baseline_shape_rounding_duplicate_policy_and_identity_opt_in_are_preserved():
    engine = DecisionEngine()
    row = report("a", .8, run="annotated-run")
    detail = engine.decide_detailed([row])
    assert type(detail) is DecisionDetail
    assert set(asdict(detail)) == {"domain", "status", "raw_score", "score", "threshold", "aggregation", "votes"}
    with pytest.raises(ValueError, match="duplicate verifier name"):
        engine.decide_detailed([row, row])
    snapshot, _ = captured(names=("a",))
    with pytest.raises(ValueError, match="duplicate verifier name"):
        engine.decide_detailed([row, row], snapshot=snapshot)
    with pytest.raises(ValueError, match="validation_id differs"):
        engine.decide_detailed([row], validation_id="other-run")
    opted = engine.decide_detailed([row], validation_id="annotated-run", team=("a",))
    assert opted.to_dict()["validation_id"] == "annotated-run"
    assert engine.decide([row], snapshot=snapshot) == ("passed", .8)
    assert engine.decide([row], snapshot=snapshot, aggregation="dependency_group") == ("passed", .8)


def test_frozen_log_odds_hand_formula_uses_unrounded_means():
    snapshot, _ = captured({"a": (8, 0), "b": (0, 2)}, names=("a", "b"))
    detail = DecisionEngine().decide_detailed([report("a", .8), report("b", -.4)], snapshot=snapshot)
    means = {s.verifier_name: s.posterior_mean for s in snapshot.context.plan.reputation_statistics}
    wa, wb = log_odds_weight(means["a"]), log_odds_weight(means["b"])
    assert detail.raw_score == math.fsum((wa * .8, wb * -.4)) / math.fsum((abs(wa), abs(wb)))
    assert detail.aggregation_id == "reputation_weighted" and detail.aggregation_version == "log_odds_v1"


@pytest.mark.parametrize("row,mass,excluded", [
    (VerificationResult(verifier_name="rule", score=0, passed=False, metadata={"rule": "arithmetic_addition"}), -1., None),
    (VerificationResult(verifier_name="rule", score=1, passed=True, metadata={"rule": "email_regex"}), None, "abstention"),
    (VerificationResult(verifier_name="evidence", score=.8, passed=False, metadata={"nli_label": "neutral"}), None, "abstention"),
    (VerificationResult(verifier_name="confidence", score=.5, passed=True, metadata={"judgments": ["support", "reject"]}), None, "abstention"),
    (VerificationResult(verifier_name="semantic", score=0, passed=False, reasoning="No reference context provided"), None, "abstention"),
    (VerificationResult(verifier_name="custom", score=0, passed=True), 0., "zero_confidence"),
])
def test_existing_normalization_is_reused_for_rules_metadata_and_abstentions(row, mass, excluded):
    snapshot, _ = captured(names=(row.verifier_name,))
    detail = grouped([row], snapshot)
    assert detail.votes[0].normalized_strength == mass
    assert detail.votes[0].inclusion_reason == (excluded or "included")
    assert detail.raw_score == (mass or 0)


def test_explanations_are_detached_serializable_and_do_not_claim_coverage():
    snapshot, _ = captured(names=("a", "b"))
    detail = grouped([report("a", .8)], snapshot, validation_id="test-run", team=("a", "b"))
    first = detail.to_dict()
    json.dumps(first, allow_nan=False)
    first["votes"][0]["reputation"] = 1
    first["groups"][0]["active_members"].clear()
    assert detail.to_dict()["votes"][0]["reputation"] == .5
    assert detail.groups[0].active_members == ("a",)
    assert detail.missing_reports == ("b",) and detail.status == "passed"
    assert "coverage" not in detail.to_dict()


@pytest.mark.parametrize("score", [True, math.nan, -.1, 1.1])
def test_dependency_entry_point_validates_all_scores_before_exclusion(score):
    snapshot, _ = captured(names=("a",))
    invalid = report("a", decision="UNSURE").model_copy(update={"score": score})
    with pytest.raises((TypeError, ValueError), match="score"):
        grouped([invalid], snapshot)


def test_cyclic_metadata_is_explicitly_rejected_without_mutation():
    snapshot, _ = captured(names=("a",))
    metadata = {"decision": "SUPPORT"}
    metadata["cycle"] = metadata
    row = report("a").model_copy(update={"metadata": metadata})
    with pytest.raises(ValueError, match="acyclic"):
        grouped([row], snapshot)
    assert metadata["cycle"] is metadata
