"""Prepare blinded review queues and merge independent adjudication decisions.

The source datasets are read-only. Outputs are written to a versioned,
separate adjudication directory. See evaluation/docs/candidate_adjudication_protocol.md.

Prepare once:
  python evaluation/data_preparation/candidate_adjudication.py prepare
Apply an incremental decisions JSONL (same path can be appended and re-applied):
  python evaluation/data_preparation/candidate_adjudication.py apply --decisions decisions.jsonl
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from datasets import load_from_disk


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "evaluation/datasets/adjudication/v1"
PARTITIONS = ("history", "development", "final_test")
DATASET_VERSIONS = {
    "GSM8K": "main@740312add88f781978c0658806c59bc2815b9866",
    "HotpotQA": "distractor@1908d6afbbead072334abe2965f91bd2709910ab",
}
GSM_PATTERN = re.compile(r"gsm8k_(train|test)_(\d+)")
VALID_STATUSES = {"verified_correct", "verified_incorrect", "unresolved"}


def jdump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: each line must be an object")
            records.append(value)
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def decimal_value(value: object) -> Decimal | None:
    cleaned = str(value).strip().replace(",", "").replace("$", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def raw_maps() -> tuple[dict, dict]:
    gsm = load_from_disk(str(ROOT / "evaluation/datasets/raw/gsm8k"))
    gsm_rows = {
        (split, index): row
        for split, dataset in gsm.items()
        for index, row in enumerate(dataset)
    }
    hotpot = load_from_disk(str(ROOT / "evaluation/datasets/raw/hotpotqa"))
    hotpot_rows = {
        str(row["id"]): (split, row)
        for split, dataset in hotpot.items()
        for row in dataset
    }
    return gsm_rows, hotpot_rows


def base_record(dataset: str, partition: str, example: dict, index: int, candidate: dict) -> dict:
    example_id = str(example["id"])
    return {
        "candidate_id": f"{example_id}::candidate_{index}",
        "example_id": example_id,
        "partition": partition,
        "dataset": dataset,
        "dataset_version": DATASET_VERSIONS[dataset],
        "candidate_index": index,
        "candidate_answer": str(candidate.get("answer", "")),
        "candidate_source": candidate.get("source"),
        "source_expected_correct_unverified": candidate.get("expected_correct"),
        "adjudication_status": "unresolved",
        "adjudication_method": None,
        "adjudication_provenance": None,
        "adjudication_rationale": None,
        "adjudication_evidence": [],
        "reviewer_decisions": [],
        "adjudicated_at_utc": None,
        "source_integrity_status": "unchecked",
    }


def prepare(output_dir: Path, resume: bool) -> None:
    if output_dir.exists() and any(output_dir.iterdir()) and not resume:
        raise FileExistsError(f"Output already exists and is non-empty: {output_dir}; use --resume")
    output_dir.mkdir(parents=True, exist_ok=True)
    gsm_raw, hotpot_raw = raw_maps()

    gsm_full: list[dict] = []
    hotpot_full: list[dict] = []
    gsm_blind: list[dict] = []
    hotpot_blind: list[dict] = []

    source_hashes = {}
    for partition in PARTITIONS:
        source_file = ROOT / f"evaluation/datasets/unified/{partition}.json"
        source_hashes[str(source_file.relative_to(ROOT))] = sha256(source_file)
        examples = json.loads(source_file.read_text(encoding="utf-8"))
        for example in examples:
            dataset = example.get("benchmark")
            if dataset not in {"GSM8K", "HotpotQA"}:
                continue
            candidates = example.get("candidate_answers") or []
            for index, candidate in enumerate(candidates):
                if not isinstance(candidate, dict) or "answer" not in candidate:
                    raise ValueError(f"Malformed candidate: {example.get('id')}[{index}]")
                record = base_record(dataset, partition, example, index, candidate)
                gold_candidate = candidate.get("source") == "benchmark_gold"
                integrity_ok = False
                source_split = None
                source_id = None
                source_gold = None
                evidence: list[dict] = []

                if dataset == "GSM8K":
                    match = GSM_PATTERN.fullmatch(str(example.get("id", "")))
                    source = gsm_raw.get((match.group(1), int(match.group(2)))) if match else None
                    if source is not None:
                        source_split = match.group(1)
                        source_id = f"{source_split}:{match.group(2)}"
                        gold_match = re.search(r"####\s*(-?[\d,]+(?:\.\d+)?)", source["answer"])
                        source_gold = gold_match.group(1).replace(",", "") if gold_match else None
                        integrity_ok = (
                            source_gold is not None
                            and decimal_value(example.get("gold_answer")) == decimal_value(source_gold)
                            and decimal_value(candidate.get("answer")) == decimal_value(source_gold)
                        ) if gold_candidate else source_gold is not None
                        evidence = [{
                            "kind": "benchmark_source_reference",
                            "source": "GSM8K raw answer final marker",
                            "source_id": source_id,
                        }]
                    else:
                        record["source_integrity_status"] = "source_record_not_found"
                else:
                    raw_id = str(example.get("id", "")).removeprefix("hotpot_")
                    source_tuple = hotpot_raw.get(raw_id)
                    if source_tuple:
                        source_split, source = source_tuple
                        source_id = raw_id
                        source_gold = str(source.get("answer", ""))
                        integrity_ok = (
                            norm_text(candidate.get("answer")) == norm_text(source_gold)
                            and norm_text(example.get("gold_answer")) == norm_text(source_gold)
                        ) if gold_candidate else bool(source_gold)
                        evidence = [{
                            "kind": "benchmark_reference_answer",
                            "source": "HotpotQA source answer",
                            "source_id": source_id,
                        }]
                    else:
                        record["source_integrity_status"] = "source_record_not_found"
                    for paragraph in example.get("context") or []:
                        evidence.append({
                            "kind": "reference_context",
                            "title": paragraph.get("title"),
                            "text": paragraph.get("text"),
                        })
                    evidence.extend({
                        "kind": "supporting_fact_reference",
                        "title": fact.get("title"),
                        "sentence_id": fact.get("sentence_id"),
                    } for fact in example.get("supporting_facts") or [])

                record.update({
                    "source_split": source_split,
                    "source_id": source_id,
                    "source_gold_answer": source_gold,
                    "source_evidence": evidence,
                })
                if gold_candidate and integrity_ok:
                    record.update({
                        "adjudication_status": "verified_correct",
                        "adjudication_method": "benchmark_source_match",
                        "adjudication_provenance": {
                            "source_dataset": DATASET_VERSIONS[dataset],
                            "source_id": source_id,
                            "source_split": source_split,
                        },
                        "adjudication_rationale": "Candidate matches the canonical answer in the linked benchmark source under the documented normalization. This is source-label verification, not independent re-solving.",
                        "adjudication_evidence": evidence[:1],
                        "source_integrity_status": "match",
                        "adjudicated_at_utc": datetime.now(timezone.utc).isoformat(),
                    })
                elif gold_candidate:
                    record["source_integrity_status"] = "gold_source_mismatch"
                    record["adjudication_rationale"] = "Stored benchmark_gold candidate did not match the linked raw source; requires investigation. Not automatically classified incorrect."
                else:
                    record["source_integrity_status"] = "source_linked_negative_unadjudicated" if source_gold is not None else "source_unavailable"
                    record["adjudication_rationale"] = "Synthetic/borrowed candidate is not established incorrect by its construction or by the framework; independent review required."

                # Blinded first-pass queue: hide construction label, expected flag,
                # benchmark gold, and worked GSM solution. Hotpot context stays visible.
                blind = {
                    "candidate_id": record["candidate_id"],
                    "example_id": record["example_id"],
                    "partition": partition,
                    "dataset": dataset,
                    "dataset_version": record["dataset_version"],
                    "source_split": source_split,
                    "source_id": source_id,
                    "question": example.get("question"),
                    "candidate_answer": record["candidate_answer"],
                    "rubric_version": "candidate-adjudication-v1",
                    "reference_context": example.get("context") if dataset == "HotpotQA" else None,
                    "supporting_facts": example.get("supporting_facts") if dataset == "HotpotQA" else None,
                    "reviewer_decisions": [],
                }
                if dataset == "GSM8K":
                    blind["candidate_answer_format"] = "numeric candidate; record independent solution and units"
                if dataset == "GSM8K":
                    gsm_full.append(record); gsm_blind.append(blind)
                else:
                    hotpot_full.append(record); hotpot_blind.append(blind)

    for name, records in (("gsm8k", gsm_full), ("hotpotqa", hotpot_full)):
        path = output_dir / f"{name}_adjudications.jsonl"
        if path.exists() and resume:
            existing = {row["candidate_id"]: row for row in read_jsonl(path)}
            generated = {row["candidate_id"]: row for row in records}
            if existing.keys() != generated.keys():
                raise ValueError(f"Existing {path} candidate IDs differ from regenerated source inventory")
            # Preserve imported decisions while refreshing only source-derived fields.
            for candidate_id, old in existing.items():
                fresh = generated[candidate_id]
                for field in ("adjudication_status", "adjudication_method", "adjudication_provenance", "adjudication_rationale", "adjudication_evidence", "reviewer_decisions", "adjudicated_at_utc"):
                    if old.get(field) not in (None, [], "unresolved"):
                        fresh[field] = old[field]
            records = list(generated.values())
        write_jsonl(path, records)
        blind_rows = gsm_blind if name == "gsm8k" else hotpot_blind
        write_jsonl(output_dir / f"{name}_blinded_review_queue.jsonl", blind_rows)

    jdump(output_dir / "manifest.json", {
        "protocol_version": "candidate-adjudication-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_files_sha256": source_hashes,
        "outputs": ["gsm8k_adjudications.jsonl", "hotpotqa_adjudications.jsonl", "gsm8k_blinded_review_queue.jsonl", "hotpotqa_blinded_review_queue.jsonl"],
        "source_datasets_modified": False,
        "results_modified": False,
        "notice": "Benchmark-gold matches are source-label verification. Synthetic negatives start unresolved. No uncertain candidate is classified incorrect.",
    })
    summarize(output_dir)


def validate_manual_decision(row: dict) -> None:
    status = row.get("adjudication_status")
    if status not in VALID_STATUSES:
        raise ValueError(f"{row.get('candidate_id')}: invalid adjudication_status {status!r}")
    if row.get("adjudication_method") not in {"independent_arithmetic_solution", "independent_factual_review", "third_party_adjudication"}:
        raise ValueError(f"{row.get('candidate_id')}: unsupported independent method")
    if not row.get("adjudication_provenance"):
        raise ValueError(f"{row.get('candidate_id')}: adjudication_provenance is required")
    if not str(row.get("adjudication_rationale") or "").strip():
        raise ValueError(f"{row.get('candidate_id')}: rationale is required")
    evidence = row.get("adjudication_evidence")
    if not isinstance(evidence, list) or not evidence or any(not str(item).strip() for item in evidence):
        raise ValueError(f"{row.get('candidate_id')}: at least one evidence item/reference is required")
    reviewers = row.get("reviewer_decisions")
    if not isinstance(reviewers, list) or len(reviewers) < 2:
        raise ValueError(f"{row.get('candidate_id')}: two independent reviewer decisions are required")
    for reviewer in reviewers:
        if not isinstance(reviewer, dict) or not reviewer.get("reviewer_id") or reviewer.get("decision") not in VALID_STATUSES:
            raise ValueError(f"{row.get('candidate_id')}: each reviewer needs reviewer_id and valid decision")
    if status != "unresolved" and any(r["decision"] != status for r in reviewers):
        if not row.get("adjudicator"):
            raise ValueError(f"{row.get('candidate_id')}: disagreement requires an adjudicator")
        if row.get("adjudication_method") != "third_party_adjudication":
            raise ValueError(f"{row.get('candidate_id')}: disagreement must use third_party_adjudication")


def apply_decisions(output_dir: Path, decision_path: Path) -> None:
    incoming = read_jsonl(decision_path)
    by_id = {}
    for row in incoming:
        validate_manual_decision(row)
        candidate_id = row.get("candidate_id")
        if not candidate_id or candidate_id in by_id:
            raise ValueError(f"Missing or duplicate candidate_id in decisions: {candidate_id!r}")
        by_id[candidate_id] = row
    sibling_ids = {
        name: {row["candidate_id"] for row in read_jsonl(output_dir / f"{name}_adjudications.jsonl")}
        for name in ("gsm8k", "hotpotqa")
    }
    all_ids = sibling_ids["gsm8k"] | sibling_ids["hotpotqa"]
    unknown_ids = set(by_id) - all_ids
    if unknown_ids:
        raise ValueError(f"Decisions contain unknown candidate IDs: {sorted(unknown_ids)[:5]}")
    for name in ("gsm8k", "hotpotqa"):
        target = output_dir / f"{name}_adjudications.jsonl"
        records = read_jsonl(target)
        ids = sibling_ids[name]
        relevant_ids = ids & set(by_id)
        if not relevant_ids:
            continue
        for record in records:
            decision = by_id.get(record["candidate_id"])
            if not decision:
                continue
            record.update({
                key: decision[key]
                for key in ("adjudication_status", "adjudication_method", "adjudication_provenance", "adjudication_rationale", "adjudication_evidence", "reviewer_decisions")
            })
            record["adjudicated_at_utc"] = decision.get("adjudicated_at_utc") or datetime.now(timezone.utc).isoformat()
            record["adjudicator"] = decision.get("adjudicator")
            record["source_integrity_status"] = "manual_adjudication_recorded"
        write_jsonl(target, records)
    known = {
        row["candidate_id"]
        for name in ("gsm8k", "hotpotqa")
        for row in read_jsonl(output_dir / f"{name}_adjudications.jsonl")
    }
    if set(by_id) - known:
        raise ValueError(f"Decisions contain unknown candidate IDs: {sorted(set(by_id)-known)[:5]}")
    summarize(output_dir)


def summarize(output_dir: Path) -> None:
    summary = {"benchmarks": {}, "combined": {"candidates": 0, "statuses": {}, "methods": {}}}
    for name in ("gsm8k", "hotpotqa"):
        records = read_jsonl(output_dir / f"{name}_adjudications.jsonl")
        statuses = collections.Counter(row.get("adjudication_status", "unresolved") for row in records)
        methods = collections.Counter(row.get("adjudication_method") or "pending_manual_review" for row in records)
        summary["benchmarks"][name] = {
            "candidates": len(records),
            "statuses": dict(statuses),
            "methods": dict(methods),
            "partitions": {
                partition: dict(collections.Counter(row.get("adjudication_status", "unresolved") for row in records if row.get("partition") == partition))
                for partition in PARTITIONS
            },
        }
        summary["combined"]["candidates"] += len(records)
        for key, value in statuses.items():
            summary["combined"]["statuses"][key] = summary["combined"]["statuses"].get(key, 0) + value
        for key, value in methods.items():
            summary["combined"]["methods"][key] = summary["combined"]["methods"].get(key, 0) + value
    jdump(output_dir / "statistics.json", summary)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="prepare source-linked adjudication files and blinded queues")
    prep.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    prep.add_argument("--resume", action="store_true", help="preserve prior adjudication decisions when refreshing")
    apply = sub.add_parser("apply", help="validate and merge manual decisions JSONL")
    apply.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    apply.add_argument("--decisions", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.output_dir, args.resume)
    else:
        apply_decisions(args.output_dir, args.decisions)


if __name__ == "__main__":
    main()
