"""
Broader evidence benchmark for the Multi-agent-verification project.

Run from repository root:
    .\.venv\Scripts\python.exe -m scripts.test_broader_evidence_cases

This script does not edit the verifier, corpus, index, or existing result files.
It creates a new JSON result file. Validate labels and corpus coverage before
using its scores as research results.
"""
from __future__ import annotations
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "corpus_evidence_broader_results.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from app.verifiers.evidence_verifier import EvidenceVerifier
except Exception as exc:
    raise SystemExit(
        "Could not import EvidenceVerifier. Run from the repository root "
        "using the project's virtual environment. Import error: " + str(exc)
    )

# Proposed expected labels; independently verify corpus coverage and labels.
# M-series are rule/pipeline tests, not corpus-only evidence tests.
CASES: list[dict[str, Any]] = [
# Direct factual support (15)
("F01","direct_support","What is the capital of Australia?","Canberra","SUPPORT",True),
("F02","direct_support","What is the capital of Japan?","Tokyo","SUPPORT",True),
("F03","direct_support","What is the chemical symbol for gold?","Au","SUPPORT",True),
("F04","direct_support","What is the chemical symbol for silver?","Ag","SUPPORT",True),
("F05","direct_support","Which planet is known as the Red Planet?","Mars","SUPPORT",True),
("F06","direct_support","What is the largest ocean on Earth?","Pacific Ocean","SUPPORT",True),
("F07","direct_support","What is the primary gas in Earth's atmosphere?","Nitrogen","SUPPORT",True),
("F08","direct_support","Which continent contains the Sahara Desert?","Africa","SUPPORT",True),
("F09","direct_support","Which planet is closest to the Sun?","Mercury","SUPPORT",True),
("F10","direct_support","Which country is Paris the capital of?","France","SUPPORT",True),
("F11","direct_support","What is the hardest naturally occurring mineral on the Mohs scale?","Diamond","SUPPORT",True),
("F12","direct_support","What is the currency of the United Kingdom?","Pound sterling","SUPPORT",True),
("F13","direct_support","Which gas do plants absorb during photosynthesis?","Carbon dioxide","SUPPORT",True),
("F14","direct_support","What is the largest mammal known to have lived on Earth?","Blue whale","SUPPORT",True),
("F15","direct_support","What is the SI unit of force?","Newton","SUPPORT",True),

# Contradictions (15)
("C01","contradiction","What is the capital of Australia?","Sydney","REJECT",True),
("C02","contradiction","What is the capital of Japan?","Osaka","REJECT",True),
("C03","contradiction","What is the chemical symbol for gold?","Ag","REJECT",True),
("C04","contradiction","What is the chemical symbol for silver?","Au","REJECT",True),
("C05","contradiction","Which planet is known as the Red Planet?","Venus","REJECT",True),
("C06","contradiction","What is the largest ocean on Earth?","Atlantic Ocean","REJECT",True),
("C07","contradiction","What is the primary gas in Earth's atmosphere?","Oxygen","REJECT",True),
("C08","contradiction","Which continent contains the Sahara Desert?","South America","REJECT",True),
("C09","contradiction","Which planet is closest to the Sun?","Venus","REJECT",True),
("C10","contradiction","Which country is Paris the capital of?","Italy","REJECT",True),
("C11","contradiction","What is the SI unit of force?","Joule","REJECT",True),
("C12","contradiction","What is the currency of the United Kingdom?","Euro","REJECT",True),
("C13","contradiction","Which gas do plants absorb during photosynthesis?","Oxygen","REJECT",True),
("C14","contradiction","What is the hardest naturally occurring mineral on the Mohs scale?","Talc","REJECT",True),
("C15","contradiction","What is the largest mammal known to have lived on Earth?","African elephant","REJECT",True),

# Paraphrases (10)
("P01","paraphrase","What is the capital of Australia?","Australia's capital city is Canberra.","SUPPORT",True),
("P02","paraphrase","What is the chemical symbol for gold?","Gold is represented by Au.","SUPPORT",True),
("P03","paraphrase","Which planet is known as the Red Planet?","Mars is commonly called the Red Planet.","SUPPORT",True),
("P04","paraphrase","What is the largest ocean on Earth?","The Pacific is Earth's largest ocean.","SUPPORT",True),
("P05","paraphrase","What is the primary gas in Earth's atmosphere?","Most of Earth's atmosphere consists of nitrogen.","SUPPORT",True),
("P06","paraphrase","Which country is Paris the capital of?","Paris serves as France's capital.","SUPPORT",True),
("P07","paraphrase","What is the chemical symbol for silver?","Ag is the element symbol assigned to silver.","SUPPORT",True),
("P08","paraphrase","Which planet is closest to the Sun?","Mercury is the nearest planet to the Sun.","SUPPORT",True),
("P09","paraphrase","What is the SI unit of force?","Force is measured in newtons in the SI system.","SUPPORT",True),
("P10","paraphrase","Which gas do plants absorb during photosynthesis?","Plants take in carbon dioxide for photosynthesis.","SUPPORT",True),

# Numeric/property alignment (15)
("N01","numeric_property","How many days are in a standard week?","7","SUPPORT",True),
("N02","numeric_property","How many days are in a standard week?","8","REJECT",True),
("N03","numeric_property","How many months are in a calendar year?","12","SUPPORT",True),
("N04","numeric_property","How many months are in a calendar year?","10","REJECT",True),
("N05","numeric_property","How many degrees are in a right angle?","90 degrees","SUPPORT",True),
("N06","numeric_property","How many degrees are in a right angle?","180 degrees","REJECT",True),
("N07","numeric_property","How many sides does a hexagon have?","6","SUPPORT",True),
("N08","numeric_property","How many sides does a hexagon have?","8","REJECT",True),
("N09","numeric_property","At standard atmospheric pressure, what is water's boiling point in Celsius?","100°C","SUPPORT",True),
("N10","numeric_property","At standard atmospheric pressure, what is water's boiling point in Celsius?","50°C","REJECT",True),
("N11","numeric_property","How many minutes are in one hour?","60","SUPPORT",True),
("N12","numeric_property","How many minutes are in one hour?","100","REJECT",True),
("N13","numeric_property","How many centimeters are in one meter?","100","SUPPORT",True),
("N14","numeric_property","How many centimeters are in one meter?","10","REJECT",True),
("N15","numeric_property","How many sides does a triangle have?","3","SUPPORT",True),

# Entity/event disambiguation (10)
("E01","entity_disambiguation","Which country is Paris the capital of?","France","SUPPORT",True),
("E02","entity_disambiguation","Which country is Paris the capital of?","Texas","REJECT",True),
("E03","entity_disambiguation","Which planet is closest to the Sun?","Mercury","SUPPORT",True),
("E04","entity_disambiguation","Which planet is closest to the Sun?","Mars","REJECT",True),
("E05","entity_disambiguation","Which ocean lies between Africa and Australia?","Indian Ocean","SUPPORT",True),
("E06","entity_disambiguation","Which ocean lies between Africa and Australia?","Arctic Ocean","REJECT",True),
("E07","entity_disambiguation","Which continent contains the Sahara Desert?","Africa","SUPPORT",True),
("E08","entity_disambiguation","Which continent contains the Sahara Desert?","Asia","REJECT",True),
("E09","entity_disambiguation","What is the capital of Georgia, the country in the Caucasus?","Tbilisi","SUPPORT",True),
("E10","entity_disambiguation","What is the capital of Georgia, the country in the Caucasus?","Atlanta","REJECT",True),

# Extra temporal / scientific fact alignment cases (5)
("D01","date_fact_alignment","In what year did World War II end?","1945","SUPPORT",True),
("D02","date_fact_alignment","In what year did World War II end?","1944","REJECT",True),
("D03","date_fact_alignment","In what year did the first crewed Moon landing occur?","1969","SUPPORT",True),
("D04","date_fact_alignment","In what year did the first crewed Moon landing occur?","1972","REJECT",True),
("D05","date_fact_alignment","How many planets are recognized in the Solar System?","8","SUPPORT",True),

# Multi-hop arithmetic: pipeline/rule-verifier cases, not corpus-only tests (10)
("M01","multi_hop_pipeline","A book costs ₹200 and another costs ₹150. What is their total cost?","₹350","SUPPORT",False),
("M02","multi_hop_pipeline","A book costs ₹200 and another costs ₹150. What is their total cost?","₹300","REJECT",False),
("M03","multi_hop_pipeline","A meeting starts at 10:00 and lasts 90 minutes. When does it end?","11:30","SUPPORT",False),
("M04","multi_hop_pipeline","A meeting starts at 10:00 and lasts 90 minutes. When does it end?","11:00","REJECT",False),
("M05","multi_hop_pipeline","A box contains 4 rows of 6 items. How many items are there?","24","SUPPORT",False),
("M06","multi_hop_pipeline","A box contains 4 rows of 6 items. How many items are there?","20","REJECT",False),
("M07","multi_hop_pipeline","A train travels 120 km in 2 hours at constant speed. What is its speed?","60 km/h","SUPPORT",False),
("M08","multi_hop_pipeline","A train travels 120 km in 2 hours at constant speed. What is its speed?","40 km/h","REJECT",False),
("M09","multi_hop_pipeline","A rectangle is 8 cm long and 3 cm wide. What is its area?","24 square cm","SUPPORT",False),
("M10","multi_hop_pipeline","A rectangle is 8 cm long and 3 cm wide. What is its area?","22 square cm","REJECT",False),

# Insufficient evidence: confirm corpus does not contain relevant evidence (10)
("U01","insufficient_evidence","What was the exact temperature inside a particular room at 2:17 PM yesterday?","23°C","UNSURE",True),
("U02","insufficient_evidence","What was the serial number of an unspecified laptop?","SN-847291","UNSURE",True),
("U03","insufficient_evidence","What was the exact number of visitors to an unspecified website last Tuesday?","14,287","UNSURE",True),
("U04","insufficient_evidence","What was the middle name of an unspecified person's grandfather?","James","UNSURE",True),
("U05","insufficient_evidence","What was the precise weight of an unspecified parcel before shipping?","2.45 kg","UNSURE",True),
("U06","insufficient_evidence","What was the exact battery percentage of an unspecified phone at noon yesterday?","73%","UNSURE",True),
("U07","insufficient_evidence","What was the exact number of people in an unspecified office at 9:05 AM?","18","UNSURE",True),
("U08","insufficient_evidence","What was the exact private Wi-Fi password of an unspecified household?","bluebird123","UNSURE",True),
("U09","insufficient_evidence","What was the exact amount in an unspecified person's bank account yesterday?","₹42,000","UNSURE",True),
("U10","insufficient_evidence","What was the exact serial number printed on an unspecified parcel?","PKG-009177","UNSURE",True),

# Multi-claim answers (10)
("X01","multi_claim","State the capital of Australia and the capital of Japan.","Canberra and Tokyo","SUPPORT",True),
("X02","multi_claim","State the capital of Australia and the capital of Japan.","Canberra and Osaka","REJECT",True),
("X03","multi_claim","Give the chemical symbols for gold and silver.","Au and Ag","SUPPORT",True),
("X04","multi_claim","Give the chemical symbols for gold and silver.","Au and Si","REJECT",True),
("X05","multi_claim","Name the Red Planet and the planet closest to the Sun.","Mars and Mercury","SUPPORT",True),
("X06","multi_claim","Name the Red Planet and the planet closest to the Sun.","Mars and Venus","REJECT",True),
("X07","multi_claim","Give the capital of France and the capital of Italy.","Paris and Rome","SUPPORT",True),
("X08","multi_claim","Give the capital of France and the capital of Italy.","Paris and Milan","REJECT",True),
("X09","multi_claim","Give the SI units for force and energy.","Newton and joule","SUPPORT",True),
("X10","multi_claim","Give the SI units for force and energy.","Joule and watt","REJECT",True),
]
CASES = [
    {"case_id": i, "category": cat, "question": q, "answer": a,
     "expected_decision": expected, "coverage_review_required": coverage,
     "note": "Proposed label; independently validate. " +
             ("Corpus coverage must be checked." if coverage else
              "Pipeline/rule-verifier test; not a corpus-only evidence test.")}
    for i, (cid, cat, q, a, expected, coverage) in enumerate(CASES, start=1)
    for _ in [0]
    for i in [{"case_id": cid, "category": cat, "question": q, "answer": a,
               "expected_decision": expected, "coverage_review_required": coverage,
               "note": "Proposed label; independently validate. " +
                       ("Corpus coverage must be checked." if coverage else
                        "Pipeline/rule-verifier test; not a corpus-only evidence test.")}]
]


def decision_of(result: Any) -> str:
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    elif hasattr(result, "dict"):
        result = result.dict()
    if isinstance(result, dict):
        for key in ("final_status", "decision", "status", "final_decision", "label"):
            if key in result:
                value = result[key]
                value = getattr(value, "value", value)
                value = str(value).strip().upper()
                aliases = {"SUPPORTED": "SUPPORT", "PASS": "SUPPORT",
                           "PASSED": "SUPPORT", "REJECTED": "REJECT",
                           "CONTRADICTION": "REJECT", "CONTRADICT": "REJECT",
                           "FAIL": "REJECT", "FAILED": "REJECT",
                           "ABSTAIN": "UNSURE", "ABSTAINED": "UNSURE",
                           "INCONCLUSIVE": "UNSURE", "UNKNOWN": "UNSURE"}
                return aliases.get(value, value)
    return "UNKNOWN"


def jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
        return value
    return repr(value)


def safe_div(a: int, b: int):
    return round(a / b, 4) if b else None


def main():
    print(f"Cases: {len(CASES)}")
    print(f"Output: {OUTPUT}")
    try:
        verifier = EvidenceVerifier()
    except TypeError as exc:
        raise SystemExit(
            "EvidenceVerifier() requires constructor arguments in this repo. "
            "Inspect its __init__ and adapt the construction line only. Error: " + str(exc)
        )
    rows = []
    for n, case in enumerate(CASES, 1):
        started = time.perf_counter()
        error = None
        raw = None
        try:
            try:
                raw = verifier.verify(question=case["question"], answer=case["answer"], context=None)
            except TypeError:
                raw = verifier.verify(case["question"], case["answer"], None)
            actual = decision_of(raw)
        except Exception as exc:
            actual = "ERROR"
            error = f"{type(exc).__name__}: {exc}"
        row = {
            **case,
            "actual_decision": actual,
            "matched_expected": actual == case["expected_decision"],
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            "error": error,
            "raw_result": jsonable(raw),
            "corpus_coverage_status": "REVIEW_REQUIRED" if case["coverage_review_required"] else "NOT_APPLICABLE_PIPELINE_CASE",
        }
        rows.append(row)
        status = "MATCH" if row["matched_expected"] else "MISMATCH"
        if actual == "ERROR":
            status = "ERROR"
        print(f"[{n:03}/{len(CASES)}] {case['case_id']} expected={case['expected_decision']} actual={actual} {status}")
        if error:
            print("   ", error)

    valid = [r for r in rows if r["actual_decision"] not in {"ERROR", "UNKNOWN"}]
    labels = ["SUPPORT", "REJECT", "UNSURE"]
    confusion = {
        exp: {pred: sum(r["expected_decision"] == exp and r["actual_decision"] == pred for r in valid)
              for pred in labels}
        for exp in labels
    }
    class_metrics = {}
    for label in labels:
        tp = sum(r["expected_decision"] == label and r["actual_decision"] == label for r in valid)
        fp = sum(r["expected_decision"] != label and r["actual_decision"] == label for r in valid)
        fn = sum(r["expected_decision"] == label and r["actual_decision"] != label for r in valid)
        class_metrics[label] = {
            "precision": safe_div(tp, tp + fp), "recall": safe_div(tp, tp + fn),
            "true_positive": tp, "false_positive": fp, "false_negative": fn
        }
    per_category = {}
    for cat in sorted({r["category"] for r in rows}):
        group = [r for r in rows if r["category"] == cat]
        scored = [r for r in group if r["actual_decision"] not in {"ERROR", "UNKNOWN"}]
        correct = sum(r["matched_expected"] for r in scored)
        per_category[cat] = {
            "total": len(group), "scored": len(scored), "correct": correct,
            "accuracy": safe_div(correct, len(scored)),
            "unsure_count": sum(r["actual_decision"] == "UNSURE" for r in group),
            "errors": sum(r["actual_decision"] == "ERROR" for r in group),
        }

    summary = {
        "total_cases": len(rows), "scored_cases": len(valid),
        "matched_expected_decisions": sum(r["matched_expected"] for r in valid),
        "decision_match_rate": safe_div(sum(r["matched_expected"] for r in valid), len(valid)),
        "unsure_count": sum(r["actual_decision"] == "UNSURE" for r in rows),
        "unsure_rate": safe_div(sum(r["actual_decision"] == "UNSURE" for r in rows), len(rows)),
        "errors": sum(r["actual_decision"] == "ERROR" for r in rows),
        "unknown_decisions": sum(r["actual_decision"] == "UNKNOWN" for r in rows),
        "class_metrics": class_metrics,
        "confusion_matrix_rows_expected_columns_predicted": confusion,
        "per_category": per_category,
        "coverage_review_required": sum(r["coverage_review_required"] for r in rows),
        "pipeline_cases_not_applicable_to_corpus_coverage": sum(not r["coverage_review_required"] for r in rows),
    }
    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_name": "broader_evidence_cases",
        "warning": "Labels are proposed, not independently adjudicated. Check corpus coverage before treating accuracy as research evidence. Multi-hop arithmetic cases are pipeline/rule-verifier cases.",
        "summary": summary,
        "cases": rows,
    }
    try:
        with OUTPUT.open("x", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        output_used = OUTPUT
    except FileExistsError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_used = OUTPUT.with_name(f"corpus_evidence_broader_results_{timestamp}.json")
        with output_used.open("x", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\nSaved: {output_used}")
    print(f"Matched: {summary['matched_expected_decisions']}/{summary['scored_cases']} ({summary['decision_match_rate']})")
    print(f"UNSURE: {summary['unsure_count']}/{summary['total_cases']} ({summary['unsure_rate']})")
    print(f"Errors: {summary['errors']}")
    print("\nPer category:")
    for cat, m in per_category.items():
        print(f"  {cat}: {m['correct']}/{m['scored']} accuracy={m['accuracy']} unsure={m['unsure_count']} errors={m['errors']}")
    print("\nConfusion matrix (rows expected, columns predicted):")
    print("             SUPPORT REJECT UNSURE")
    for label in labels:
        row = confusion[label]
        print(f"{label:10s} {row['SUPPORT']:7d} {row['REJECT']:6d} {row['UNSURE']:6d}")


if __name__ == "__main__":
    main()
