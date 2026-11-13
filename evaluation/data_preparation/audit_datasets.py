"""Read-only inventory of local evaluation datasets and result JSONL files.

Run from any directory with the project environment:
    python evaluation/data_preparation/audit_datasets.py

This script never edits source datasets or experiment results.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number}: expected a JSON object")
            rows.append(value)
    return rows


def counts(rows: list[dict]) -> dict:
    ids = [row.get("id") for row in rows]
    benchmarks = collections.Counter(row.get("benchmark", row.get("dataset")) for row in rows)
    labels = collections.Counter(
        str(row.get("label", row.get("ground_truth_label"))) for row in rows
    )
    candidate_labels = collections.Counter()
    candidate_sources = collections.Counter()
    candidate_counts = collections.Counter()
    for row in rows:
        candidates = row.get("candidate_answers") or []
        candidate_counts[len(candidates)] += 1
        for candidate in candidates:
            if isinstance(candidate, dict):
                candidate_labels[str(candidate.get("expected_correct"))] += 1
                candidate_sources[str(candidate.get("source"))] += 1
    return {
        "rows": len(rows),
        "unique_ids": len(set(ids)),
        "duplicate_ids": len(ids) - len(set(ids)),
        "benchmarks": dict(benchmarks),
        "labels": dict(labels),
        "candidate_count_per_question": dict(candidate_counts),
        "candidate_expected_correct": dict(candidate_labels),
        "candidate_sources": dict(candidate_sources),
        "has_group_id": sum(bool(row.get("group_id")) for row in rows),
        "has_label_provenance": sum(
            any(key in row for key in ("label_provenance", "ground_truth_provenance"))
            for row in rows
        ),
        "has_evidence_resource_id": sum(bool(row.get("evidence_resource_id")) for row in rows),
    }


def inspect_dataset_dir(path: Path) -> dict:
    """Inspect JSON datasets and, when installed, local HF datasets metadata."""
    result: dict[str, Any] = {"path": str(path.relative_to(ROOT)), "files": {}}
    for file in sorted(path.rglob("*.json")):
        if any(part in {"dataset_info.json", "state.json", "dataset_dict.json"} for part in file.parts):
            continue
        try:
            value = read_json(file)
            if isinstance(value, list) and all(isinstance(row, dict) for row in value):
                result["files"][str(file.relative_to(ROOT))] = counts(value)
        except (OSError, json.JSONDecodeError) as exc:
            result["files"][str(file.relative_to(ROOT))] = {"read_error": str(exc)}

    raw = path / "raw"
    if raw.is_dir():
        try:
            from datasets import load_from_disk
        except ImportError:
            result["raw_arrow"] = "not inspected: install the project's datasets dependency"
        else:
            result["raw_arrow"] = {}
            for name_dir in sorted(p for p in raw.iterdir() if p.is_dir()):
                try:
                    dataset = load_from_disk(str(name_dir))
                    result["raw_arrow"][name_dir.name] = {
                        split: {"rows": len(rows), "columns": rows.column_names}
                        for split, rows in dataset.items()
                    }
                except Exception as exc:  # report, never hide a partial inventory
                    result["raw_arrow"][name_dir.name] = {"read_error": str(exc)}
    return result


def inspect_results(path: Path) -> dict:
    result = {}
    for file in sorted(path.rglob("*.jsonl")):
        try:
            rows = load_jsonl(file)
            result[str(file.relative_to(ROOT))] = {
                "rows": len(rows),
                "unique_instance_ids": len({row.get("instance_id") for row in rows}),
                "run_status": dict(collections.Counter(row.get("run_status") for row in rows)),
                "benchmarks": dict(collections.Counter(row.get("benchmark") for row in rows)),
                "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
            }
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            result[str(file.relative_to(ROOT))] = {"read_error": str(exc)}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    report = {
        "datasets": inspect_dataset_dir(root / "evaluation" / "datasets"),
        "results_jsonl": inspect_results(root / "evaluation" / "results"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
