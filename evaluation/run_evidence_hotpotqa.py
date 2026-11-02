
import json
import os
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.verifiers.evidence_retriever import EvidenceRetriever
from app.verifiers.evidence_verifier import EvidenceVerifier


DATASET_PATH = ROOT / "evaluation" / "datasets" / "unified" / "development.json"
RESULTS_DIR = ROOT / "evaluation" / "results"
OUTPUT_JSON = RESULTS_DIR / "evidence_hotpotqa_results.json"
OUTPUT_CSV = RESULTS_DIR / "evidence_hotpotqa_results.csv"

# Start with 5 examples. Change to None to evaluate all examples.
MAX_EXAMPLES = 50

# Keep the existing production verifier thresholds unchanged.
TOP_K = 3


def load_hotpotqa():
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        rows = json.load(f)

    return [
        row for row in rows
        if row.get("benchmark") == "HotpotQA"
    ]


def build_example_corpus(example, corpus_path):
    """
    Convert this example's HotpotQA context into the article schema
    expected by EvidenceRetriever.

    Only this example's context is included to prevent cross-example
    evidence leakage.
    """
    articles = []

    for index, paragraph in enumerate(example.get("context", [])):
        title = str(paragraph.get("title", "")).strip()
        text = str(paragraph.get("text", "")).strip()

        if not title or not text:
            continue

        articles.append({
            "id": f"{example['id']}_{index}",
            "title": title,
            "text": text,
            "url": ""
        })

    if not articles:
        raise ValueError(
            f"No usable context paragraphs for example {example.get('id')}"
        )

    with corpus_path.open("w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    return articles


def get_decision(result):
    metadata = result.metadata or {}

    decision = metadata.get("decision")

    if decision in {"SUPPORT", "REJECT", "UNSURE"}:
        return decision

    # Fallback for older result formats.
    if result.passed:
        return "SUPPORT"

    return "UNSURE"


def evaluate_candidate(verifier, example, candidate):
    answer = str(candidate.get("answer", "")).strip()
    expected_correct = bool(candidate.get("expected_correct", False))

    start = time.perf_counter()

    result = verifier.verify(
        question=example["question"],
        answer=answer,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000

    metadata = result.metadata or {}
    decision = get_decision(result)

    # SUPPORT is a positive prediction.
    # REJECT is a negative prediction.
    # UNSURE is abstention and is not forced into either class.
    covered = decision in {"SUPPORT", "REJECT"}

    prediction_correct = None
    if covered:
        prediction_correct = (
            (decision == "SUPPORT" and expected_correct)
            or (decision == "REJECT" and not expected_correct)
        )

    retrieved = metadata.get("retrieved_evidence", [])
    evaluated = metadata.get("evaluated_evidence", [])

    # Evidence metadata field names may vary by implementation.
    # Preserve the full metadata so no trace information is lost.
    return {
        "example_id": example.get("id"),
        "question": example["question"],
        "answer": answer,
        "expected_correct": expected_correct,
        "decision": decision,
        "score": float(result.score),
        "passed": bool(result.passed),
        "covered": covered,
        "prediction_correct": prediction_correct,
        "latency_ms": round(elapsed_ms, 3),
        "reasoning": result.reasoning,
        "evidence_title": metadata.get("evidence_title"),
        "retrieval_score": metadata.get("retrieval_score"),
        "best_retrieval_score": metadata.get("best_retrieval_score"),
        "nli_label": metadata.get("nli_label"),
        "retrieved_evidence": retrieved,
        "evaluated_evidence": evaluated,
        "supporting_evidence": metadata.get("supporting_evidence", []),
        "contradicting_evidence": metadata.get("contradicting_evidence", []),
        "discarded_evidence": metadata.get("discarded_evidence", []),
        "claim_decisions": metadata.get("claim_decisions", []),
        "full_metadata": metadata,
    }


def calculate_metrics(results):
    total = len(results)

    if total == 0:
        return {}

    covered = [r for r in results if r["covered"]]
    abstained = [r for r in results if not r["covered"]]

    correct = [
        r for r in covered
        if r["prediction_correct"] is True
    ]

    incorrect = [
        r for r in covered
        if r["prediction_correct"] is False
    ]

    false_accepts = [
        r for r in results
        if not r["expected_correct"] and r["decision"] == "SUPPORT"
    ]

    incorrect_candidates = [
        r for r in results if not r["expected_correct"]
    ]

    latencies = [r["latency_ms"] for r in results]

    return {
        "benchmark": "HotpotQA",
        "verifier": "EvidenceVerifier",
        "examples": len(set(r["example_id"] for r in results)),
        "candidate_predictions": total,
        "covered_predictions": len(covered),
        "abstained_predictions": len(abstained),
        "coverage": round(len(covered) / total, 4),
        "selective_accuracy": (
            round(len(correct) / len(covered), 4)
            if covered else None
        ),
        "false_acceptances": len(false_accepts),
        "false_acceptance_rate": (
            round(len(false_accepts) / len(incorrect_candidates), 4)
            if incorrect_candidates else None
        ),
        "average_latency_ms": round(sum(latencies) / total, 3),
        "decision_counts": dict(Counter(r["decision"] for r in results)),
        "expected_correct_count": sum(
            1 for r in results if r["expected_correct"]
        ),
        "expected_incorrect_count": sum(
            1 for r in results if not r["expected_correct"]
        ),
        "covered_correct": len(correct),
        "covered_incorrect": len(incorrect),
    }


def save_csv(results):
    import csv

    fields = [
        "example_id",
        "question",
        "answer",
        "expected_correct",
        "decision",
        "score",
        "covered",
        "prediction_correct",
        "latency_ms",
        "evidence_title",
        "retrieval_score",
        "best_retrieval_score",
        "nli_label",
        "reasoning",
    ]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for row in results:
            writer.writerow({
                field: row.get(field)
                for field in fields
            })


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    examples = load_hotpotqa()

    if MAX_EXAMPLES is not None:
        examples = examples[:MAX_EXAMPLES]

    print(f"HotpotQA examples selected: {len(examples)}")
    print("Building isolated context corpora and running EvidenceVerifier...\n")

    all_results = []
    errors = []

    with tempfile.TemporaryDirectory(
        prefix="hotpotqa_evidence_"
    ) as temporary_directory:

        temp_root = Path(temporary_directory)

        for index, example in enumerate(examples, start=1):
            example_id = str(example.get("id", f"example_{index}"))

            print(
                f"[{index}/{len(examples)}] "
                f"Processing {example_id}"
            )

            example_dir = temp_root / f"example_{index}"
            example_dir.mkdir(parents=True, exist_ok=True)

            corpus_path = example_dir / "corpus.json"
            index_dir = example_dir / "evidence_index"

            try:
                articles = build_example_corpus(
                    example,
                    corpus_path,
                )

                # Build a separate retriever and FAISS index for this example.
                retriever = EvidenceRetriever(
                    corpus_path=str(corpus_path),
                    index_dir=str(index_dir),
                )

                verifier = EvidenceVerifier(
                    retriever=retriever,
                    top_k=TOP_K,
                )

                candidates = example.get("candidate_answers", [])

                for candidate in candidates:
                    row = evaluate_candidate(
                        verifier,
                        example,
                        candidate,
                    )

                    row["context_article_count"] = len(articles)
                    all_results.append(row)

                    print(
                        f"  {row['decision']:<8} "
                        f"expected_correct={row['expected_correct']} "
                        f"latency={row['latency_ms']:.2f} ms"
                    )

                # Release references before processing the next example.
                del verifier
                del retriever

            except Exception as exc:
                errors.append({
                    "example_id": example_id,
                    "error": repr(exc),
                })

                print(f"  ERROR: {exc}")

    metrics = calculate_metrics(all_results)

    output = {
        "experiment": "Evidence Verifier on HotpotQA",
        "dataset": str(DATASET_PATH.relative_to(ROOT)),
        "max_examples": MAX_EXAMPLES,
        "top_k": TOP_K,
        "corpus_policy": (
            "Each example uses only its own HotpotQA context paragraphs."
        ),
        "metrics": metrics,
        "errors": errors,
        "results": all_results,
    }

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    save_csv(all_results)

    print("\n" + "=" * 55)
    print("EVIDENCE VERIFIER - HOTPOTQA RESULTS")
    print("=" * 55)

    print(json.dumps(metrics, indent=2))

    print(f"\nErrors: {len(errors)}")
    print(f"JSON: {OUTPUT_JSON}")
    print(f"CSV:  {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
