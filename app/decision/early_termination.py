"""Adaptive early-termination rule.

The orchestrator calls ``should_terminate`` after each selected verifier.
A False result means keep running the rest of the selected list. The rule
never stops before the difficulty minimum, and a hard question does not
stop early once that minimum is met.

Stopping uses one ``DecisionEngine.decide_detailed`` result for the current
prefix. It does not recompute log-odds, cold-start means, or reputation
rounding. Abstentions, zero-confidence results, and zero log-odds weights
do not count as contributing votes. A negative weight reverses that vote's
direction. Raw pass/reject agreement is not enough when the weighted score
cancels or the decision is uncertain.

This is an UNCALIBRATED threshold heuristic. It is not Wald's sequential
probability ratio test. See docs/decision_formulas.md.
"""

from __future__ import annotations

import math

from app.analysis.question_analyzer import QuestionAnalysis
from app.decision.decision_engine import DecisionDetail, DecisionEngine, VoteExplanation
from app.models.schemas import VerificationResult

# UNCALIBRATED. These minima match VerifierSelector's default range minima.
MIN_VERIFIERS_BY_DIFFICULTY = {
    "easy": 1,
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
        prefix. ``min_verifiers`` overrides the difficulty minimum. The
        orchestrator passes its own engine and the selector minimum.
        Omitting the engine uses a neutral default manager.
        """
        domain = _require_domain(analysis.domain)
        if analysis.difficulty not in MIN_VERIFIERS_BY_DIFFICULTY:
            raise ValueError(f"unknown difficulty {analysis.difficulty!r}")
        required = (
            _require_minimum(min_verifiers)
            if min_verifiers is not None
            else MIN_VERIFIERS_BY_DIFFICULTY[analysis.difficulty]
        )
        engine = decision_engine if decision_engine is not None else DecisionEngine()
        detail = engine.decide_detailed(results, domain=domain)
        contributors = _contributors(detail)
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

    def _cuts(self, difficulty: str) -> tuple[float, float]:
        if difficulty == "easy":
            return self._easy_confidence, self._easy_margin
        return self._medium_confidence, self._medium_margin


def _contributors(detail: DecisionDetail) -> list[tuple[VoteExplanation, int]]:
    """Return ``(vote, effective direction)`` pairs that can support a stop."""
    rows: list[tuple[object, int]] = []
    for vote in detail.votes:
        if vote.abstained or vote.confidence == 0.0:
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


def _require_unit(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite value in [0, 1]")
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be a finite value in [0, 1]")
    return float(value)
