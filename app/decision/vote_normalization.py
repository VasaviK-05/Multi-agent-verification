"""Map verifier outputs onto a pass/reject vote or an abstention.

The four verifiers do not use ``score`` the same way. This module is the
decision layer's reading of those conventions. It does not change verifier
code.

- rule, supported (``metadata.rule`` is present and not ``unsupported``):
  ``score`` is a correctness bit, 1 when the rule passed and 0 when it
  failed. The vote is deterministic, so confidence is 1 either way.
  ``passed=False`` and ``score=0`` on ``arithmetic_addition`` is a
  rejection, not a missing vote.
- rule, ``metadata.rule == "unsupported"``: the verifier cannot handle the
  question. Abstention. Not a rejection.
- semantic, reasoning says no reference context was provided: abstention.
  Otherwise ``score`` is cosine similarity and is used as the confidence
  already attached to ``passed``.
- evidence, no NLI label (nothing retrieved): abstention. An NLI label of
  ``neutral`` is also an abstention, because that label is not a
  contradiction. Entailment and contradiction keep ``score`` as the NLI
  confidence of that label.
- confidence, no judgments: abstention. A majority of ``support`` or
  ``reject`` keeps ``score`` as the agreement fraction. Any other majority
  label is an abstention, because ``passed=False`` only means "not support".

Anything else uses ``clip(score, 0, 1)`` as confidence in ``passed``.
"""

from __future__ import annotations

from app.models.schemas import VerificationResult


def _metadata(result: VerificationResult) -> dict:
    return dict(result.metadata or {})


def is_abstention(result: VerificationResult) -> bool:
    """True when the verifier did not cast a pass or reject vote."""
    metadata = _metadata(result)
    rule = metadata.get("rule")
    if rule == "unsupported":
        return True

    name = result.verifier_name
    reasoning = result.reasoning or ""

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
    if isinstance(rule, str) and rule != "unsupported":
        return 1.0
    return min(max(float(result.score), 0.0), 1.0)


def signed_mass(result: VerificationResult) -> float | None:
    """``confidence * (+1 if passed else -1)``, or None when the result abstains."""
    if is_abstention(result):
        return None
    vote = 1.0 if result.passed else -1.0
    return vote_confidence(result) * vote
