"""Confidence verifier based on self-consistency (majority agreement).

What this verifier measures
    The agreement fraction among several independent verification
    judgments of the same answer. Agreement is a consistency signal only:
    judgments that share the same model bias or the same missing knowledge
    can agree and still be wrong. Whether agreement predicts correctness
    has to be measured against external labels; ``score`` is not accuracy.

Where judgments come from
    Sources, in priority order (cheap explicit input beats sampling):

    1. ``judgments=[...]`` passed to ``verify``.
    2. ``context`` when, and only when, it is a comma-separated list of
       judgment labels. Reference prose is not a judgment list and is
       ignored here (the semantic verifier uses it).
    3. The ``judgment_provider(question, answer) -> list[str]``. By default
       this is ``SelfConsistencyJudge`` (``self_consistency.py``): N
       regenerations from the answer model, each labelled against the
       candidate answer. This is what lets ``ConfidenceVerifier()`` act on
       a bare question/answer pair inside the pipeline. Pass
       ``judgment_provider=None`` for a pure counter with no sampling.

    The verifier never fabricates judgments. If the provider fails (the
    generator is down) it abstains with ``NO_JUDGMENTS_REASON`` as the
    prefix of its reasoning, so the decision layer's hook still matches.

Vocabulary
    ``support``, ``reject``, ``unsure`` (case-insensitive). Any other token
    makes the whole input invalid and the verifier abstains; it does not
    guess what free text meant.

Output contract
    ``score`` = agreement fraction = majority count / total judgments.
    ``passed`` = the majority label is ``support``.
    ``metadata["majority_label"]`` is ``support``, ``reject``, ``unsure``,
    ``tie`` (support and reject tied), or ``invalid``. The decision layer
    treats anything other than ``support``/``reject`` as an abstention.
"""

from __future__ import annotations

import time
from collections import Counter
from typing import Any, Callable, Optional

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import (
    DECISION_REJECT,
    DECISION_SUPPORT,
    DECISION_UNSURE,
    BaseVerifier,
)

VALID_JUDGMENTS = frozenset({"support", "reject", "unsure"})

NO_JUDGMENTS_REASON = "No verification judgments were provided."
INVALID_JUDGMENTS_REASON = (
    "No valid verification judgments were provided: "
    "judgments must be one of support, reject, unsure."
)
PROVIDER_UNAVAILABLE_SOURCE = "provider_unavailable"

JudgmentProvider = Callable[[str, str], list[str]]

# Sentinel: "build the default SelfConsistencyJudge on first use".
# Distinct from None, which means "no provider; count explicit judgments only".
AUTO: Any = object()


def normalize_judgments(judgments: list[str]) -> tuple[list[str], list[str]]:
    """Return (valid lowercase tokens, invalid raw tokens). Blank tokens are dropped."""
    valid: list[str] = []
    invalid: list[str] = []
    for judgment in judgments:
        token = str(judgment).strip().lower()
        if not token:
            continue
        if token in VALID_JUDGMENTS:
            valid.append(token)
        else:
            invalid.append(str(judgment).strip())
    return valid, invalid


def parse_judgment_list(text: Optional[str]) -> Optional[list[str]]:
    """Parse ``text`` as a comma-separated judgment list.

    Returns the normalized tokens when every non-blank token is in the
    vocabulary, otherwise ``None``. Prose therefore returns ``None``.
    """
    if text is None or not text.strip():
        return None
    valid, invalid = normalize_judgments(text.split(","))
    if invalid or not valid:
        return None
    return valid


class ConfidenceVerifier(BaseVerifier):
    """Estimates confidence from agreement among verification judgments."""

    SCORE_MEANING = (
        "Agreement fraction among the judgments (majority count / total). With the "
        "default provider the judgments are N independent regenerations of the answer "
        "labelled against the candidate answer. A consistency signal, not accuracy "
        "and not a probability of correctness: a model can be consistently wrong."
    )

    def __init__(self, judgment_provider: JudgmentProvider | None | Any = AUTO) -> None:
        self._provider_arg = judgment_provider
        self._provider: JudgmentProvider | None = (
            None if judgment_provider is AUTO else judgment_provider
        )

    @property
    def judgment_provider(self) -> JudgmentProvider | None:
        """The provider in use. The default judge is built lazily on first access."""
        if self._provider is None and self._provider_arg is AUTO:
            from app.verifiers.self_consistency import SelfConsistencyJudge

            self._provider = SelfConsistencyJudge()
        return self._provider

    @judgment_provider.setter
    def judgment_provider(self, provider: JudgmentProvider | None) -> None:
        self._provider_arg = provider
        self._provider = provider

    @property
    def name(self) -> str:
        return "confidence"

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def calculate_confidence(self, judgments: list[str]) -> tuple[float, str]:
        """Agreement fraction and a reasoning sentence for valid judgments."""
        valid, invalid = normalize_judgments(judgments)
        if invalid:
            return 0.0, INVALID_JUDGMENTS_REASON
        if not valid:
            return 0.0, NO_JUDGMENTS_REASON

        majority_label, majority_count, confidence = self._majority(valid)
        reasoning = (
            f"Majority judgment: {majority_label}. "
            f"Agreement: {majority_count}/{len(valid)}. "
            f"Confidence: {confidence:.4f}."
        )
        return confidence, reasoning

    @staticmethod
    def _majority(valid: list[str]) -> tuple[str, int, float]:
        """Return (majority_label, majority_count, agreement fraction).

        ``majority_label`` is ``tie`` when two or more labels share the top
        count. ``unsure`` can be the majority on its own.
        """
        counts = Counter(valid)
        top_count = max(counts.values())
        leaders = [label for label, count in counts.items() if count == top_count]
        # Any shared top count (support/reject, or either with unsure) is a tie.
        label = leaders[0] if len(leaders) == 1 else "tie"
        return label, top_count, top_count / len(valid)

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
        judgments: Optional[list[str]] = None,
    ) -> VerificationResult:
        start_time = time.perf_counter()

        try:
            raw_judgments, source, trace = self._collect(question, answer, context, judgments)
        except Exception as exc:  # generator down, timeout, malformed reply
            return self._abstain(
                f"{NO_JUDGMENTS_REASON} Judgment source unavailable: {exc}",
                PROVIDER_UNAVAILABLE_SOURCE,
                [],
                [],
                start_time,
                error=f"{type(exc).__name__}: {exc}",
            )
        if raw_judgments is None:
            return self._abstain(NO_JUDGMENTS_REASON, "none", [], [], start_time)

        valid, invalid = normalize_judgments(raw_judgments)
        if invalid:
            return self._abstain(
                INVALID_JUDGMENTS_REASON,
                source,
                valid,
                invalid,
                start_time,
                majority_label="invalid",
                **trace,
            )
        if not valid:
            return self._abstain(NO_JUDGMENTS_REASON, source, [], [], start_time, **trace)

        majority_label, agreement_count, confidence = self._majority(valid)
        counts = Counter(valid)

        if majority_label == "support":
            decision = DECISION_SUPPORT
        elif majority_label == "reject":
            decision = DECISION_REJECT
        else:
            decision = DECISION_UNSURE
        passed = majority_label == "support"

        if majority_label == "tie":
            verdict = "Judgments are tied; no directional majority."
        elif majority_label == "unsure":
            verdict = "Majority of judgments are unsure."
        else:
            verdict = ""

        latency_ms = (time.perf_counter() - start_time) * 1000
        return VerificationResult(
            verifier_name=self.name,
            score=confidence,
            passed=passed,
            reasoning=(
                f"Majority judgment: {majority_label}. "
                f"Agreement: {agreement_count}/{len(valid)}. "
                f"Confidence: {confidence:.4f}."
                + (f" {verdict}" if verdict else "")
            ),
            metadata={
                "decision": decision,
                "score_meaning": self.SCORE_MEANING,
                "method": "self_consistency",
                "judgment_source": source,
                "judgments": valid,
                "judgment_counts": dict(counts),
                "majority_label": majority_label,
                "agreement_count": agreement_count,
                "total_judgments": len(valid),
                **trace,
                "latency_ms": round(latency_ms, 2),
            },
        )

    def _collect(
        self,
        question: str,
        answer: str,
        context: Optional[str],
        judgments: Optional[list[str]],
    ) -> tuple[Optional[list[str]], str, dict]:
        """Return (raw judgments, source, provider trace) or (None, "none", {}).

        Order: explicit ``judgments`` -> label list in ``context`` -> provider.
        Prose in ``context`` is not judgment input and falls through to the
        provider. Provider exceptions propagate to ``verify``.
        """
        if judgments is not None:
            return list(judgments), "argument", {}

        if context is not None and context.strip():
            parsed = parse_judgment_list(context)
            if parsed is not None:
                return parsed, "context", {}
            tokens = [token.strip() for token in context.split(",") if token.strip()]
            valid, _ = normalize_judgments(tokens)
            if valid and all(" " not in token for token in tokens):
                # A label list with unknown labels ("support,maybe"): report
                # the invalid entries rather than silently dropping them.
                return tokens, "context", {}
            # Otherwise prose: not judgments. Fall through to the provider.

        provider = self.judgment_provider
        if provider is None:
            return None, "none", {}
        provided = provider(question, answer)
        source = getattr(provider, "source_name", "provider")
        trace = getattr(provider, "last_trace", None)
        return list(provided or []), source, dict(trace) if isinstance(trace, dict) else {}

    def _abstain(
        self,
        reasoning: str,
        source: str,
        valid: list[str],
        invalid: list[str],
        start_time: float,
        majority_label: str | None = None,
        **extra: Any,
    ) -> VerificationResult:
        latency_ms = (time.perf_counter() - start_time) * 1000
        metadata = {
            "decision": DECISION_UNSURE,
            "score_meaning": self.SCORE_MEANING,
            "method": "self_consistency",
            "judgment_source": source,
            "judgments": [] if invalid else valid,
            **extra,
            "latency_ms": round(latency_ms, 2),
        }
        if invalid:
            metadata["invalid_judgments"] = invalid
            metadata["valid_judgments"] = valid
        if majority_label is not None:
            metadata["majority_label"] = majority_label
        return VerificationResult(
            verifier_name=self.name,
            score=0.0,
            passed=False,
            reasoning=reasoning,
            metadata=metadata,
        )
