
import json
from pathlib import Path

results_file = Path("real_ollama_evidence_results.json")

with results_file.open("r", encoding="utf-8") as f:
    data = json.load(f)


def find_cases(obj):
    """Find test-case dictionaries regardless of the outer JSON structure."""
    if isinstance(obj, dict):
        if any(k in obj for k in ("question", "case_id", "case")) and any(
            k in obj for k in ("verification", "answer", "ollama_answer")
        ):
            yield obj
        else:
            for value in obj.values():
                yield from find_cases(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_cases(item)


cases = list(find_cases(data))

for index, case in enumerate(cases, start=1):
    question = str(case.get("question", ""))

    # Inspect the Europa League cases: date, multi-part details, winner.
    if not any(term in question.lower() for term in (
        "europa league final",
    )):
        continue

    verification = case.get("verification", {})
    metadata = verification.get("metadata", {}) if isinstance(
        verification, dict
    ) else {}

    print("\n" + "=" * 90)
    print(f"CASE {index}")
    print("QUESTION:", question)
    print("ANSWER:", case.get("answer", case.get("ollama_answer")))
    print("FINAL STATUS:", verification.get("final_status"))
    print("SCORE:", verification.get("score"))

    print("\n--- CLAIM DECISIONS ---")
    print(json.dumps(metadata.get("claim_decisions", []), indent=2))

    print("\n--- DISCARDED EVIDENCE ---")
    print(json.dumps(metadata.get("discarded_evidence", []), indent=2))

    print("\n--- OTHER METADATA ---")
    print(json.dumps({
        key: value
        for key, value in metadata.items()
        if key not in ("claim_decisions", "discarded_evidence")
    }, indent=2))
