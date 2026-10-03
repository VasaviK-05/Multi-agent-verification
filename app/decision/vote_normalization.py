"""Map verifier outputs onto a pass/reject vote or an abstention.

The four verifiers do not use ``score`` the same way. This module is the
decision layer's reading of those conventions. It does not change verifier
code.

- rule, supported (``metadata.rule`` is present and not ``unsupported``):
  ``score`` is a correctness bit, 1 when the rule passed and 0 when it
  failed. The vote is deterministic, so confidence is 1 either way.
  ``passed=False`` and ``score=0`` on ``arithmetic_addition`` is a
  rejection, not a missing vote. That reading applies only when
  ``verifier_name`` is ``rule``. The same metadata on another verifier
  does not raise its confidence to 1.
- rule, ``metadata.rule == "unsupported"``: the verifier cannot handle the
  question. Abstention. Not a rejection.
- semantic, reasoning says no reference context was provided: abstention.
  Otherwise ``score`` is cosine similarity and is used as the confidence
  already attached to ``passed``. There is no calibration transform.
- evidence, no NLI label (nothing retrieved): abstention. An NLI label of
  ``neutral`` is also an abstention, because that label is not a
  contradiction. Entailment and contradiction keep ``score`` as the NLI
  confidence of that label.
- confidence, no judgments: abstention. A unique majority of ``support``
  or ``reject`` keeps ``score`` as the agreement fraction. A tie for the
  highest judgment count is an abstention, whichever label was listed
  first. Any other unique majority label is an abstention, because
  ``passed=False`` only means "not support".

A usable score has to be a finite number in [0, 1]. Values outside that
range are rejected. They are not clipped into a vote. Anything else uses
that score as confidence in ``passed``.
"""

from __future__ import annotations

import math

from app.models.schemas import VerificationResult

# These rules check structure or range, not factual correctness.
STRUCTURAL_RANGE_RULES = frozenset(
    {
        "probability_range",
        "percentage_range",
        "email_regex",
        "url_regex",
        "date_regex",
        "id_regex",
        "json_structure",
    }
)


def _metadata(result: VerificationResult) -> dict:
    return dict(result.metadata or {})


def _require_result(result: VerificationResult) -> None:
    if not isinstance(result, VerificationResult):
        raise TypeError("results must contain VerificationResult values")
    if not isinstance(result.verifier_name, str) or result.verifier_name.strip() == "":
        raise ValueError("verifier_name must be a non-blank string")
    if not isinstance(result.passed, bool):
        raise TypeError("verifier passed must be a boolean")
    score = result.score
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise TypeError("verifier score must be a finite number in [0, 1]")
    if not math.isfinite(float(score)) or score < 0.0 or score > 1.0:
        raise ValueError("verifier score must be a finite number in [0, 1]")


def _judgment_counts(judgments: object) -> dict[str, int] | None:
    """Count confidence labels, or return None when the list is absent."""
    if not isinstance(judgments, list):
        return None
    counts: dict[str, int] = {}
    for item in judgments:
        if not isinstance(item, str):
            continue
        label = item.strip().lower()
        if label == "":
            continue
        counts[label] = counts.get(label, 0) + 1
    return counts


def confidence_judgment_tie(result: VerificationResult) -> bool:
    """True when the highest stored judgment count is shared.

    Order does not matter. A missing judgment list is not a tie; legacy
    results without that metadata keep their directional vote.
    """
    counts = _judgment_counts(_metadata(result).get("judgments"))
    if not counts:
        return False
    highest = max(counts.values())
    return sum(1 for count in counts.values() if count == highest) > 1


def is_abstention(result: VerificationResult) -> bool:
    """True when the verifier did not cast a pass or reject vote."""
    _require_result(result)
    metadata = _metadata(result)
    name = result.verifier_name
    reasoning = result.reasoning or ""
        # Preserve the verifier result for reporting, but do not treat
    # structural validity as evidence of factual correctness.
    if name == "rule":
        rule = metadata.get("rule")
        if isinstance(rule, str) and rule in STRUCTURAL_RANGE_RULES:
            return True

    if name == "rule" and metadata.get("rule") == "unsupported":
        return True

    if name == "semantic" and "No reference context" in reasoning:
        return True

    if name == "evidence":
        label = metadata.get("nli_label")
        if label is None and result.score == 0.0 and not result.passed:
            return True
        if isinstance(label, str) and label.lower() == "neutral":
            return True

    if name == "confidence":
        judgments = metadata.get("judgments")
        if judgments == [] or (
            "No verification judgments" in reasoning
            or "No valid verification judgments" in reasoning
        ):
            return True
        if confidence_judgment_tie(result):
            return True
        majority = metadata.get("majority_label")
        if isinstance(majority, str) and majority not in {"support", "reject"}:
            return True

    return False


def vote_confidence(result: VerificationResult) -> float:
    """Confidence in the pass/reject vote, in [0, 1]. Abstentions are 0."""
    if is_abstention(result):
        return 0.0
    metadata = _metadata(result)
    rule = metadata.get("rule")
    if (
        result.verifier_name == "rule"
        and isinstance(rule, str)
        and rule != "unsupported"
    ):
        return 1.0
    score = result.score
    return float(score)


def signed_mass(result: VerificationResult) -> float | None:
    """``confidence * (+1 if passed else -1)``, or None when the result abstains."""
    if is_abstention(result):
        return None
    vote = 1.0 if result.passed else -1.0
    return vote_confidence(result) * vote
