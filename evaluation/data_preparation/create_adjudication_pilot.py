"""Create a fixed-seed, reviewer-ready sample without changing source files.

Default output: evaluation/datasets/adjudication/pilot_v1_seed_20261101/
The sampled adjudication JSONL files are compatible with
candidate_adjudication.py apply --output-dir <pilot-dir>.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
from pathlib import Path

from datasets import load_from_disk


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "evaluation/datasets/adjudication/v1"
DEFAULT_SEED = 20261101
DEFAULT_OUTPUT = ROOT / f"evaluation/datasets/adjudication/pilot_v1_seed_{DEFAULT_SEED}"
AVAILABLE_PARTITIONS = ("history", "development", "final_test")
PICK = {
    "gsm8k": "synthetic_numeric_perturbation",
    "hotpotqa": "synthetic_cross_example_answer",
}


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blank_reviewer_slots() -> list[dict]:
    return [
        {
            "reviewer_id": "",
            "decision": "",
            "evidence": [],
            "evidence_provenance": [],
            "rationale": "",
        }
        for _ in range(2)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--per-dataset", type=int, default=30)
    parser.add_argument("--partitions", nargs="+", choices=AVAILABLE_PARTITIONS, default=list(AVAILABLE_PARTITIONS))
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.per_dataset < 1:
        parser.error("--per-dataset must be positive")
    if not args.partitions:
        parser.error("select at least one partition")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty pilot directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    unified = {}
    source_hashes = {}
    for partition in ("history", "development", "final_test"):
        path = ROOT / f"evaluation/datasets/unified/{partition}.json"
        source_hashes[str(path.relative_to(ROOT))] = sha256(path)
        unified[partition] = {
            str(row["id"]): row
            for row in json.loads(path.read_text(encoding="utf-8"))
        }

    gsm_raw = load_from_disk(str(ROOT / "evaluation/datasets/raw/gsm8k"))
    gsm_answers = {
        f"{split}:{index}": row
        for split, rows in gsm_raw.items()
        for index, row in enumerate(rows)
    }

    prepared = {}
    decisions_template = []
    for benchmark, source_tag in PICK.items():
        source_file = args.source_dir / f"{benchmark}_adjudications.jsonl"
        rows = read_jsonl(source_file)
        pool = [
            row for row in rows
            if row.get("adjudication_status") == "unresolved"
            and row.get("candidate_source") == source_tag
            and row.get("partition") in args.partitions
        ]
        pool.sort(key=lambda row: row["candidate_id"])
        if len(pool) < args.per_dataset:
            raise ValueError(f"Only {len(pool)} unresolved {benchmark} candidates; need {args.per_dataset}")
        selected = random.Random(args.seed).sample(pool, args.per_dataset)
        selected.sort(key=lambda row: row["candidate_id"])
        queue = []
        selected_records = []
        for source_record in selected:
            partition = source_record["partition"]
            example = unified[partition].get(source_record["example_id"])
            if example is None:
                raise ValueError(f"Missing source example {source_record['example_id']}")
            queue_row = {
                "candidate_id": source_record["candidate_id"],
                "example_id": source_record["example_id"],
                "partition": partition,
                "dataset": source_record["dataset"],
                "dataset_version": source_record["dataset_version"],
                "source_split": source_record.get("source_split"),
                "source_id": source_record.get("source_id"),
                "question": example.get("question"),
                "candidate_answer": source_record["candidate_answer"],
                "benchmark_reference_answer": source_record.get("source_gold_answer"),
                "reviewer_decisions": blank_reviewer_slots(),
            }
            if benchmark == "gsm8k":
                raw_key = source_record.get("source_id")
                raw = gsm_answers.get(raw_key)
                if raw is None:
                    raise ValueError(f"Missing GSM8K source row {raw_key}")
                queue_row["benchmark_reference_context"] = raw["answer"]
                queue_row["benchmark_reference_context_kind"] = "original worked solution; reviewers should solve independently before consulting"
            else:
                queue_row["reference_context"] = example.get("context") or []
                queue_row["supporting_facts"] = example.get("supporting_facts") or []
                queue_row["reference_context_kind"] = "target HotpotQA context paragraphs"
            queue.append(queue_row)
            selected_records.append(source_record)
            decisions_template.append({
                "candidate_id": source_record["candidate_id"],
                "adjudication_status": "",
                "adjudication_method": "",
                "adjudication_provenance": {},
                "adjudication_rationale": "",
                "adjudication_evidence": [],
                "reviewer_decisions": blank_reviewer_slots(),
                "adjudicator": None,
            })
        prepared[benchmark] = (selected_records, queue)

    for benchmark, (selected, queue) in prepared.items():
        write_jsonl(args.output_dir / f"{benchmark}_adjudications.jsonl", selected)
        write_jsonl(args.output_dir / f"{benchmark}_review_queue.jsonl", queue)
    write_jsonl(args.output_dir / "decisions_template.jsonl", decisions_template)

    # This has the shape expected by candidate_adjudication.py's statistics helper.
    stats = {"benchmarks": {}, "combined": {"candidates": 0, "statuses": {"unresolved": 0}, "methods": {"pending_manual_review": 0}}}
    for benchmark, (selected, _) in prepared.items():
        stats["benchmarks"][benchmark] = {
            "candidates": len(selected),
            "statuses": {"unresolved": len(selected)},
            "methods": {"pending_manual_review": len(selected)},
            "partitions": dict(collections.Counter(row["partition"] for row in selected)),
        }
        stats["combined"]["candidates"] += len(selected)
        stats["combined"]["statuses"]["unresolved"] += len(selected)
        stats["combined"]["methods"]["pending_manual_review"] += len(selected)
    (args.output_dir / "statistics.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "pilot_version": "candidate-review-pilot-v1",
        "seed": args.seed,
        "selection": "random sample without replacement from sorted unresolved synthetic candidates, independently per benchmark",
        "partitions_included": args.partitions,
        "final_test_included": "final_test" in args.partitions,
        "per_dataset": args.per_dataset,
        "source_adjudication_files_sha256": {
            name: sha256(args.source_dir / f"{name}_adjudications.jsonl") for name in PICK
        },
        "unified_source_files_sha256": source_hashes,
        "selected_candidate_ids": {
            name: [row["candidate_id"] for row in prepared[name][0]] for name in PICK
        },
        "framework_predictions_included": False,
        "source_files_modified": False,
        "notice": "All selected items remain unresolved. Reference fields are supplied for human adjudication only; no human decisions are included.",
    }
    (args.output_dir / "pilot_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
