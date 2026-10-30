"""Offline semantic evaluation, separate from exact parser contract tests.

Run as a module. Default is heuristic-only with no environment configuration.
Supplied outputs: JSON array of {"id": case_id, "analysis": {...}}.
No live mode is implemented; producing live outputs is a separate opt-in task.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path

from app.analysis.question_analyzer import QuestionAnalyzer
from app.analysis.model_assessment import PRIMARY_DOMAINS, DOMAIN_STATUSES, VERIFICATION_TYPES

DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "tests/fixtures/analyzer_semantic_examples.json"


def _validate_records(records: object, collection: str, payload_key: str) -> list[str]:
    """Validate the full collection before any metric calculation."""
    if not isinstance(records, list):
        raise ValueError(f"{collection} must be a list of objects")
    ids = []
    for index, record in enumerate(records):
        location = f"{collection}[{index}]"
        if not isinstance(record, dict):
            raise ValueError(f"{location} must be an object")
        case_id = record.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"{location}.id must be a nonempty string (IDs)")
        location = f"{collection} case {case_id!r}"
        if case_id in ids:
            raise ValueError(f"{location}.id is duplicated (IDs must be unique)")
        ids.append(case_id)
        payload = record.get(payload_key)
        if not isinstance(payload, dict):
            raise ValueError(f"{location}.{payload_key} must be an object")
        labels = {"domain": PRIMARY_DOMAINS, "domain_status": DOMAIN_STATUSES,
                  "difficulty": ("easy", "medium", "hard")}
        if payload_key == "analysis":
            labels["analysis_method"] = ("heuristic", "heuristic_fallback", "ollama")
        for field, allowed in labels.items():
            path = f"{location}.{payload_key}.{field}"
            if field not in payload:
                raise ValueError(f"{path} is required")
            value = payload[field]
            if field == "difficulty" and payload_key == "expected" and value is None:
                continue
            if not isinstance(value, str) or value not in allowed:
                raise ValueError(f"{path} must be one of {allowed}" +
                                 (" or explicit null" if field == "difficulty" and payload_key == "expected" else ""))
        hints = payload.get("verification_types")
        if not isinstance(hints, list) or any(not isinstance(hint, str) or hint not in VERIFICATION_TYPES for hint in hints):
            raise ValueError(f"{location}.{payload_key}.verification_types must be a list of supported string labels")
    return ids


def evaluate(cases: list[dict], outputs: list[dict]) -> dict:
    """Micro type precision/recall; undefined metrics are None, never perfect.

    Require a complete, unique set of supplied IDs to avoid silently excluding
    failures. Difficulty agreement excludes explicitly unlabeled cases.
    """
    ids = _validate_records(cases, "cases", "expected")
    supplied = _validate_records(outputs, "outputs", "analysis")
    if not ids:
        raise ValueError("fixture IDs must be nonempty")
    if set(ids) != set(supplied):
        raise ValueError(f"supplied output IDs must match fixture IDs exactly once; "
                         f"missing={sorted(set(ids)-set(supplied))}, extra={sorted(set(supplied)-set(ids))}")
    by_id = {row["id"]: row["analysis"] for row in outputs}
    domain = status = band = band_count = tp = fp = fn = fallbacks = 0
    methods = Counter()
    for case in cases:
        expected, actual = case["expected"], by_id[case["id"]]
        hints = actual["verification_types"]
        predicted, wanted = set(hints), set(expected["verification_types"])
        domain += actual["domain"] == expected["domain"]
        status += actual["domain_status"] == expected["domain_status"]
        if expected.get("difficulty") is not None:
            band_count += 1
            band += actual["difficulty"] == expected["difficulty"]
        tp += len(predicted & wanted)
        fp += len(predicted - wanted)
        fn += len(wanted - predicted)
        methods[actual["analysis_method"]] += 1
        fallbacks += actual["analysis_method"] == "heuristic_fallback"
    n = len(cases)
    return {"cases": n, "domain_accuracy": domain/n, "domain_status_accuracy": status/n,
            "verification_type_precision_micro": tp/(tp+fp) if tp+fp else None,
            "verification_type_recall_micro": tp/(tp+fn) if tp+fn else None,
            "type_counts": {"true_positive": tp, "false_positive": fp, "false_negative": fn},
            "difficulty_band_agreement": band/band_count if band_count else None,
            "difficulty_labeled_cases": band_count, "fallback_rate": fallbacks/n,
            "analysis_methods": dict(sorted(methods.items()))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--outputs", type=Path, help="Supplied analysis outputs; never invokes a service")
    parser.add_argument("--save-outputs", type=Path, help="Optional output capture for reproducible offline scoring")
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    if not isinstance(fixture, dict):
        raise ValueError("fixture must be an object")
    if not isinstance(fixture.get("fixture_version"), str) or not fixture["fixture_version"].strip():
        raise ValueError("fixture.fixture_version must be a nonempty string")
    cases = fixture.get("cases")
    _validate_records(cases, "cases", "expected")
    if args.outputs:
        outputs = json.loads(args.outputs.read_text(encoding="utf-8"))
    else:
        for case in cases:
            if not isinstance(case.get("question"), str) or not case["question"].strip():
                raise ValueError(f"cases case {case['id']!r}.question must be a nonempty string")
        analyzer = QuestionAnalyzer(mode="heuristic", environ={})
        outputs = [{"id": case["id"], "analysis": asdict(analyzer.analyze(case["question"]))} for case in cases]
    metrics = evaluate(cases, outputs)
    if args.save_outputs:
        args.save_outputs.write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"fixture_version": fixture["fixture_version"],
                      "source": "supplied" if args.outputs else "offline_heuristic",
                      "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
