"""Aggregate metrics for baseline validation records.

Framework statuses stay ``passed``, ``failed``, ``uncertain``, and
``unknown``. Abstentions are never counted as rejections.
"""

from __future__ import annotations

import math
from collections import Counter


ABSTAIN_STATUSES = {"uncertain", "unknown"}
DEFINITIVE_STATUSES = {"passed", "failed"}


def _finite(values: list[float]) -> list[float]:
    return [value for value in values if isinstance(value, (int, float)) and math.isfinite(value)]


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _safe_div(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _class_f1(tp: int, fp: int, fn: int) -> float | None:
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    if precision is None or recall is None or precision + recall == 0:
        return None
    return 2 * precision * recall / (precision + recall)


def summarize(records: list[dict], *, skipped: list[dict] | None = None) -> dict:
    """Summarize completed records. Error records are counted separately."""
    completed = [row for row in records if row.get("run_status") == "completed"]
    failed = [row for row in records if row.get("run_status") == "error"]
    by_benchmark: dict[str, list[dict]] = {}
    for row in completed:
        by_benchmark.setdefault(row.get("benchmark") or "unknown", []).append(row)

    summary = {
        "completed": len(completed),
        "failed": len(failed),
        "skipped": len(skipped or []),
        "overall": _block(completed),
        "by_benchmark": {name: _block(rows) for name, rows in sorted(by_benchmark.items())},
        "decision_distribution": dict(Counter(row.get("framework_decision") for row in completed)),
        "verifier_selection_frequency": _name_frequency(completed, "selected_verifiers"),
        "verifier_execution_frequency": _name_frequency(completed, "executed_verifiers"),
        "skipped_by_benchmark": dict(Counter(row.get("benchmark") for row in (skipped or []))),
    }
    return summary


def _name_frequency(records: list[dict], field: str) -> dict:
    counts: Counter = Counter()
    for row in records:
        names = row.get(field) or []
        if isinstance(names, list):
            counts.update(str(name) for name in names)
    return dict(counts)


def _block(records: list[dict]) -> dict:
    total = len(records)
    abstained = [row for row in records if row.get("abstained") is True]
    definitive = [row for row in records if row.get("framework_decision") in DEFINITIVE_STATUSES]
    correct = [row for row in records if row.get("prediction_correct") is True]
    selective_correct = [row for row in definitive if row.get("prediction_correct") is True]

    binary = [row for row in records if row.get("gold_role") in {"accept", "reject"}]
    binary_definitive = [row for row in binary if row.get("framework_decision") in DEFINITIVE_STATUSES]
    tp = sum(1 for row in binary_definitive if row["framework_decision"] == "passed" and row["gold_role"] == "accept")
    fp = sum(1 for row in binary_definitive if row["framework_decision"] == "passed" and row["gold_role"] == "reject")
    fn = sum(1 for row in binary_definitive if row["framework_decision"] == "failed" and row["gold_role"] == "accept")
    tn = sum(1 for row in binary_definitive if row["framework_decision"] == "failed" and row["gold_role"] == "reject")

    incorrect = [row for row in records if row.get("gold_role") == "reject"]
    correct_candidates = [row for row in records if row.get("gold_role") == "accept"]
    false_accepts = sum(1 for row in incorrect if row.get("framework_decision") == "passed")
    false_rejects = sum(1 for row in correct_candidates if row.get("framework_decision") == "failed")

    accept_f1 = _class_f1(tp, fp, fn)
    reject_f1 = _class_f1(tn, fn, fp)
    macro_values = [value for value in (accept_f1, reject_f1) if value is not None]
    macro_f1 = sum(macro_values) / len(macro_values) if macro_values else None

    latencies = _finite([row.get("latency_ms") for row in records])
    calls = _finite([row.get("verifier_calls") for row in records])
    distribution = dict(Counter(row.get("framework_decision") for row in records))

    return {
        "instances": total,
        "accuracy": _safe_div(len(correct), total),
        "precision_accept": _safe_div(tp, tp + fp),
        "recall_accept": _safe_div(tp, tp + fn),
        "f1_accept": accept_f1,
        "macro_f1_accept_reject": macro_f1,
        "precision_recall_scope": (
            "Accept/reject precision, recall, and macro F1 use only definitive "
            "predictions on binary gold roles. Abstentions are excluded from "
            "those counts and are not treated as rejections."
        ),
        "confusion_definitive_binary": {
            "true_accept": tp,
            "false_accept": fp,
            "false_reject": fn,
            "true_reject": tn,
        },
        "false_acceptance_rate": _safe_div(false_accepts, len(incorrect)),
        "false_rejection_rate": _safe_div(false_rejects, len(correct_candidates)),
        "false_acceptance_count": false_accepts,
        "false_rejection_count": false_rejects,
        "incorrect_candidate_count": len(incorrect),
        "correct_candidate_count": len(correct_candidates),
        "coverage": _safe_div(len(definitive), total),
        "abstention_rate": _safe_div(len(abstained), total),
        "selective_accuracy": _safe_div(len(selective_correct), len(definitive)),
        "definitive_count": len(definitive),
        "abstention_count": len(abstained),
        "correct_count": len(correct),
        "decision_distribution": distribution,
        "latency_ms": {
            "mean": (sum(latencies) / len(latencies)) if latencies else None,
            "median": _percentile(latencies, 0.5),
            "p95": _percentile(latencies, 0.95),
        },
        "verifier_calls": {
            "mean": (sum(calls) / len(calls)) if calls else None,
            "total": sum(calls) if calls else 0,
        },
    }
