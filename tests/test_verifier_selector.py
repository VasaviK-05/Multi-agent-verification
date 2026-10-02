"""Isolated tests for VerifierSelector."""

import math

import pytest

from app.analysis.question_analyzer import QuestionAnalysis
from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import ReputationManager
from app.selection.verifier_selector import (
    DEFAULT_DIFFICULTY_RANGE,
    VerifierSelector,
    suitability_by_verifier,
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
    selector = VerifierSelector()
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
    assert selector.target_count(QuestionAnalysis("general", "easy", 0.0)) == 1
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
    selector = VerifierSelector(reputation_manager=manager)
    selected = selector.select(
        QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.1)
    )
    assert selected[0].name == "rule"


def _names(selector: VerifierSelector, analysis: QuestionAnalysis) -> list[str]:
    return [verifier.name for verifier in selector.iter_ranked(analysis)]


def test_empty_verification_types_keep_the_resource_ranking():
    selector = VerifierSelector(verifiers=_stubs())
    analysis = QuestionAnalysis("general", "easy", 0.1, verification_types=[])
    assert _names(selector, analysis) == ["rule", "semantic", "confidence", "evidence"]
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
        "confidence",
        "evidence",
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
