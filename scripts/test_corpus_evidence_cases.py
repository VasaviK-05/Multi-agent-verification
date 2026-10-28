
import json
from pathlib import Path
from datetime import datetime, timezone

from app.verifiers.evidence_verifier import EvidenceVerifier


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "data" / "articles_13083.json"
OUTPUT_PATH = ROOT / "corpus_evidence_test_results.json"

# Format: (case_id, question, answer, expected_decision)
CASES = [
    # Correct answers
    ("C01", "When did the 1099 papal election take place?",
     "13 August 1099", "SUPPORT"),
    ("C02", "Who was elected pope in the 1099 papal election?",
     "Raniero, who took the name Paschal II", "SUPPORT"),
    ("C03", "When was Paschal II consecrated as Bishop of Rome?",
     "14 August 1099", "SUPPORT"),
    ("C04", "When did the 2014 Seattle Pacific University shooting occur?",
     "5 June 2014", "SUPPORT"),
    ("C05", "Where did the Seattle Pacific University shooting take place?",
     "Otto Miller Hall at Seattle Pacific University", "SUPPORT"),
    ("C06", "How many people were killed in the Seattle Pacific University shooting?",
     "One student", "SUPPORT"),
    ("C07", "What did Jon Meis use to subdue the gunman?",
     "Pepper spray", "SUPPORT"),
    ("C08", "When was the 1974 Toronto municipal election held?",
     "2 December 1974", "SUPPORT"),
    ("C09", "Who was re-elected Mayor of Toronto in 1974?",
     "David Crombie", "SUPPORT"),
    ("C10", "Approximately what percentage of the vote did David Crombie receive?",
     "83%", "SUPPORT"),
    ("C11", "What was the Green Bay Packers' regular-season record in 2012?",
     "11-5", "SUPPORT"),
    ("C12", "Which team defeated the Packers in the NFC Divisional Playoff Game?",
     "San Francisco 49ers", "SUPPORT"),
    ("C13", "What was the score of the Packers' divisional playoff loss?",
     "45-31", "SUPPORT"),
    ("C14", "In which country did the 2009 South American U-17 Championship take place?",
     "Chile", "SUPPORT"),
    ("C15", "What were the start and end dates of the 2009 South American U-17 Championship?",
     "17 April to 9 May 2009", "SUPPORT"),

    # Incorrect answers
    ("N01", "When did the 1099 papal election take place?",
     "13 August 1100", "REJECT"),
    ("N02", "Who was elected pope in 1099?",
     "Urban II", "REJECT"),
    ("N03", "When did the Seattle Pacific University shooting occur?",
     "5 June 2015", "REJECT"),
    ("N04", "How many people were killed in the Seattle Pacific University shooting?",
     "Three students", "REJECT"),
    ("N05", "Who was re-elected Mayor of Toronto in 1974?",
     "Mel Lastman", "REJECT"),
    ("N06", "What was the Packers' regular-season record in 2012?",
     "10-6", "REJECT"),
    ("N07", "Which team defeated the Packers in the divisional playoffs?",
     "Minnesota Vikings", "REJECT"),
    ("N08", "In which country did the 2009 South American U-17 Championship take place?",
     "Argentina", "REJECT"),
]


def main():
    if not CORPUS_PATH.exists():
        raise FileNotFoundError(f"Corpus not found: {CORPUS_PATH}")

    print(f"Corpus: {CORPUS_PATH}")
    print(f"Test cases: {len(CASES)}")
    print("Initializing EvidenceVerifier...")

    # Uses the existing index if the verifier determines it is current.
    verifier = EvidenceVerifier(corpus_path=CORPUS_PATH)

    results = []

    for case_id, question, answer, expected in CASES:
        print(f"\n[{case_id}] {question}")
        print(f"Answer: {answer}")

        row = {
            "case_id": case_id,
            "question": question,
            "answer": answer,
            "expected_decision": expected,
        }

        try:
            result = verifier.verify(question, answer)
            metadata = result.metadata or {}
            actual = metadata.get("decision", "UNKNOWN")

            row.update({
                "actual_decision": actual,
                "passed": actual == expected,
                "result_passed": result.passed,
                "nli_label": metadata.get("nli_label"),
                "reason": metadata.get("reason"),
                "claim_decisions": metadata.get("claim_decisions"),
                "evaluated_evidence": metadata.get("evaluated_evidence"),
            })

            print(f"Expected: {expected} | Actual: {actual}")
            print("MATCH" if row["passed"] else "MISMATCH")

        except Exception as exc:
            row.update({
                "actual_decision": "ERROR",
                "passed": False,
                "error": repr(exc),
            })
            print(f"ERROR: {exc}")

        results.append(row)

    matched = sum(r.get("passed", False) for r in results)
    total = len(results)

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "corpus": str(CORPUS_PATH),
        "total_cases": total,
        "matched_expected_decisions": matched,
        "decision_match_rate": matched / total if total else 0,
        "cases": results,
    }

    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print(f"Decision matches: {matched}/{total}")
    print(f"Match rate: {matched / total:.1%}" if total else "No cases")
    print(f"Results saved to: {OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
