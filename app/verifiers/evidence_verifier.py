"""Evidence-based verifier using FAISS retrieval and NLI.""" 

from typing import Optional
import time
import re
from transformers import pipeline

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier
from app.verifiers.evidence_retriever import EvidenceRetriever
from app.verifiers.claim_generator import ClaimGenerator

class EvidenceVerifier(BaseVerifier):
    """Verifies an answer against retrieved evidence using NLI."""

    NLI_MODEL = "cross-encoder/nli-deberta-v3-small"

    def __init__(
        self,
        corpus_path: str = "data/evidence_corpus.json",
        top_k: int = 3,
        
    ) -> None:
        self.retriever = EvidenceRetriever(corpus_path=corpus_path)
        self.top_k = top_k
        self.claim_generator = ClaimGenerator()
        self.nli = pipeline(
            "text-classification",
            model=self.NLI_MODEL,
        )

    @property
    def name(self) -> str:
        return "evidence"
    def extract_relevant_sentences(
        self,
        text: str,
        claim: str,
        max_sentences: int = 3,
    ) -> str:
        """Extract sentences from evidence that are most relevant to the claim."""

        sentences = re.split(r"(?<=[.!?])\s+", text)

        claim_words = set(
            word.lower()
            for word in re.findall(r"\b\w+\b", claim)
        )

        scored_sentences = []

        for sentence in sentences:
            sentence_words = set(
                word.lower()
                for word in re.findall(r"\b\w+\b", sentence)
            )

            overlap = len(claim_words & sentence_words)

            if overlap > 0:
                scored_sentences.append(
                    (overlap, sentence.strip())
                )

        scored_sentences.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        selected = [
            sentence
            for _, sentence in scored_sentences[:max_sentences]
        ]

        if not selected:
            return text[:1500]

        return " ".join(selected)
    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        start_time = time.perf_counter()

        # Retrieve evidence using the question and answer.
        query = f"{question} {answer}"
        retrieved_evidence = self.retriever.retrieve(
            query,
            k=self.top_k,
        )

        if not retrieved_evidence:
            return VerificationResult(
                verifier_name=self.name,
                score=0.0,
                passed=False,
                reasoning="No evidence was retrieved.",
                metadata={
                    "top_k": self.top_k,
                    "latency_ms": round(
                        (time.perf_counter() - start_time) * 1000,
                        2,
                    ),
                },
            )

        claim = self.claim_generator.generate(question, answer)

        nli_results = []

        for evidence in retrieved_evidence:

            relevant_evidence = self.extract_relevant_sentences(
                evidence["text"],
                claim,
            )

            nli_result = self.nli(
                {
                    "text": relevant_evidence,
                    "text_pair": claim,
                }
            )

            nli_results.append(
                {
                    "evidence": evidence,
                    "relevant_evidence": relevant_evidence,
                    "label": nli_result["label"],
                    "score": float(nli_result["score"]),
                }
            )

        

                # Find evidence chunks that support the claim.
        entailments = [
            result
            for result in nli_results
            if result["label"] == "entailment"
        ]

        if entailments:
            # If any chunk supports the claim, use the
            # strongest supporting chunk.
            best_result = max(
                entailments,
                key=lambda result: result["score"],
            )
            passed = True
        else:
            # No retrieved chunk supports the claim.
            # Keep the strongest NLI result for reporting.
            best_result = max(
                nli_results,
                key=lambda result: result["score"],
            )
            passed = False

        best_evidence = best_result["evidence"]
        label = best_result["label"]
        nli_score = best_result["score"]

        # Store NLI results for every retrieved chunk.
        evaluated_evidence = [
            {
                "title": result["evidence"]["title"],
                "chunk_id": result["evidence"]["chunk_id"],
                "retrieval_score": result["evidence"]["score"],
                "nli_label": result["label"],
                "nli_score": result["score"],
            }
            for result in nli_results
        ]

        latency_ms = (time.perf_counter() - start_time) * 1000

        return VerificationResult(
            verifier_name=self.name,
            score=nli_score,
            passed=passed,
            reasoning=(
                f"NLI result: {label}. "
                f"Evidence: {best_evidence['title']}. "
                f"Claim: {claim}. "
                f"NLI confidence: {nli_score:.4f}."
            ),
            metadata={
                "nli_label": label,
                "nli_model": self.NLI_MODEL,
                "retrieval_score": best_evidence["score"],
                "evidence_title": best_evidence["title"],
                "evidence_chunk_id": best_evidence["chunk_id"],
                "top_k": self.top_k,
                "evaluated_evidence": evaluated_evidence,
                "latency_ms": round(latency_ms, 2),
            },
        )