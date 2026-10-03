"""Evidence-based verifier: FAISS retrieval + Natural Language Inference.

Pipeline, per claim in the answer:

    claim -> retrieve top-k chunks -> relevance gate -> NLI on each kept
    chunk (premise = chunk excerpt, hypothesis = claim) -> per-claim
    decision -> aggregate across claims

Three different scores appear in the output and must not be confused:
    retrieval_score   cosine similarity of the query and a chunk ("is this
                      chunk about the claim?")
    probabilities     NLI class probabilities for one chunk/claim pair
    score             the NLI probability of the label that decided the
                      final result (see ``SCORE_MEANING``)

Relevance gate (issue 6)
    FAISS always returns the nearest chunks. If the best hit is below
    ``min_retrieval_score`` the corpus has nothing on the claim and the
    verifier abstains instead of running NLI on unrelated text. Chunks
    further than ``retrieval_margin`` below the best hit are dropped so a
    distant neighbour (e.g. "Berlin is the capital of Germany" for a claim
    about France) cannot create a false contradiction.

    The default floor of 0.45 comes from a probe on the test corpus: claims
    the corpus covers retrieved their chunk at >= 0.78, while claims it
    does not cover ("capital of Japan", "Alan Turing") had nearest
    neighbours at 0.39-0.41 that the NLI model nonetheless labelled as
    0.999 contradictions. It is UNCALIBRATED for the full corpus and has to
    be re-fitted on labelled data.

Per-claim aggregation (issue 5)
    A chunk is a strong entailment / contradiction when that class is the
    argmax and its probability is >= ``min_nli_score``.
        strong entailment and strong contradiction -> UNSURE (conflict)
        strong entailment only                      -> SUPPORT
        strong contradiction only                   -> REJECT
        neither                                     -> UNSURE (neutral)
    Conflicts are reported, not resolved by picking the favourable side.

Across claims (issue 7)
    all SUPPORT -> SUPPORT (confidence = weakest claim)
    any REJECT  -> REJECT  (confidence = strongest rejection)
    otherwise   -> UNSURE  (partial support / unchecked claims listed)

Decision-layer hooks (unchanged)
    SUPPORT -> passed=True,  nli_label="entailment"
    REJECT  -> passed=False, nli_label="contradiction"
    UNSURE  -> passed=False, nli_label="neutral" (evidence was evaluated)
               or nli_label=None, score=0 (nothing relevant retrieved)
    Both UNSURE forms are abstentions for the decision layer.

All thresholds are UNCALIBRATED defaults and are echoed in metadata.
"""

from __future__ import annotations

import functools
import re
import time
from typing import Any, Callable, Optional

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import (
    DECISION_REJECT,
    DECISION_SUPPORT,
    DECISION_UNSURE,
    BaseVerifier,
)
from app.verifiers.claim_generator import ClaimGenerator
from app.verifiers.evidence_retriever import EvidenceRetriever

NLI_LABELS = ("entailment", "contradiction", "neutral")
NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
NO_EVIDENCE_REASON = "No evidence was retrieved."
NO_RELEVANT_EVIDENCE_REASON = "No sufficiently relevant evidence was retrieved."


@functools.lru_cache(maxsize=1)
def default_nli_pipeline() -> Any:
    """Process-wide NLI pipeline shared by the evidence and confidence verifiers.

    Loading the cross-encoder twice costs several hundred MB; both verifiers
    call this when no ``nli`` is injected. ``top_k=None`` returns every label
    so callers can read all three probabilities.
    """
    from transformers import pipeline

    return pipeline("text-classification", model=NLI_MODEL, top_k=None)


def normalize_nli_label(label: str) -> str:
    """Map a model label string onto entailment / contradiction / neutral.

    Raises ``ValueError`` for labels that match none of them (for example
    ``LABEL_0``), so a model with an unexpected label set fails loudly
    instead of being read as neutral.
    """
    lowered = str(label).strip().lower()
    if "entail" in lowered:
        return "entailment"
    if "contradict" in lowered:
        return "contradiction"
    if "neutral" in lowered:
        return "neutral"
    raise ValueError(f"Unrecognised NLI label {label!r}; expected one of {NLI_LABELS}")


def parse_nli_output(raw: Any) -> tuple[dict[str, float], str]:
    """Normalise a text-classification pipeline output for one input.

    Accepts the shapes different Transformers versions produce for a
    single ``{"text", "text_pair"}`` input:
        dict                      -> top label only
        list[dict]                -> all labels (``top_k=None``) or one
        list[list[dict]]          -> batch of one input
    Returns ``({label: probability}, shape_name)``.
    """
    if isinstance(raw, dict):
        rows, shape = [raw], "dict"
    elif isinstance(raw, list) and raw and isinstance(raw[0], list):
        rows, shape = raw[0], "list[list[dict]]"
    elif isinstance(raw, list):
        rows, shape = raw, "list[dict]"
    else:
        raise ValueError(f"Unexpected NLI output type {type(raw).__name__}")

    probabilities: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict) or "label" not in row or "score" not in row:
            raise ValueError(f"Unexpected NLI output row {row!r}")
        probabilities[normalize_nli_label(row["label"])] = float(row["score"])
    if not probabilities:
        raise ValueError("NLI output contained no labels")
    return probabilities, shape


class EvidenceVerifier(BaseVerifier):
    """Verifies each claim of an answer against retrieved evidence using NLI."""

    NLI_MODEL = NLI_MODEL

    SCORE_MEANING = (
        "NLI probability of the label that decided the result (entailment for "
        "SUPPORT, contradiction for REJECT) on the deciding evidence chunk; 0 for "
        "UNSURE. A class probability from one model, not a calibrated probability "
        "that the answer is correct."
    )

    def __init__(
        self,
        corpus_path: str = "data/evidence_corpus.json",
        top_k: int = 3,
        min_retrieval_score: float = 0.45,
        retrieval_margin: float = 0.15,
        min_nli_score: float = 0.50,
        retriever: EvidenceRetriever | None = None,
        nli: Callable[[dict], Any] | None = None,
    ) -> None:
        self.retriever = retriever or EvidenceRetriever(corpus_path=corpus_path)
        self.top_k = top_k
        self.min_retrieval_score = min_retrieval_score
        self.retrieval_margin = retrieval_margin
        self.min_nli_score = min_nli_score
        self.claim_generator = ClaimGenerator()

        if nli is None:
            nli = default_nli_pipeline()
        self.nli = nli
        self.nli_label_map = self._check_label_map(nli)

    @property
    def name(self) -> str:
        return "evidence"

    # ------------------------------------------------------------------
    # NLI helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_label_map(nli: Any) -> dict[str, str] | None:
        """Verify the model's id2label covers the three NLI classes, if visible."""
        config = getattr(getattr(nli, "model", None), "config", None)
        id2label = getattr(config, "id2label", None)
        if not id2label:
            return None
        mapping = {str(label): normalize_nli_label(label) for label in id2label.values()}
        missing = set(NLI_LABELS) - set(mapping.values())
        if missing:
            raise ValueError(f"NLI model labels {list(id2label.values())} do not cover {sorted(missing)}")
        return mapping

    def extract_relevant_sentences(self, text: str, claim: str, max_sentences: int = 3) -> str:
        """Pick the chunk sentences with most word overlap with the claim.

        Chunks can exceed the NLI model's input length; this keeps the
        premise short and on-topic. Falls back to the chunk head when no
        sentence shares a word with the claim.
        """
        sentences = re.split(r"(?<=[.!?])\s+", text)
        claim_words = {w.lower() for w in re.findall(r"\b\w+\b", claim)}

        scored = []
        for sentence in sentences:
            words = {w.lower() for w in re.findall(r"\b\w+\b", sentence)}
            overlap = len(claim_words & words)
            if overlap > 0:
                scored.append((overlap, sentence.strip()))
        scored.sort(key=lambda item: item[0], reverse=True)
        selected = [sentence for _, sentence in scored[:max_sentences]]
        return " ".join(selected) if selected else text[:1500]

    def score_evidence(self, evidence: dict, claim: str) -> dict:
        """Run NLI for one chunk/claim pair and return a flat evidence row."""
        premise = self.extract_relevant_sentences(evidence["text"], claim)
        probabilities, shape = parse_nli_output(self.nli({"text": premise, "text_pair": claim}))
        label = max(probabilities, key=probabilities.get)
        return {
            "title": evidence.get("title"),
            "chunk_id": evidence.get("chunk_id"),
            "url": evidence.get("url"),
            "retrieval_score": float(evidence["score"]),
            "relevant_evidence": premise,
            "nli_label": label,
            "nli_score": probabilities[label],
            "probabilities": probabilities,
            "nli_output_shape": shape,
        }

    # ------------------------------------------------------------------
    # Relevance and aggregation
    # ------------------------------------------------------------------

    def select_relevant(self, retrieved: list[dict]) -> list[dict]:
        """Apply the relevance floor and the margin below the best hit."""
        if not retrieved:
            return []
        best = max(item["score"] for item in retrieved)
        if best < self.min_retrieval_score:
            return []
        cutoff = best - self.retrieval_margin
        return [item for item in retrieved if item["score"] >= cutoff]

    def _strong(self, rows: list[dict], label: str) -> list[dict]:
        return [
            row
            for row in rows
            if row["nli_label"] == label and row["probabilities"].get(label, 0.0) >= self.min_nli_score
        ]

    def aggregate_chunks(self, rows: list[dict]) -> dict:
        """Per-claim decision from the NLI rows of its kept chunks."""
        supporting = self._strong(rows, "entailment")
        contradicting = self._strong(rows, "contradiction")

        if supporting and contradicting:
            return {
                "decision": DECISION_UNSURE,
                "unsure_reason": "conflict",
                "confidence": 0.0,
                "deciding": None,
                "supporting": supporting,
                "contradicting": contradicting,
            }
        if supporting:
            best = max(supporting, key=lambda row: row["probabilities"]["entailment"])
            return {
                "decision": DECISION_SUPPORT,
                "unsure_reason": None,
                "confidence": best["probabilities"]["entailment"],
                "deciding": best,
                "supporting": supporting,
                "contradicting": [],
            }
        if contradicting:
            best = max(contradicting, key=lambda row: row["probabilities"]["contradiction"])
            return {
                "decision": DECISION_REJECT,
                "unsure_reason": None,
                "confidence": best["probabilities"]["contradiction"],
                "deciding": best,
                "supporting": [],
                "contradicting": contradicting,
            }
        return {
            "decision": DECISION_UNSURE,
            "unsure_reason": "neutral",
            "confidence": 0.0,
            "deciding": None,
            "supporting": [],
            "contradicting": [],
        }

    @staticmethod
    def aggregate_claims(claim_results: list[dict]) -> tuple[str, float, str | None, dict | None]:
        """Return (decision, confidence, unsure_reason, deciding claim result)."""
        if claim_results and all(c["decision"] == DECISION_SUPPORT for c in claim_results):
            weakest = min(claim_results, key=lambda c: c["confidence"])
            return DECISION_SUPPORT, weakest["confidence"], None, weakest

        rejections = [c for c in claim_results if c["decision"] == DECISION_REJECT]
        if rejections:
            strongest = max(rejections, key=lambda c: c["confidence"])
            return DECISION_REJECT, strongest["confidence"], None, strongest

        reasons = {c["unsure_reason"] for c in claim_results if c["decision"] == DECISION_UNSURE}
        if any(c["decision"] == DECISION_SUPPORT for c in claim_results):
            reason = "partial_support"
        elif reasons == {"no_relevant_evidence"}:
            reason = "no_relevant_evidence"
        elif "conflict" in reasons:
            reason = "conflict"
        else:
            reason = "neutral"
        return DECISION_UNSURE, 0.0, reason, None

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        start = time.perf_counter()
        retrieval_ms = 0.0
        nli_ms = 0.0

        claims = self.claim_generator.generate_claims(question, answer)
        claim_results: list[dict] = []
        any_retrieved = False

        for position, item in enumerate(claims):
            claim = item["claim"]
            query = f"{question} {claim}"

            t0 = time.perf_counter()
            retrieved = self.retriever.retrieve(query, k=self.top_k)
            retrieval_ms += (time.perf_counter() - t0) * 1000
            any_retrieved = any_retrieved or bool(retrieved)

            best_score = max((r["score"] for r in retrieved), default=None)
            kept = self.select_relevant(retrieved)
            if not kept:
                claim_results.append(
                    {
                        "index": position,
                        "claim": claim,
                        "template": item["template"],
                        "decision": DECISION_UNSURE,
                        "unsure_reason": "no_relevant_evidence",
                        "confidence": 0.0,
                        "best_retrieval_score": best_score,
                        "deciding": None,
                        "supporting": [],
                        "contradicting": [],
                        "evidence": [],
                    }
                )
                continue

            t0 = time.perf_counter()
            rows = [self.score_evidence(evidence, claim) for evidence in kept]
            nli_ms += (time.perf_counter() - t0) * 1000

            aggregated = self.aggregate_chunks(rows)
            aggregated.update(
                {
                    "index": position,
                    "claim": claim,
                    "template": item["template"],
                    "best_retrieval_score": best_score,
                    "evidence": rows,
                }
            )
            claim_results.append(aggregated)

        decision, confidence, unsure_reason, deciding_claim = self.aggregate_claims(claim_results)
        total_ms = (time.perf_counter() - start) * 1000
        return self._build_result(
            decision=decision,
            confidence=confidence,
            unsure_reason=unsure_reason,
            deciding_claim=deciding_claim,
            claim_results=claim_results,
            any_retrieved=any_retrieved,
            latency={"retrieval": retrieval_ms, "nli": nli_ms, "total": total_ms},
        )

    def _build_result(
        self,
        *,
        decision: str,
        confidence: float,
        unsure_reason: str | None,
        deciding_claim: dict | None,
        claim_results: list[dict],
        any_retrieved: bool,
        latency: dict[str, float],
    ) -> VerificationResult:
        evaluated_evidence = [
            {"claim_index": c["index"], **{k: v for k, v in row.items()}}
            for c in claim_results
            for row in c["evidence"]
        ]
        evidence_evaluated = bool(evaluated_evidence)

        if decision == DECISION_SUPPORT:
            nli_label, passed = "entailment", True
        elif decision == DECISION_REJECT:
            nli_label, passed = "contradiction", False
        elif evidence_evaluated:
            nli_label, passed = "neutral", False
        else:
            nli_label, passed = None, False

        deciding_row = deciding_claim["deciding"] if deciding_claim else None
        unchecked = [c["claim"] for c in claim_results if c["unsure_reason"] == "no_relevant_evidence"]
        reasoning = self._reasoning(decision, unsure_reason, deciding_claim, claim_results, any_retrieved)

        metadata = {
            "decision": decision,
            "score_meaning": self.SCORE_MEANING,
            "nli_label": nli_label,
            "nli_model": self.NLI_MODEL,
            "nli_output_shape": evaluated_evidence[0]["nli_output_shape"] if evaluated_evidence else None,
            "unsure_reason": unsure_reason,
            "top_k": self.top_k,
            "min_retrieval_score": self.min_retrieval_score,
            "retrieval_margin": self.retrieval_margin,
            "min_nli_score": self.min_nli_score,
            "thresholds_calibrated": False,
            "claims": [c["claim"] for c in claim_results],
            "claim_decisions": [
                {
                    "claim": c["claim"],
                    "template": c["template"],
                    "decision": c["decision"],
                    "confidence": c["confidence"],
                    "unsure_reason": c["unsure_reason"],
                    "best_retrieval_score": c["best_retrieval_score"],
                }
                for c in claim_results
            ],
            "unchecked_claims": unchecked,
            "supporting": [self._brief(r) for c in claim_results for r in c["supporting"]],
            "contradicting": [self._brief(r) for c in claim_results for r in c["contradicting"]],
            "evaluated_evidence": evaluated_evidence,
            "evidence_title": deciding_row["title"] if deciding_row else None,
            "evidence_chunk_id": deciding_row["chunk_id"] if deciding_row else None,
            "retrieval_score": deciding_row["retrieval_score"] if deciding_row else None,
            "best_retrieval_score": max(
                (c["best_retrieval_score"] for c in claim_results if c["best_retrieval_score"] is not None),
                default=None,
            ),
            "latency_ms": round(latency["total"], 2),
            "latency_breakdown_ms": {k: round(v, 2) for k, v in latency.items()},
        }
        return VerificationResult(
            verifier_name=self.name,
            score=min(max(float(confidence), 0.0), 1.0),
            passed=passed,
            reasoning=reasoning,
            metadata=metadata,
        )

    @staticmethod
    def _brief(row: dict) -> dict:
        return {
            "title": row["title"],
            "chunk_id": row["chunk_id"],
            "retrieval_score": row["retrieval_score"],
            "nli_label": row["nli_label"],
            "nli_score": row["nli_score"],
            "excerpt": row["relevant_evidence"][:300],
        }

    @staticmethod
    def _reasoning(
        decision: str,
        unsure_reason: str | None,
        deciding_claim: dict | None,
        claim_results: list[dict],
        any_retrieved: bool,
    ) -> str:
        n = len(claim_results)
        if decision == DECISION_SUPPORT:
            row = deciding_claim["deciding"]
            return (
                f"NLI result: entailment. Retrieved evidence entails "
                f"{'the claim' if n == 1 else f'all {n} claims'}. "
                f"Evidence: {row['title']}. Claim: {deciding_claim['claim']} "
                f"NLI confidence: {row['probabilities']['entailment']:.4f}."
            )
        if decision == DECISION_REJECT:
            row = deciding_claim["deciding"]
            return (
                f"NLI result: contradiction. Retrieved evidence contradicts the claim. "
                f"Evidence: {row['title']}. Claim: {deciding_claim['claim']} "
                f"NLI confidence: {row['probabilities']['contradiction']:.4f}."
            )
        if unsure_reason == "no_relevant_evidence":
            return NO_RELEVANT_EVIDENCE_REASON if any_retrieved else NO_EVIDENCE_REASON
        if unsure_reason == "conflict":
            return (
                "NLI result: neutral (conflict). Retrieved evidence both entails and "
                "contradicts the claim; see supporting and contradicting in metadata."
            )
        if unsure_reason == "partial_support":
            unchecked = [c["claim"] for c in claim_results if c["decision"] != DECISION_SUPPORT]
            return (
                "NLI result: neutral (partial support). Some claims are entailed, but "
                f"{len(unchecked)} of {n} could not be established: {' | '.join(unchecked)}"
            )
        return "NLI result: neutral. Retrieved evidence neither entails nor contradicts the claim."
