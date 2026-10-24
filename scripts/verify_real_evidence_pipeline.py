import json
import tempfile
from pathlib import Path

from app.verifiers.evidence_retriever import EvidenceRetriever
from app.verifiers.evidence_verifier import EvidenceVerifier

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "articles_13083.json"

CASES = [
    {
        "name": "Known answer: Hamlet",
        "question": "Who wrote Hamlet?",
        "answer": "William Shakespeare",
    },
    {
        "name": "Wrong answer: Hamlet",
        "question": "Who wrote Hamlet?",
        "answer": "Charles Dickens",
    },
    {
        "name": "Known answer: France",
        "question": "What is the capital of France?",
        "answer": "Paris",
    },
    {
        "name": "Wrong answer: France",
        "question": "What is the capital of France?",
        "answer": "London",
    },
    {
        "name": "Potentially unsupported topic",
        "question": "What is the capital of Atlantis?",
        "answer": "Poseidon City",
    },
]

def main():
    print("=" * 72)
    print("REAL EVIDENCE RETRIEVAL + REAL NLI DIAGNOSTIC")
    print("=" * 72)

    if not CORPUS.is_file():
        raise FileNotFoundError(f"Corpus not found: {CORPUS}")

    print("Corpus:", CORPUS)
    print("Corpus size:", f"{CORPUS.stat().st_size:,}", "bytes")

    # A fresh temporary index forces the real retriever to rebuild
    # its chunks and vector index from the selected corpus.
    with tempfile.TemporaryDirectory(prefix="real_evidence_check_") as temp:
        index_dir = Path(temp) / "fresh_index"

        print("\nBuilding a fresh index from the real corpus...")
        retriever = EvidenceRetriever(
            corpus_path=str(CORPUS),
            index_dir=str(index_dir),
        )

        print("Index directory:", retriever.index_dir)
        print("Chunk count:", len(retriever.chunks))
        print("FAISS vector count:", retriever.index.ntotal)
        print("Embedding model:", retriever.EMBEDDING_MODEL)
        print("Corpus version:", retriever.corpus_version)
        print("Index version:", retriever.index_version)

        assert len(retriever.chunks) > 0, "No chunks were created"
        assert retriever.index.ntotal == len(retriever.chunks), (
            "FAISS vector count does not match chunk count"
        )

        print("\nLoading the real EvidenceVerifier and NLI model...")
        verifier = EvidenceVerifier(retriever=retriever)

        print("Verifier:", verifier.name)
        print("NLI model:", verifier.NLI_MODEL)
        print("NLI implementation:", type(verifier.nli).__name__)

        for case in CASES:
            print("\n" + "=" * 72)
            print("CASE:", case["name"])
            print("Question:", case["question"])
            print("Answer:", case["answer"])

            # Inspect actual retrieval from the newly built index.
            retrieved = retriever.retrieve(case["question"], k=5)
            print("\nTOP RETRIEVED REAL CORPUS CHUNKS:")
            for i, item in enumerate(retrieved, start=1):
                print(json.dumps({
                    "rank": i,
                    "title": item.get("title"),
                    "score": item.get("score"),
                    "chunk_id": item.get("chunk_id"),
                    "text_excerpt": str(item.get("text", ""))[:500],
                }, ensure_ascii=False))

            # This invokes the verifier's own retrieval, gates,
            # premise extraction, real NLI, and aggregation.
            result = verifier.verify(
                question=case["question"],
                answer=case["answer"],
            )
            metadata = result.metadata

            print("\nVERIFIER RESULT:")
            print(json.dumps({
                "passed": result.passed,
                "score": result.score,
                "decision": metadata.get("decision"),
                "nli_label": metadata.get("nli_label"),
                "unsure_reason": metadata.get("unsure_reason"),
                "evaluated_evidence_count": len(
                    metadata.get("evaluated_evidence", [])
                ),
                "discarded_evidence_count": len(
                    metadata.get("discarded_evidence", [])
                ),
                "claim_decisions": metadata.get("claim_decisions", []),
                "evaluated_evidence": metadata.get("evaluated_evidence", []),
                "discarded_evidence": metadata.get("discarded_evidence", []),
            }, indent=2, ensure_ascii=False, default=str))

        print("\n" + "=" * 72)
        print("DIAGNOSTIC COMPLETED")
        print("All retrieval and verification calls used real components.")
        print("The temporary rebuilt index will now be removed.")
        print("=" * 72)

if __name__ == "__main__":
    main()
