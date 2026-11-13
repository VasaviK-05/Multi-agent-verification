"""Audit stored GSM8K and HotpotQA candidates against local benchmark sources.

The audit is conservative: matching the benchmark gold verifies source
provenance, but synthetic negatives remain unresolved without independent
adjudication. No files are modified.

Run from the repository root with its virtual environment:
    .venv/Scripts/python.exe evaluation/data_preparation/audit_candidate_answers.py
"""

from __future__ import annotations

import collections
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from datasets import load_from_disk


ROOT = Path(__file__).resolve().parents[2]
PARTITIONS = ("history", "development", "final_test")
GSM_FINAL = re.compile(r"####\s*(-?[\d,]+(?:\.\d+)?)")


def norm_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def parse_gsm_gold(solution: str) -> str | None:
    match = GSM_FINAL.search(solution)
    return match.group(1).replace(",", "") if match else None


def decimal_value(value: object) -> Decimal | None:
    # Deliberately handles only plain numeric strings; units, fractions,
    # spelled numbers, and answer semantics need adjudication.
    cleaned = str(value).strip().replace(",", "").replace("$", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def raw_gsm_maps():
    dataset = load_from_disk(str(ROOT / "evaluation/datasets/raw/gsm8k"))
    result = {}
    for split, rows in dataset.items():
        result[split] = {
            (split, index): row for index, row in enumerate(rows)
        }
    return result


def raw_hotpot_maps():
    dataset = load_from_disk(str(ROOT / "evaluation/datasets/raw/hotpotqa"))
    result = {}
    for split, rows in dataset.items():
        result[split] = {str(row["id"]): row for row in rows}
    return result


def audit_gsm(rows: list[dict], raw: dict) -> dict:
    report = collections.Counter()
    examples = collections.defaultdict(list)
    candidate_count = 0
    for row in rows:
        match = re.fullmatch(r"gsm8k_(train|test)_(\d+)", str(row.get("id", "")))
        if not match:
            report["source_id_unresolved"] += len(row.get("candidate_answers") or [])
            continue
        split, index_s = match.groups()
        source = raw.get(split, {}).get((split, int(index_s)))
        candidates = row.get("candidate_answers") or []
        if source is None:
            report["source_row_missing"] += len(candidates)
            continue
        source_gold = parse_gsm_gold(source["answer"])
        stored_gold = str(row.get("gold_answer", ""))
        for candidate in candidates:
            candidate_count += 1
            answer = candidate.get("answer") if isinstance(candidate, dict) else None
            source_match = decimal_value(answer) is not None and decimal_value(answer) == decimal_value(source_gold)
            if candidate.get("source") == "benchmark_gold":
                if source_gold is not None and source_match and decimal_value(stored_gold) == decimal_value(source_gold):
                    report["verified_benchmark_gold"] += 1
                else:
                    report["rejected_source_mismatch"] += 1
            elif candidate.get("source") == "synthetic_numeric_perturbation":
                value = decimal_value(answer)
                gold_value = decimal_value(source_gold)
                if gold_value is not None and value is not None and value == gold_value:
                    report["rejected_duplicate_of_gold"] += 1
                else:
                    report["unresolved_synthetic_negative"] += 1
                    if len(examples["unresolved_synthetic_negative"]) < 5:
                        examples["unresolved_synthetic_negative"].append(row.get("id"))
            else:
                report["unresolved_unknown_candidate_source"] += 1
        # Check the construction itself, not correctness of the negative.
        if len(candidates) == 2 and source_gold is not None:
            values = [decimal_value(c.get("answer")) for c in candidates]
            if all(value is not None for value in values):
                report["pairs_matching_gold_plus_one_rule"] += int(
                    values[0] == decimal_value(source_gold)
                    and values[1] == decimal_value(source_gold) + 1
                )
                report["pairs_with_non_numeric_candidate"] += int(
                    any(value is None for value in values)
                )
            else:
                report["pairs_with_non_numeric_candidate"] += 1
    return {
        "questions": len(rows),
        "candidates": candidate_count,
        "audit_counts": dict(report),
        "sample_unresolved_ids_not_adjudications": dict(examples),
        "interpretation": (
            "verified_benchmark_gold means the stored candidate and gold_answer "
            "match the linked GSM8K source answer. Every synthetic negative remains "
            "unresolved as a correctness label; gold+1 is not proof of incorrectness."
        ),
    }


def audit_hotpot(rows: list[dict], raw: dict) -> dict:
    report = collections.Counter()
    examples = collections.defaultdict(list)
    candidate_count = 0
    all_source_answers = {
        norm_text(source["answer"])
        for split_rows in raw.values()
        for source in split_rows.values()
    }
    for row in rows:
        raw_id = str(row.get("id", "")).removeprefix("hotpot_")
        source = next((split.get(raw_id) for split in raw.values() if raw_id in split), None)
        candidates = row.get("candidate_answers") or []
        if source is None:
            report["source_row_missing"] += len(candidates)
            continue
        source_gold = str(source.get("answer", ""))
        stored_gold = str(row.get("gold_answer", ""))
        if norm_text(stored_gold) != norm_text(source_gold):
            report["question_gold_source_mismatch"] += 1
        for candidate in candidates:
            candidate_count += 1
            answer = str(candidate.get("answer", "")) if isinstance(candidate, dict) else ""
            source_kind = candidate.get("source") if isinstance(candidate, dict) else None
            if source_kind == "benchmark_gold":
                if norm_text(answer) == norm_text(source_gold) and norm_text(stored_gold) == norm_text(source_gold):
                    report["verified_benchmark_gold"] += 1
                else:
                    report["rejected_source_mismatch"] += 1
            elif source_kind == "synthetic_cross_example_answer":
                normalized = norm_text(answer)
                if normalized == norm_text(source_gold):
                    report["rejected_duplicate_of_target_gold"] += 1
                else:
                    report["unresolved_borrowed_answer"] += 1
                    report["borrowed_answer_occurs_as_some_source_gold"] += int(normalized in all_source_answers)
                    if len(examples["unresolved_borrowed_answer"]) < 5:
                        examples["unresolved_borrowed_answer"].append(row.get("id"))
            else:
                report["unresolved_unknown_candidate_source"] += 1
    return {
        "questions": len(rows),
        "candidates": candidate_count,
        "audit_counts": dict(report),
        "sample_unresolved_ids_not_adjudications": dict(examples),
        "interpretation": (
            "verified_benchmark_gold means the candidate matches the linked "
            "HotpotQA source answer after the builder's alphanumeric normalization. "
            "A borrowed answer's being a valid answer to some other question says "
            "nothing about its correctness for the target question. All borrowed "
            "answers not identical to target gold require independent factual review."
        ),
    }


def main() -> None:
    unified = ROOT / "evaluation/datasets/unified"
    gsm_raw = raw_gsm_maps()
    hotpot_raw = raw_hotpot_maps()
    report = {}
    for partition in PARTITIONS:
        rows = json.loads((unified / f"{partition}.json").read_text(encoding="utf-8"))
        gsm = [row for row in rows if row.get("benchmark") == "GSM8K"]
        hotpot = [row for row in rows if row.get("benchmark") == "HotpotQA"]
        report[partition] = {
            "GSM8K": audit_gsm(gsm, gsm_raw),
            "HotpotQA": audit_hotpot(hotpot, hotpot_raw),
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
