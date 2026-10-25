
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "corpus_evidence_test_results.json"
OUTPUT = ROOT / "corpus_evidence_failure_details.txt"

data = json.loads(RESULTS.read_text(encoding="utf-8"))
lines = []

for case in data["cases"]:
    if case.get("expected_decision") == case.get("actual_decision"):
        continue

    lines.append("=" * 100)
    lines.append(f'CASE: {case["case_id"]}')
    lines.append(f'Question: {case["question"]}')
    lines.append(f'Answer: {case["answer"]}')
    lines.append(
        f'Expected: {case.get("expected_decision")} | '
        f'Actual: {case.get("actual_decision")}'
    )

    for field in (
        "nli_label",
        "reason",
        "claim_decisions",
        "evaluated_evidence",
    ):
        lines.append(f"\n{field.upper()}:")

        value = case.get(field)
        lines.append(
            json.dumps(value, indent=2, ensure_ascii=False)
            if value is not None
            else "Not available in saved results"
        )

    lines.append("")

OUTPUT.write_text("\n".join(lines), encoding="utf-8")

print(f"Failed cases: {sum(c.get('expected_decision') != c.get('actual_decision') for c in data['cases'])}")
print(f"Full details saved to:\n{OUTPUT}")
print(f"File size: {OUTPUT.stat().st_size:,} bytes")
