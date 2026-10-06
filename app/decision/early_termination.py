"""Adaptive early-termination rule.

Standalone stopping assessment; orchestration wiring remains deferred.
A False result means continue verification when candidates remain. Easy
and medium require at least two contributors, or a larger supplied minimum.
Hard questions never stop early. Approval does not establish factual
coverage: orchestration must also satisfy requested capabilities.

Stopping uses one ``DecisionEngine.decide_detailed`` result for the current
prefix. It does not recompute log-odds, cold-start means, or reputation
rounding. Abstentions, zero-confidence results, structural rule outputs,
and zero log-odds weights do not count as contributing votes. A negative
weight reverses effective direction. In addition, original directional
disagreement vetoes stopping, including dissent with zero or negative
weight. This conservative stopping policy does not change aggregation.

This is an UNCALIBRATED threshold heuristic. It is not Wald's sequential
probability ratio test. See docs/decision_formulas.md.
"""

from __future__ import annotations

import math

from app.analysis.question_analyzer import QuestionAnalysis
from app.decision.decision_engine import DecisionDetail, DecisionEngine, VoteExplanation
from app.decision.vote_normalization import STRUCTURAL_RANGE_RULES
from app.models.schemas import VerificationResult

# UNCALIBRATED. These minima match VerifierSelector's default range minima.
MIN_VERIFIERS_BY_DIFFICULTY = {
    "easy": 2,
    "medium": 2,
    "hard": 3,
}
EASY_CONFIDENCE = 0.75
STRONG_CONFIDENCE = 0.80
EASY_MARGIN = 0.60
STRONG_MARGIN = 0.70


class AdaptiveEarlyTermination:
    """Sequential stopping rule for an already chosen verifier list."""

    def __init__(
        self,
        *,
        easy_confidence: float = EASY_CONFIDENCE,
        easy_margin: float = EASY_MARGIN,
        medium_confidence: float = STRONG_CONFIDENCE,
        medium_margin: float = STRONG_MARGIN,
    ) -> None:
        self._easy_confidence = _require_unit("easy_confidence", easy_confidence)
        self._easy_margin = _require_unit("easy_margin", easy_margin)
        self._medium_confidence = _require_unit("medium_confidence", medium_confidence)
        self._medium_margin = _require_unit("medium_margin", medium_margin)

    def should_terminate(
        self,
        results: list[VerificationResult],
        analysis: QuestionAnalysis,
        min_verifiers: int | None = None,
        *,
        decision_engine: DecisionEngine | None = None,
    ) -> dict:
        """Return ``terminate`` and ``reason``.

        A stop also includes ``decision``, the immutable detail for this
        prefix. ``min_verifiers`` supplies the selector minimum, subject
        to an easy/medium floor of two. Callers should supply their shared
        engine; omission uses a neutral default manager. Orchestration
        must check requested factual coverage before using this approval.
        """
        domain = _require_domain(analysis.domain)
        if analysis.difficulty not in MIN_VERIFIERS_BY_DIFFICULTY:
            raise ValueError(f"unknown difficulty {analysis.difficulty!r}")
        _require_score(analysis.difficulty_score)
        required = (
            _require_minimum(min_verifiers)
            if min_verifiers is not None
            else MIN_VERIFIERS_BY_DIFFICULTY[analysis.difficulty]
        )
        if analysis.difficulty != "hard":
            required = max(2, required)
        engine = decision_engine if decision_engine is not None else DecisionEngine()
        detail = engine.decide_detailed(results, domain=domain)
        structural_names = {
            result.verifier_name for result in results if _is_structural_rule(result)
        }
        contributors = _contributors(detail, structural_names)
        if not contributors:
            return _continue("no usable contributing votes")
        if len(contributors) < required:
            return _continue(
                f"minimum {required} contributing verifier(s) not yet available"
            )
        if analysis.difficulty == "hard":
            return _continue("hard question — continue verification")

        directions = {direction for _vote, direction in contributors}
        if len(directions) != 1:
            return _continue("effective disagreement — continue verification")
        raw_directions = {
            vote.passed for vote in detail.votes
            if not vote.abstained and vote.confidence > 0.0
            and vote.verifier_name not in structural_names
        }
        if len(raw_directions) > 1:
            return _continue("original directional disagreement — continue verification")
        if detail.status not in {"passed", "failed"}:
            return _continue("uncertain weighted decision — continue verification")

        confidence_cut, margin_cut = self._cuts(analysis.difficulty)
        average_confidence = sum(vote.confidence for vote, _direction in contributors) / len(
            contributors
        )
        if average_confidence < confidence_cut or abs(detail.raw_score) < margin_cut:
            return _continue("insufficient confidence or margin to stop early")
        return {
            "terminate": True,
            "reason": (
                f"{analysis.difficulty} question with sufficient confidence, "
                "margin, and a decisive decision"
            ),
            "decision": detail,
        }

    @staticmethod
    def contributor_count(
        detail: DecisionDetail, results: list[VerificationResult],
    ) -> int:
        """Count eligible contributors in an already captured decision.

        Results supply structural metadata only; no reputation reads or
        numerical aggregation occur here. They must be the assessed prefix.
        """
        if tuple(r.verifier_name for r in results) != tuple(v.verifier_name for v in detail.votes):
            raise ValueError("results must match the decision snapshot prefix")
        structural = {r.verifier_name for r in results if _is_structural_rule(r)}
        return len(_contributors(detail, structural))

    def _cuts(self, difficulty: str) -> tuple[float, float]:
        if difficulty == "easy":
            return self._easy_confidence, self._easy_margin
        return self._medium_confidence, self._medium_margin


def _is_structural_rule(result: VerificationResult) -> bool:
    """Use RuleVerifier's factual/structural kind, scoped to its identity.

    Old results with absent/null kind use only the normalization layer's
    established structural/range labels. format_validity is factual: it
    answers an explicit validity question, unlike generating formatted text.
    """
    if result.verifier_name != "rule":
        return False
    metadata = result.metadata or {}
    kind = metadata.get("rule_kind")
    if kind is not None:
        return kind == "structural"
    rule = metadata.get("rule")
    return isinstance(rule, str) and rule in STRUCTURAL_RANGE_RULES


def _contributors(
    detail: DecisionDetail, structural_names: set[str],
) -> list[tuple[VoteExplanation, int]]:
    """Return ``(vote, effective direction)`` pairs that can support a stop."""
    rows: list[tuple[VoteExplanation, int]] = []
    for vote in detail.votes:
        if vote.verifier_name in structural_names or vote.abstained or vote.confidence == 0.0:
            continue
        if detail.aggregation == "equal_weight":
            direction = 1 if vote.passed else -1
        elif detail.aggregation == "log_odds":
            if vote.weight == 0.0:
                continue
            direction = 1 if vote.passed else -1
            if vote.weight < 0.0:
                direction = -direction
        else:
            continue
        rows.append((vote, direction))
    return rows


def _continue(reason: str) -> dict:
    return {"terminate": False, "reason": reason}


def _require_domain(domain: object) -> str:
    if not isinstance(domain, str) or domain.strip() == "":
        raise ValueError("domain must be a non-blank string")
    return domain


def _require_minimum(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("min_verifiers must be a positive integer")
    return value


def _require_score(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("difficulty_score must be a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError("difficulty_score must be a finite number")


def _require_unit(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite value in [0, 1]")
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be a finite value in [0, 1]")
    return float(value)
