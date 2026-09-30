"""Evidence-based verifier using FAISS retrieval and NLI.""" 

from typing import Optional
import time

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

        best_evidence = retrieved_evidence[0]

        claim = self.claim_generator.generate(question, answer)

        nli_result = self.nli(
            {
                "text": best_evidence["text"],
                "text_pair": claim,
            }
        )

        label = nli_result["label"]
        nli_score = float(nli_result["score"])

        passed = label == "entailment"

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
                "latency_ms": round(latency_ms, 2),
            },
        )