
import csv
import json
import sys
import time
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.verifiers.rule_verifier import RuleVerifier

DATA_PATH = ROOT / "evaluation" / "datasets" / "unified" / "development.json"
RESULT_DIR = ROOT / "evaluation" / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = RESULT_DIR / "rule_gsm8k_results.json"
OUTPUT_CSV = RESULT_DIR / "rule_gsm8k_results.csv"

with DATA_PATH.open("r", encoding="utf-8") as f:
    records = json.load(f)

records = [
    row for row in records
    if row.get("benchmark") == "GSM8K"
]

verifier = RuleVerifier()

results = []
decision_counts = Counter()
rule_counts = Counter()

correct_predictions = 0
covered_predictions = 0
total_predictions = 0
total_latency = 0.0

for row in records:
    question = row["question"]

    for candidate in row.get("candidate_answers", []):
        answer = str(candidate["answer"])
        expected_correct = bool(candidate["expected_correct"])

        start = time.perf_counter()

        result = verifier.verify(
            question=question,
            answer=answer,
            context=None
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        metadata = result.metadata or {}
        decision = metadata.get("decision", "UNSURE")
        rule = metadata.get("rule", "unknown")

        decision_counts[decision] += 1
        rule_counts[rule] += 1

        # Unsupported/UNSURE examples are abstentions.
        covered = (
            rule != "unsupported"
            and decision in ("SUPPORT", "REJECT")
        )

        prediction_correct = (
            (decision == "SUPPORT" and expected_correct)
            or
            (decision == "REJECT" and not expected_correct)
        )

        if covered:
            covered_predictions += 1
            if prediction_correct:
                correct_predictions += 1

        total_predictions += 1
        total_latency += elapsed_ms

        results.append({
            "id": row["id"],
            "question": question,
            "candidate_answer": answer,
            "expected_correct": expected_correct,
            "decision": decision,
            "rule": rule,
            "rule_kind": metadata.get("rule_kind"),
            "covered": covered,
            "prediction_correct": (
                prediction_correct if covered else None
            ),
            "latency_ms": round(elapsed_ms, 3),
            "reasoning": result.reasoning,
        })

coverage = (
    covered_predictions / total_predictions
    if total_predictions else 0
)

selective_accuracy = (
    correct_predictions / covered_predictions
    if covered_predictions else 0
)

summary = {
    "benchmark": "GSM8K",
    "verifier": "RuleVerifier",
    "examples": len(records),
    "candidate_predictions": total_predictions,
    "covered_predictions": covered_predictions,
    "abstained_predictions": total_predictions - covered_predictions,
    "coverage": round(coverage, 4),
    "selective_accuracy": round(selective_accuracy, 4),
    "average_latency_ms": round(
        total_latency / total_predictions, 3
    ) if total_predictions else 0,
    "decision_counts": dict(decision_counts),
    "rule_counts": dict(rule_counts),
    "note": (
        "Selective accuracy is calculated only on covered predictions. "
        "Unsupported cases are counted as abstentions, not incorrect answers."
    )
}

with OUTPUT_JSON.open("w", encoding="utf-8") as f:
    json.dump(
        {"summary": summary, "results": results},
        f,
        indent=2,
        ensure_ascii=False
    )

if results:
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(results[0].keys())
        )
        writer.writeheader()
        writer.writerows(results)

print("\n========== RULE VERIFIER: GSM8K BASELINE ==========")
print(json.dumps(summary, indent=2))
print("\nSaved:", OUTPUT_JSON)
print("Saved:", OUTPUT_CSV)
