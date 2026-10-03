"""Semantic similarity verifier.

Compares a representation of the generated answer with reference text
using Sentence-BERT embeddings and cosine similarity.

What this verifier measures
    Resemblance of meaning between two texts. It does not measure factual
    correctness: "The Sun revolves around the Earth" is close to "The Earth
    revolves around the Sun" in embedding space. Low similarity means the
    texts talk about different things, which is not evidence that the
    answer is false.

Output contract
    ``score`` is cosine similarity clipped to [0, 1]. Cosine similarity can
    be negative; the raw value is kept in ``metadata["raw_similarity"]``.
    Clipping only satisfies the schema bound. It is not a calibrated
    probability and must not be read as one.

    ``metadata["decision"]`` uses two UNCALIBRATED thresholds:
        similarity >= SUPPORT_THRESHOLD  -> SUPPORT
        similarity <  REJECT_THRESHOLD   -> REJECT
        otherwise                        -> UNSURE
    ``passed`` is ``similarity >= SUPPORT_THRESHOLD``. The decision layer
    currently reads every non-abstaining semantic result as a vote with
    confidence ``score``; the UNSURE band is reported for it to consume.

Comparison representation
    ``comparison_mode`` selects what is embedded against the reference:
    ``question_answer`` (question + answer), ``answer`` (answer alone), or
    ``claim`` (answer rewritten as a declarative sentence). Measured on 800
    HaluEval QA pairs with the knowledge passage as reference, threshold
    0.5: question_answer F1 0.649 (acc 0.520), claim F1 0.645 (acc 0.521),
    answer F1 0.290 (acc 0.309; hallucinated answers were *closer* to the
    passage than the short right answers, and this mode produced negative
    similarities). ``question_answer`` is therefore the default. All three
    separate correct from hallucinated answers only weakly, which is the
    limitation described above, not a bug in one mode.

Abstention
    Without reference text this verifier abstains. The reasoning begins
    with "No reference context", which is the hook the decision layer uses
    to recognise the abstention. A ``context`` that holds confidence
    judgment labels ("support,reject,...") is not reference text and also
    abstains.
"""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import (
    DECISION_REJECT,
    DECISION_SUPPORT,
    DECISION_UNSURE,
    BaseVerifier,
)
from app.verifiers.claim_generator import ClaimGenerator
from app.verifiers.confidence_verifier import parse_judgment_list

NO_CONTEXT_REASON = "No reference context provided for semantic comparison."
JUDGMENT_CONTEXT_REASON = (
    "No reference context provided for semantic comparison "
    "(context held judgment labels)."
)


class SemanticVerifier(BaseVerifier):
    """Checks semantic similarity between an answer and reference context."""

    MODEL_NAME = "all-MiniLM-L6-v2"

    # UNCALIBRATED. SUPPORT_THRESHOLD is the historical pass boundary.
    SUPPORT_THRESHOLD = 0.5
    REJECT_THRESHOLD = 0.3
    # Backwards-compatible alias.
    SIMILARITY_THRESHOLD = SUPPORT_THRESHOLD

    COMPARISON_MODES = ("question_answer", "answer", "claim")
    DEFAULT_COMPARISON_MODE = "question_answer"

    SCORE_MEANING = (
        "Cosine similarity between the compared text and the reference, "
        "clipped to [0, 1]. Measures resemblance of meaning, not factual "
        "correctness; not a probability and not calibrated."
    )

    def __init__(
        self,
        comparison_mode: str | None = None,
        model=None,
        model_name: str | None = None,
    ) -> None:
        mode = comparison_mode or self.DEFAULT_COMPARISON_MODE
        if mode not in self.COMPARISON_MODES:
            raise ValueError(
                f"comparison_mode must be one of {self.COMPARISON_MODES}, got {mode!r}"
            )
        self.comparison_mode = mode
        self.model_name = model_name or self.MODEL_NAME
        if model is None:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_name)
        self.model = model
        self._claim_generator = ClaimGenerator()

    @property
    def name(self) -> str:
        return "semantic"

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def comparison_text(self, question: str, answer: str) -> str:
        """Text that is embedded and compared with the reference."""
        if self.comparison_mode == "answer":
            return answer.strip()
        if self.comparison_mode == "claim":
            return self._claim_generator.generate(question, answer)
        return f"{question.strip()} {answer.strip()}"

    @staticmethod
    def cosine_similarity(first: np.ndarray, second: np.ndarray) -> float:
        first = np.asarray(first, dtype=np.float64).ravel()
        second = np.asarray(second, dtype=np.float64).ravel()
        denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
        if denominator == 0.0:
            return 0.0
        return float(np.dot(first, second) / denominator)

    def similarity(self, question: str, answer: str, context: str) -> tuple[float, str]:
        """Return (raw cosine similarity, compared text)."""
        text = self.comparison_text(question, answer)
        embeddings = self.model.encode([text, context])
        return self.cosine_similarity(embeddings[0], embeddings[1]), text

    def decide(self, raw_similarity: float) -> str:
        if raw_similarity >= self.SUPPORT_THRESHOLD:
            return DECISION_SUPPORT
        if raw_similarity < self.REJECT_THRESHOLD:
            return DECISION_REJECT
        return DECISION_UNSURE

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        start_time = time.perf_counter()

        if not context or not context.strip():
            return self._abstain(NO_CONTEXT_REASON, "no_context", start_time)

        if parse_judgment_list(context) is not None:
            return self._abstain(JUDGMENT_CONTEXT_REASON, "context_was_judgment_list", start_time)

        raw, compared_text = self.similarity(question, answer, context)
        score = min(max(raw, 0.0), 1.0)
        decision = self.decide(raw)
        passed = decision == DECISION_SUPPORT

        if decision == DECISION_SUPPORT:
            verdict = "Compared text is semantically close to the reference."
        elif decision == DECISION_REJECT:
            verdict = (
                "Compared text is semantically far from the reference. "
                "Low similarity is not evidence of falsity; treat as a weak signal."
            )
        else:
            verdict = "Similarity falls between the reject and support thresholds."

        latency_ms = (time.perf_counter() - start_time) * 1000
        return VerificationResult(
            verifier_name=self.name,
            score=score,
            passed=passed,
            reasoning=(
                f"Semantic similarity score: {raw:.4f}. "
                f"Support threshold: {self.SUPPORT_THRESHOLD:.2f}; "
                f"reject threshold: {self.REJECT_THRESHOLD:.2f}. {verdict}"
            ),
            metadata={
                "decision": decision,
                "score_meaning": self.SCORE_MEANING,
                "raw_similarity": raw,
                "threshold": self.SUPPORT_THRESHOLD,
                "support_threshold": self.SUPPORT_THRESHOLD,
                "reject_threshold": self.REJECT_THRESHOLD,
                "thresholds_calibrated": False,
                "comparison_method": f"{self.comparison_mode}_vs_context",
                "compared_text": compared_text,
                "model": self.model_name,
                "latency_ms": round(latency_ms, 2),
            },
        )

    def _abstain(self, reasoning: str, abstain_reason: str, start_time: float) -> VerificationResult:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return VerificationResult(
            verifier_name=self.name,
            score=0.0,
            passed=False,
            reasoning=reasoning,
            metadata={
                "decision": DECISION_UNSURE,
                "score_meaning": self.SCORE_MEANING,
                "abstain_reason": abstain_reason,
                "threshold": self.SUPPORT_THRESHOLD,
                "support_threshold": self.SUPPORT_THRESHOLD,
                "reject_threshold": self.REJECT_THRESHOLD,
                "comparison_method": f"{self.comparison_mode}_vs_context",
                "latency_ms": round(latency_ms, 2),
            },
        )
