"""Isolated tests for VerifierSelector."""

import math

import pytest

from app.analysis.question_analyzer import QuestionAnalysis, QuestionAnalyzer
from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import ReputationManager
from app.selection.verifier_selector import (
    DEFAULT_DIFFICULTY_RANGE,
    DEFAULT_VERIFIER_PROFILES,
    VerifierSelector,
    band_position,
    suitability_by_verifier,
    target_verifier_count,
)
from app.verifiers.base_verifier import BaseVerifier


class StubVerifier(BaseVerifier):
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def verify(self, question: str, answer: str, context: str | None = None) -> VerificationResult:
        return VerificationResult(
            verifier_name=self._name,
            score=0.5,
            passed=True,
            reasoning="stub",
        )


def _stubs() -> list[StubVerifier]:
    return [StubVerifier(name) for name in ("semantic", "evidence", "rule", "confidence")]


def test_select_returns_base_verifiers():
    # Two default easy candidates can include a model-backed verifier.
    # Inject implementations here to keep this selection test deterministic.
    selector = VerifierSelector(verifiers=_stubs())
    selected = selector.select(
        QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.1)
    )
    assert selected
    assert all(isinstance(v, BaseVerifier) for v in selected)


def test_hard_selects_more_than_easy():
    selector = VerifierSelector(verifiers=_stubs())
    easy = selector.select(
        QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.1)
    )
    hard = selector.select(
        QuestionAnalysis(domain="general", difficulty="hard", difficulty_score=0.9)
    )
    assert len(easy) == DEFAULT_DIFFICULTY_RANGE["easy"][0]
    assert len(hard) == DEFAULT_DIFFICULTY_RANGE["hard"][1]
    assert len(hard) > len(easy)


def test_configured_range_endpoints_are_reachable():
    selector = VerifierSelector(verifiers=[])
    assert selector.target_count(QuestionAnalysis("general", "easy", 0.0)) == 2
    assert selector.target_count(QuestionAnalysis("general", "easy", 0.34)) == 2
    assert selector.target_count(QuestionAnalysis("general", "medium", 0.35)) == 2
    assert selector.target_count(QuestionAnalysis("general", "medium", 0.64)) == 3
    assert selector.target_count(QuestionAnalysis("general", "hard", 0.65)) == 3
    assert selector.target_count(QuestionAnalysis("general", "hard", 1.0)) == 4


def test_cost_and_latency_reduce_utility_at_equal_reputation():
    selector = VerifierSelector(verifiers=[])
    assert selector.utility("rule", "general") > selector.utility("evidence", "general")


def test_explicit_estimates_can_change_the_first_verifier():
    profiles = {
        "semantic": {"cost": 1.0, "latency": 1.0},
        "evidence": {"cost": 0.0, "latency": 0.0},
        "rule": {"cost": 1.0, "latency": 1.0},
        "confidence": {"cost": 1.0, "latency": 1.0},
    }
    selector = VerifierSelector(verifiers=_stubs(), verifier_profiles=profiles)
    selected = selector.select(QuestionAnalysis("general", "easy", 0.1))
    assert selected[0].name == "evidence"


def test_domain_reputation_outranks_a_cheaper_verifier():
    manager = ReputationManager()
    for _ in range(3):
        manager.update_reputation("evidence", "medical", True)
    selector = VerifierSelector(reputation_manager=manager, verifiers=_stubs())
    medical = selector.select(QuestionAnalysis("medical", "easy", 0.1))
    general = selector.select(QuestionAnalysis("general", "easy", 0.1))
    assert medical[0].name == "evidence"
    assert general[0].name == "rule"


def test_higher_reputation_ranks_first():
    manager = ReputationManager()
    manager.update_reputation("rule", "general", True)
    manager.update_reputation("rule", "general", True)
    manager.update_reputation("evidence", "general", False)
    selector = VerifierSelector(reputation_manager=manager, verifiers=_stubs())
    selected = selector.select(
        QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.1)
    )
    assert selected[0].name == "rule"


def _names(selector: VerifierSelector, analysis: QuestionAnalysis) -> list[str]:
    return [verifier.name for verifier in selector.iter_ranked(analysis)]


def test_empty_verification_types_keep_the_resource_ranking():
    selector = VerifierSelector(verifiers=_stubs())
    analysis = QuestionAnalysis("general", "easy", 0.1, verification_types=[])
    assert _names(selector, analysis) == ["rule", "semantic", "evidence", "confidence"]
    assert selector.ranking_utility("rule", analysis) == selector.utility("rule", "general")
    explained = selector.explain_ranking(analysis)
    assert all(row.suitability == 0.0 and row.suitability_contribution == 0.0 for row in explained)


def test_mapped_type_can_outrank_a_cheaper_verifier():
    selector = VerifierSelector(verifiers=_stubs())
    analysis = QuestionAnalysis(
        "general",
        "easy",
        0.1,
        verification_types=["evidence_retrieval"],
    )
    assert _names(selector, analysis)[0] == "evidence"
    row = next(item for item in selector.explain_ranking(analysis) if item.verifier_name == "evidence")
    assert row.suitability == 1.0
    assert row.utility == pytest.approx(row.reputation - row.resource_penalty + row.suitability_contribution)
    assert row.utility == pytest.approx(selector.ranking_utility("evidence", analysis))
    assert selector.utility("evidence", "general") == pytest.approx(row.reputation - row.resource_penalty)


def test_combined_types_split_the_bonus_and_duplicates_do_not():
    selector = VerifierSelector(verifiers=_stubs())
    combined = QuestionAnalysis(
        "general",
        "easy",
        0.1,
        verification_types=["arithmetic", "evidence_retrieval"],
    )
    repeated = QuestionAnalysis(
        "general",
        "easy",
        0.1,
        verification_types=["evidence_retrieval", "evidence_retrieval"],
    )
    single = QuestionAnalysis("general", "easy", 0.1, verification_types=["evidence_retrieval"])
    combined_rows = {row.verifier_name: row for row in selector.explain_ranking(combined)}
    assert combined_rows["rule"].suitability == pytest.approx(0.5)
    assert combined_rows["evidence"].suitability == pytest.approx(0.5)
    assert _names(selector, combined)[0] == "rule"
    assert _names(selector, single)[0] == "evidence"
    repeated_rows = {row.verifier_name: row for row in selector.explain_ranking(repeated)}
    assert repeated_rows["evidence"].suitability == pytest.approx(1.0)
    assert _names(selector, repeated) == _names(selector, single)


def test_unknown_types_match_nobody_and_dilute_known_types():
    selector = VerifierSelector(verifiers=_stubs())
    unknown = QuestionAnalysis("general", "easy", 0.1, verification_types=["not_a_type", None])
    empty = QuestionAnalysis("general", "easy", 0.1)
    assert _names(selector, unknown) == _names(selector, empty)
    diluted = QuestionAnalysis(
        "general",
        "easy",
        0.1,
        verification_types=["arithmetic", "not_a_type"],
    )
    rows = {row.verifier_name: row for row in selector.explain_ranking(diluted)}
    assert rows["rule"].suitability == pytest.approx(0.5)
    assert rows["semantic"].suitability == 0.0
    scores = suitability_by_verifier(["direct_fact", "direct_fact", "mystery"], selector.type_mapping)
    assert scores["evidence"] == pytest.approx(0.5)


def test_learned_reputation_can_outrank_a_type_hint_in_the_same_domain():
    manager = ReputationManager()
    manager.update_reputation("evidence", "medical", False)
    selector = VerifierSelector(reputation_manager=manager, verifiers=_stubs())
    medical = QuestionAnalysis(
        "medical",
        "easy",
        0.1,
        verification_types=["direct_fact"],
        domain_candidates=["medical", "technical"],
        domain_status="mixed",
    )
    general = QuestionAnalysis("general", "easy", 0.1, verification_types=["direct_fact"])
    assert _names(selector, medical)[0] == "rule"
    assert _names(selector, general)[0] == "evidence"
    assert selector.explain_ranking(medical)[0].reputation == manager.get_reputation("rule", "medical")


def test_equal_utilities_keep_registration_order_and_empty_registry_yields_nothing():
    profiles = {
        name: {"cost": 0.5, "latency": 0.5}
        for name in ("semantic", "evidence", "rule", "confidence")
    }
    stubs = _stubs()
    selector = VerifierSelector(verifiers=stubs, verifier_profiles=profiles, lambda_suitability=0)
    analysis = QuestionAnalysis("general", "easy", 0.1, verification_types=["arithmetic"])
    assert _names(selector, analysis) == ["semantic", "evidence", "rule", "confidence"]
    empty = VerifierSelector(verifiers=[])
    assert list(empty.iter_ranked(analysis)) == []
    assert empty.explain_ranking(analysis) == []
    assert empty.select(analysis) == []


def test_explanation_matches_ranking_without_constructing_default_verifiers():
    selector = VerifierSelector()
    analysis = QuestionAnalysis("general", "easy", 0.0, verification_types=["semantic_comparison"])
    explained = selector.explain_ranking(analysis)
    assert selector._cache == {}
    assert [row.verifier_name for row in explained] == [
        "semantic",
        "rule",
        "evidence",
        "confidence",
    ]
    stubbed = VerifierSelector(verifiers=_stubs())
    assert [row.verifier_name for row in stubbed.explain_ranking(analysis)] == _names(stubbed, analysis)
    iterator = selector.iter_ranked(QuestionAnalysis("general", "easy", 0.0))
    first = next(iterator)
    assert first.name == "rule"
    assert list(selector._cache) == ["rule"]
    assert next(selector.iter_ranked(QuestionAnalysis("general", "easy", 0.0))) is first


def test_suitability_configuration_is_validated():
    with pytest.raises(ValueError, match="lambda_suitability"):
        VerifierSelector(verifiers=[], lambda_suitability=math.nan)
    with pytest.raises(ValueError, match="lambda_suitability"):
        VerifierSelector(verifiers=[], lambda_suitability=math.inf)
    with pytest.raises(ValueError, match="lambda_suitability"):
        VerifierSelector(verifiers=[], lambda_suitability=-0.01)
    with pytest.raises(ValueError, match="lambda_suitability"):
        VerifierSelector(verifiers=[], lambda_suitability=True)
    VerifierSelector(verifiers=[], lambda_suitability=0)
    VerifierSelector(verifiers=[], lambda_suitability=1)
    with pytest.raises(ValueError, match="type_mapping"):
        VerifierSelector(verifiers=[], type_mapping={" ": "rule"})
    with pytest.raises(ValueError, match="type_mapping"):
        VerifierSelector(verifiers=[], type_mapping={"arithmetic": ""})
    with pytest.raises(ValueError, match="type_mapping"):
        VerifierSelector(verifiers=[], type_mapping=["arithmetic"])  # type: ignore[arg-type]
    custom = VerifierSelector(
        verifiers=_stubs(),
        type_mapping={"arithmetic": "semantic"},
    )
    analysis = QuestionAnalysis("general", "easy", 0.1, verification_types=["arithmetic"])
    assert _names(custom, analysis)[0] == "semantic"


@pytest.mark.parametrize("weight", ["lambda_cost", "lambda_latency"])
@pytest.mark.parametrize("value", [True, None, "0.5", -0.1, 1.1, math.nan, math.inf, -math.inf])
def test_invalid_resource_weights_are_rejected(weight, value):
    with pytest.raises(ValueError, match=weight):
        VerifierSelector(verifiers=[], **{weight: value})


@pytest.mark.parametrize("field", ["cost", "latency"])
@pytest.mark.parametrize("value", [True, None, "0.5", -0.1, 1.1, math.nan, math.inf])
def test_invalid_profile_values_are_rejected(field, value):
    profile = {"cost": 0.5, "latency": 0.5, field: value}
    with pytest.raises(ValueError, match=field):
        VerifierSelector(verifiers=[], verifier_profiles={"rule": profile})


@pytest.mark.parametrize("profile", [{}, {"cost": 0.2}, {"latency": 0.2}, None])
def test_missing_profile_fields_have_clear_errors(profile):
    with pytest.raises(ValueError, match="requires cost and latency"):
        VerifierSelector(verifiers=[], verifier_profiles={"rule": profile})


@pytest.mark.parametrize("pair", [(0, 1), (-1, 2), (2, 1), (True, 2), (1, False),
                                  (1.0, 2), (1, 2.0), (1,), (1, 2, 3), "12", None])
def test_invalid_difficulty_ranges_are_rejected(pair):
    with pytest.raises(ValueError, match="positive integer pairs"):
        VerifierSelector(verifiers=[], difficulty_range={"easy": pair})
    with pytest.raises(ValueError, match="difficulty_range"):
        target_verifier_count("easy", 0.1, {"easy": pair})


@pytest.mark.parametrize("option", ["verifier_profiles", "difficulty_range"])
def test_configuration_requires_mappings(option):
    with pytest.raises(ValueError, match=option):
        VerifierSelector(verifiers=[], **{option: []})
    with pytest.raises(ValueError, match="difficulty_range"):
        VerifierSelector(verifiers=[], difficulty_range={})


@pytest.mark.parametrize("score", [None, "0.1", True, math.nan, math.inf, -math.inf])
def test_invalid_scores_fail_in_count_and_ranking_entry_points(score):
    selector = VerifierSelector(verifiers=[])
    analysis = QuestionAnalysis("general", "easy", score)
    operations = [
        lambda: band_position("easy", score),
        lambda: target_verifier_count("easy", score),
        lambda: selector.minimum_count(analysis),
        lambda: selector.target_count(analysis),
        lambda: selector.explain_ranking(analysis),
        lambda: list(selector.iter_ranked(analysis)),
        lambda: selector.select(analysis),
    ]
    for operation in operations:
        with pytest.raises(ValueError, match="difficulty_score must be a finite number"):
            operation()


@pytest.mark.parametrize("name", ["", "  ", " rule", "rule ", None, 1, True])
def test_invalid_registered_names_are_rejected(name):
    with pytest.raises(ValueError, match="verifier name"):
        VerifierSelector(verifiers=[StubVerifier(name)])


def test_duplicate_and_invalid_registrations_are_rejected():
    with pytest.raises(ValueError, match="duplicate registered"):
        VerifierSelector(verifiers=[StubVerifier("rule"), StubVerifier("rule")])
    with pytest.raises(ValueError, match="BaseVerifier"):
        VerifierSelector(verifiers=[object()])
    selector = VerifierSelector(verifiers=[StubVerifier("custom")])
    assert _names(selector, QuestionAnalysis("general", "easy", 0.1)) == ["custom"]


def test_caller_configuration_mutations_do_not_change_selection():
    profiles = {name: {"cost": 0.5, "latency": 0.5} for name in DEFAULT_VERIFIER_PROFILES}
    ranges = {"easy": [1, 1], "medium": [2, 3], "hard": [3, 4]}
    mapping = {"direct_fact": "evidence"}
    verifiers = _stubs()
    selector = VerifierSelector(verifiers=verifiers, verifier_profiles=profiles,
                                difficulty_range=ranges, type_mapping=mapping)
    analysis = QuestionAnalysis("general", "easy", 0.1, verification_types=["direct_fact"])
    original = selector.explain_ranking(analysis)
    profiles["evidence"]["cost"] = 1
    profiles.clear()
    ranges["easy"][0] = 4
    ranges.clear()
    mapping["direct_fact"] = "rule"
    verifiers.clear()
    assert selector.explain_ranking(analysis) == original
    assert selector.minimum_count(analysis) == 1
    assert selector.target_count(analysis) == 1
    assert [v.name for v in selector.select(analysis)] == ["evidence"]


def test_default_and_custom_counts_preserve_finite_score_clamping():
    default = VerifierSelector(verifiers=_stubs())
    custom = VerifierSelector(verifiers=_stubs(), difficulty_range={"easy": (1, 2)})
    for score in (-10, 0, 0.1, 0.34, 10):
        analysis = QuestionAnalysis("general", "easy", score)
        assert default.minimum_count(analysis) == 2
        assert default.target_count(analysis) == 2
        assert len(default.select(analysis)) == 2
    assert custom.target_count(QuestionAnalysis("general", "easy", -10)) == 1
    assert custom.target_count(QuestionAnalysis("general", "easy", 10)) == 2
    assert band_position("hard", -10) == 0
    assert band_position("hard", 10) == 1


def test_confidence_estimates_and_custom_overrides():
    assert DEFAULT_VERIFIER_PROFILES["confidence"] == {"cost": 0.9, "latency": 1.0}
    selector = VerifierSelector(verifiers=_stubs(), verifier_profiles={
        name: {"cost": 0, "latency": 0} if name == "confidence" else {"cost": 1, "latency": 1}
        for name in DEFAULT_VERIFIER_PROFILES
    })
    assert _names(selector, QuestionAnalysis("general", "easy", 0.1))[0] == "confidence"
    for weight in (0, 1):
        VerifierSelector(verifiers=[], lambda_cost=weight, lambda_latency=weight,
                         verifier_profiles={"custom": {"cost": weight, "latency": weight}})


@pytest.mark.parametrize("question,hint,order", [
    ("Who wrote Hamlet?", "direct_fact", ["evidence", "rule", "semantic", "confidence"]),
    ("What is 2 + 2?", "arithmetic", ["rule", "semantic", "evidence", "confidence"]),
])
def test_analyzer_hints_reach_selector_without_forcing_a_universal_order(question, hint, order):
    analysis = QuestionAnalyzer(mode="heuristic", environ={}).analyze(question)
    selector = VerifierSelector(verifiers=_stubs())
    assert analysis.verification_types == [hint]
    assert _names(selector, analysis) == order
    assert selector.target_count(analysis) == 2
    assert [v.name for v in selector.select(analysis)] == order[:2]


def test_low_reputation_evidence_remains_reachable_beyond_initial_target():
    manager = ReputationManager()
    for _ in range(3):
        manager.update_reputation("evidence", "general", False)
    selector = VerifierSelector(reputation_manager=manager, verifiers=_stubs())
    analysis = QuestionAnalyzer(mode="heuristic", environ={}).analyze("Who wrote Hamlet?")
    assert [v.name for v in selector.select(analysis)] == ["rule", "semantic"]
    assert _names(selector, analysis) == ["rule", "semantic", "confidence", "evidence"]
    # Iterator reachability is not an assertion that orchestration will run it.


# New planning API: legacy wrappers above intentionally retain utility top-k.
from dataclasses import FrozenInstanceError
from app.analysis.research_context import build_research_context
from app.selection.capabilities import CapabilityDescriptor


def _analysis(*requirements, typed=True):
    analysis = QuestionAnalysis("general", "easy", .1, verification_types=list(requirements))
    if typed:
        analysis.research_context = build_research_context(analysis)
    return analysis


def test_plan_prefers_lower_utility_specialist_and_uses_one_snapshot():
    class SnapshotOnly(ReputationManager):
        calls = 0

        def statistics_batch(self, pairs):
            self.calls += 1
            snapshot = super().statistics_batch(pairs)
            self.update_reputation("specialist", "general", True)
            return snapshot

        def get_reputation(self, *args):
            raise AssertionError("plan must use only the captured batch")

    manager = SnapshotOnly()
    for _ in range(3):
        manager.update_reputation("specialist", "general", False)
    selector = VerifierSelector(verifiers=[StubVerifier(n) for n in ("cheap", "other", "specialist")],
        reputation_manager=manager, capabilities={"specialist": CapabilityDescriptor(("direct_fact",))})
    plan = selector.plan(_analysis("direct_fact"))
    assert plan.initial_selected == ("specialist", "cheap")
    assert plan.fallback == ("other",)
    row = plan.candidates[-1]
    assert row.reputation == .2 and row.observation_count == 3 and not row.cold_start
    assert row.utility == pytest.approx(row.reputation - row.resource_penalty + row.suitability_contribution)
    assert manager.calls == 1
    saved = plan.to_dict()
    manager.update_reputation("specialist", "general", False)
    selector.verifier_profiles.clear()
    assert plan.to_dict() == saved
    saved["candidates"][0]["reputation"] = 999
    assert plan.candidates[0].reputation == .5
    with pytest.raises(FrozenInstanceError):
        plan.candidates[-1].reputation = 1


def test_plan_complementarity_soft_target_overflow_and_no_duplicates():
    requirements = ("direct_fact", "arithmetic", "consistency")
    names = ("a", "b", "c", "duplicate", "generic")
    selector = VerifierSelector(verifiers=[StubVerifier(n) for n in names], capabilities={
        "a": CapabilityDescriptor(("direct_fact",)),
        "b": CapabilityDescriptor(("arithmetic",)),
        "c": CapabilityDescriptor(("consistency",)),
        "duplicate": CapabilityDescriptor(("direct_fact",)),
    }, lambda_cost=0, lambda_latency=0, lambda_suitability=0)
    plan = selector.plan(_analysis(*requirements))
    assert plan.target_count == 2
    assert plan.initial_selected == ("a", "b", "c")
    assert plan.expected_uncovered == ()
    assert plan.fallback == ("duplicate", "generic")
    assert len(set(plan.initial_selected + plan.fallback)) == 5


def test_plan_uses_weighted_marginal_coverage_then_utility_then_registration():
    analysis = _analysis("direct_fact", "arithmetic", "consistency")
    analysis.research_context.requirement_weights.update(direct_fact=.8, arithmetic=.1, consistency=.1)
    selector = VerifierSelector(verifiers=[StubVerifier(n) for n in ("multi", "fact", "tie")],
        capabilities={"multi": CapabilityDescriptor(("arithmetic", "consistency")),
                      "fact": CapabilityDescriptor(("direct_fact",)),
                      "tie": CapabilityDescriptor(("direct_fact",))},
        lambda_cost=0, lambda_latency=0, lambda_suitability=0)
    assert selector.plan(analysis).initial_selected == ("fact", "multi")
    analysis.research_context.requirement_weights.update(direct_fact=.2, arithmetic=.4, consistency=.4)
    assert selector.plan(analysis).initial_selected == ("multi", "fact")
    selector.reputation_manager.update_reputation("tie", "general", True)
    assert selector.plan(analysis).initial_selected == ("multi", "tie")


def test_plan_context_precedence_legacy_fallback_and_observable_unknowns():
    selector = VerifierSelector(verifiers=_stubs(), capabilities={
        "rule": CapabilityDescriptor(("arithmetic",)), "evidence": CapabilityDescriptor(("direct_fact",))})
    analysis = _analysis("arithmetic")
    analysis.verification_types = ["direct_fact", "mystery"]
    plan = selector.plan(analysis)
    assert plan.requirements.source == "research_context"
    assert plan.requirements.requirements == ("arithmetic",)
    assert plan.requirements.weights == (("arithmetic", 1),)
    assert plan.requirements.disagreements
    assert plan.requirements.legacy_unrecognized == ("mystery",)
    assert plan.initial_selected[0] == "rule"
    analysis.research_context = None
    legacy = selector.plan(analysis)
    assert legacy.requirements.source == "legacy"
    assert legacy.requirements.unsupported == ("mystery",)
    assert legacy.expected_uncovered == ("mystery",)
    assert legacy.initial_selected[0] == "evidence"


@pytest.mark.parametrize("mutation", ["wrong_type", "version", "weights", "missing_weight", "known"])
def test_invalid_present_context_never_falls_back_to_legacy(mutation):
    analysis = _analysis("arithmetic")
    if mutation == "wrong_type":
        analysis.research_context = {"verification_requirements": ["direct_fact"]}
    elif mutation == "version":
        analysis.research_context.context_version = "future"
    elif mutation == "weights":
        analysis.research_context.requirement_weights["arithmetic"] = float("nan")
    elif mutation == "missing_weight":
        analysis.research_context.requirement_weights = {}
    else:
        analysis.research_context.requirements_known = False
    plan = VerifierSelector(verifiers=_stubs()).plan(analysis)
    assert plan.requirements.source == "research_context"
    assert plan.requirements.status == "invalid" and plan.requirements.errors
    assert not plan.requirements.requirements_known and plan.coverage_status == "unknown"


def test_plan_builtin_limits_and_unknown_injected_capabilities_no_constructors(monkeypatch):
    import app.selection.verifier_selector as module
    monkeypatch.setattr(module, "_build_default_verifier", lambda name: pytest.fail("constructor probe"))
    selector = VerifierSelector()
    plan = selector.plan(_analysis("logical_rule", "arithmetic", "direct_fact", "consistency"))
    assert "logical_rule" in plan.expected_uncovered
    assert dict(plan.exclusions)["semantic"] == "reference context is absent"
    assert selector._cache == {}
    assert {row.prerequisite_status for row in plan.candidates if row.verifier_name != "semantic"} == {"unknown"}
    injected = VerifierSelector(verifiers=_stubs()).plan(_analysis("arithmetic", "direct_fact"))
    assert injected.expected_covered == ()
    assert all(row.capability_source == "unknown" and row.expected_capabilities == () for row in injected.candidates)


@pytest.mark.parametrize("context,excluded", [(None, True), ("  ", True),
    ("support,reject", True), ("A reference passage.", False)])
def test_plan_observable_reference_prerequisite(context, excluded):
    selector = VerifierSelector(verifiers=[StubVerifier("custom")], capabilities={
        "custom": CapabilityDescriptor(("semantic_comparison",), requires_reference=True)})
    plan = selector.plan(_analysis("semantic_comparison"), context)
    assert plan.candidates[0].eligible is not excluded
    assert bool(plan.exclusions) is excluded
    assert plan.expected_uncovered == (("semantic_comparison",) if excluded else ())


def test_plan_explicit_unavailable_and_unknown_requirements():
    selector = VerifierSelector(verifiers=_stubs(), capabilities={
        "rule": CapabilityDescriptor(("arithmetic",), readiness="unavailable", unavailable_reason="disabled")})
    known = selector.plan(_analysis("arithmetic"))
    assert known.expected_uncovered == ("arithmetic",)
    assert "rule" not in known.initial_selected + known.fallback
    unknown = selector.plan(_analysis())
    assert unknown.coverage_status == "unknown" and not unknown.requirements.requirements_known
    assert unknown.initial_selected == ("semantic", "evidence")
    assert unknown.fallback == ("confidence",)


def test_plan_zero_weight_requirement_still_requires_coverage():
    analysis = _analysis("direct_fact", "arithmetic")
    analysis.research_context.requirement_weights.update(direct_fact=1, arithmetic=0)
    selector = VerifierSelector(verifiers=[StubVerifier("fact"), StubVerifier("math")], capabilities={
        "fact": CapabilityDescriptor(("direct_fact",)), "math": CapabilityDescriptor(("arithmetic",))})
    assert selector.plan(analysis).initial_selected == ("fact", "math")


def test_plan_compatibility_wrapper_still_returns_legacy_top_k():
    selector = VerifierSelector(verifiers=[StubVerifier(n) for n in ("a", "b", "specialist")],
        capabilities={"specialist": CapabilityDescriptor(("arithmetic",))})
    analysis = _analysis("arithmetic")
    assert selector.plan(analysis).initial_selected[0] == "specialist"
    assert [v.name for v in selector.select(analysis)] == ["a", "b"]
    assert [v.name for v in selector.iter_ranked(analysis)] == ["a", "b", "specialist"]


@pytest.mark.parametrize("kwargs", [{"expected_capabilities": "arithmetic"},
    {"readiness": "maybe"}, {"readiness": "unavailable"}, {"requires_reference": 1}])
def test_capability_configuration_rejects_malformed_descriptors(kwargs):
    with pytest.raises(ValueError):
        CapabilityDescriptor(**kwargs)


def test_explicit_descriptor_copies_caller_sequences_and_configuration():
    labels = ["arithmetic"]
    descriptor = CapabilityDescriptor(labels)
    config = {"custom": descriptor}
    selector = VerifierSelector(verifiers=[StubVerifier("custom")], capabilities=config)
    labels.clear()
    config.clear()
    assert selector.plan(_analysis("arithmetic")).expected_covered == ("arithmetic",)


@pytest.mark.parametrize("omitted", [
    {"arithmetic": .5},
    {"arithmetic": .2, "consistency": .3},
])
def test_plan_p2_rejects_positive_weights_for_omitted_requirements(omitted):
    import json
    analysis = _analysis("direct_fact")
    analysis.research_context.requirement_weights.update(direct_fact=.5, **omitted)
    # Recognized legacy hints cannot rescue or silently expand invalid context.
    analysis.verification_types = ["direct_fact", *omitted]
    plan = VerifierSelector(verifiers=_stubs()).plan(analysis)
    assert plan.requirements.source == "research_context"
    assert plan.requirements.status == "invalid"
    assert plan.requirements.requirements == ("direct_fact",)
    assert plan.requirements.weights == () and not plan.requirements.requirements_known
    assert plan.requirements.errors == ("positive requirement weights assigned to omitted requirements",)
    assert plan.requirements.weight_discrepancies == tuple(sorted(omitted.items()))
    assert plan.requirements.disagreements
    assert plan.expected_covered == () and plan.coverage_status == "unknown"
    audit = json.loads(json.dumps(plan.to_dict(), allow_nan=False))
    assert dict(audit["requirements"]["weight_discrepancies"]) == omitted


def test_plan_p2_matching_weights_and_extra_zero_entries_remain_valid():
    analysis = _analysis("direct_fact", "arithmetic")
    analysis.research_context.requirement_weights.update(direct_fact=.25, arithmetic=.75)
    # Current schema emits zero entries outside the requirement list. Extra
    # zero entries do not become obligations, including an unrecognized key.
    analysis.research_context.requirement_weights["future_label"] = 0
    plan = VerifierSelector(verifiers=_stubs()).plan(analysis)
    assert plan.requirements.status == "known" and plan.requirements.errors == ()
    assert plan.requirements.weights == (("direct_fact", .25), ("arithmetic", .75))
    assert plan.requirements.weight_discrepancies == ()
    assert plan.requirements.unsupported == ()
    untouched = VerifierSelector(verifiers=_stubs()).plan(_analysis("direct_fact"))
    assert untouched.requirements.status == "known"
    assert untouched.requirements.weights == (("direct_fact", 1),)


def test_plan_p2_overlap_recomputes_marginal_coverage_after_each_selection():
    analysis = _analysis("direct_fact", "arithmetic", "semantic_comparison", "consistency")
    analysis.research_context.requirement_weights.update(
        direct_fact=.4, arithmetic=.3, semantic_comparison=.2, consistency=.1)
    selector = VerifierSelector(verifiers=[StubVerifier(n) for n in ("a", "b", "c")],
        lambda_cost=0, lambda_latency=0, lambda_suitability=0,
        capabilities={"a": CapabilityDescriptor(("direct_fact", "arithmetic")),
                      "b": CapabilityDescriptor(("direct_fact", "semantic_comparison")),
                      "c": CapabilityDescriptor(("semantic_comparison", "consistency"))})
    selector.reputation_manager.update_reputation("b", "general", True)
    plan = selector.plan(analysis)
    # Initially A adds .7, B .6, C .3. After A, B adds only .2,
    # so C must win despite B's higher utility and registration priority.
    assert plan.candidates[1].utility > plan.candidates[2].utility
    assert plan.initial_selected == ("a", "c")
    assert plan.fallback == ("b",) and plan.expected_uncovered == ()
    assert len(plan.initial_selected) == plan.target_count == 2
