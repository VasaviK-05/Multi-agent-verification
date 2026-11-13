"""Experiment 3 summaries. Intervals reuse the paired-bootstrap quantile."""

from __future__ import annotations

import random
from collections import defaultdict

from app.game.research.uncertainty import _quantile

METHODS = ("full_minimax", "fixed_reputation_weighted", "fixed_dependency_group")
REFERENCE = "full_minimax"
SCENARIOS = ("independent_failures", "correlated_failures")
REQUIRED_FIELDS = (
    "related_group_id", "benchmark", "attack_condition", "dependency_model", "dependency_scenario",
    "aggregation_method", "decision", "gold_label", "validation_loss", "coverage", "uncertainty",
    "verifier_reports", "verifier_costs", "execution_status", "provenance", "configuration_id", "evidence_label",
)
CONTRAST = "ablation_validation_loss_minus_full_minimax"


def _reject_final_test(row: dict) -> None:
    provenance = row.get("provenance")
    blob = " ".join(str(part) for part in (row.get("partition"), row.get("benchmark"), provenance))
    if "final_test" in blob.replace("\\", "/").lower():
        raise ValueError("Final Test data is not used")


def validate_rows(rows: list[dict]) -> None:
    if not rows:
        raise ValueError("no result rows")
    labels = {row.get("evidence_label") for row in rows}
    if labels - {"SYNTHETIC", "EMPIRICAL"}:
        raise ValueError("evidence_label must be SYNTHETIC or EMPIRICAL")
    if len(labels) != 1:
        raise ValueError("synthetic and empirical rows cannot be mixed")
    for row in rows:
        _reject_final_test(row)
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            raise ValueError(f"result row is missing {missing}")
        if row["aggregation_method"] not in METHODS:
            raise ValueError("unknown aggregation method")


def binary_correctness(row: dict) -> str | None:
    """Authorized Development gold only. Unresolved labels are not binary outcomes."""
    _reject_final_test(row)
    if row.get("gold_label") in {None, "UNRESOLVED", "UNAUTHORIZED"}:
        return None
    if row.get("execution_status") != "complete" or row.get("decision") not in {"passed", "failed"}:
        return None
    passed = row["decision"] == "passed"
    correct_gold = row["gold_label"] == "VERIFIED_CORRECT"
    if row["gold_label"] not in {"VERIFIED_CORRECT", "SYNTHETIC_INCORRECT"}:
        return None
    correct = passed == correct_gold
    return ("correct_" if correct else "false_") + ("acceptance" if passed else "rejection")


def _analyzable(row: dict) -> bool:
    return (row.get("execution_status") == "complete" and row.get("validation_loss") is not None
            and row.get("gold_label") not in {None, "UNRESOLVED", "UNAUTHORIZED"})


def execution_report(rows: list[dict]) -> dict:
    validate_rows(rows)
    failed = [row for row in rows if row.get("execution_status") != "complete"]
    unresolved = [row for row in rows if row.get("gold_label") in {None, "UNRESOLVED", "UNAUTHORIZED"}]
    return {
        "rows": len(rows),
        "failed_execution_count": len(failed),
        "unresolved_or_unauthorized_label_count": len(unresolved),
        "excluded_from_loss_and_coverage": len({id(row) for row in failed + unresolved}),
        "imputed": 0,
    }


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def aggregation_comparison(rows: list[dict]) -> list[dict]:
    validate_rows(rows)
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        if _analyzable(row):
            buckets[(row["benchmark"], row["attack_condition"], row["aggregation_method"], row["dependency_model"])].append(row)
    summaries = []
    seen = {(row["benchmark"], row["attack_condition"], row["dependency_model"]) for row in rows}
    for benchmark, attack, dependency in sorted(seen):
        for method in METHODS:
            chosen = buckets.get((benchmark, attack, method, dependency), [])
            summaries.append({
                "benchmark": benchmark,
                "attack_condition": attack,
                "dependency_model": dependency,
                "aggregation_method": method,
                "evidence_label": rows[0]["evidence_label"],
                "sample_size": len(chosen),
                "validation_loss": _mean([row["validation_loss"] for row in chosen]),
                "coverage": _mean([float(row["coverage"]) for row in chosen]),
                "status": "available" if chosen else "unavailable",
            })
    return summaries


def identical_outcomes(rows: list[dict]) -> list[dict]:
    validate_rows(rows)
    grouped: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        if row.get("execution_status") != "complete":
            continue
        key = (row["related_group_id"], row["attack_condition"], row["dependency_model"], row["benchmark"])
        grouped[key][row["aggregation_method"]] = row
    findings = []
    for key, methods in sorted(grouped.items()):
        if not set(METHODS) <= set(methods):
            continue
        decisions = {methods[name]["decision"] for name in METHODS}
        losses = {methods[name]["validation_loss"] for name in METHODS}
        coverages = {methods[name]["coverage"] for name in METHODS}
        findings.append({
            "related_group_id": key[0],
            "attack_condition": key[1],
            "dependency_model": key[2],
            "benchmark": key[3],
            "identical_decisions": len(decisions) == 1,
            "identical_losses": len(losses) == 1,
            "identical_coverage": len(coverages) == 1,
            "decision": next(iter(decisions)) if len(decisions) == 1 else None,
        })
    return findings


def dependency_discrimination(verifiers: list[str], groups: list[list[str]]) -> dict:
    one_group = len(groups) == 1 and set(groups[0]) == set(verifiers)
    return {
        "limited_dependency_discrimination": one_group,
        "reason": "All verifiers are in one dependency group, so independent and correlated attacks are not separately identified." if one_group else None,
        "group_count": len(groups),
    }


def dependency_robustness_matrix(rows: list[dict], *, aggregation_method: str, declared_model: str, verifiers: list[str] | None = None, groups: list[list[str]] | None = None) -> dict:
    validate_rows(rows)
    if aggregation_method not in METHODS:
        raise ValueError("unknown aggregation method")
    chosen = [row for row in rows if row["aggregation_method"] == aggregation_method]
    models = [declared_model] + sorted({row["dependency_model"] for row in chosen if row["dependency_model"] != declared_model})
    present = {row["dependency_model"] for row in chosen}
    cells = []
    for model in models:
        for scenario in SCENARIOS:
            matched = [row for row in chosen if row["dependency_model"] == model and row["dependency_scenario"] == scenario and _analyzable(row)]
            value = _mean([row["validation_loss"] for row in matched])
            cells.append({
                "dependency_model": model,
                "row_role": "declared_dependency_model" if model == declared_model else "alternative_dependency_assumption",
                "dependency_scenario": scenario,
                "validation_loss": value,
                "sample_size": len(matched),
                "status": "available" if value is not None else "unavailable",
            })
    alternatives = [model for model in present if model != declared_model]
    estimable = bool(alternatives) and any(cell["status"] == "available" for cell in cells)
    reason = None if estimable else "only one dependency model is available" if not alternatives else "no matched validation-loss cells are available"
    discrimination = dependency_discrimination(verifiers, groups) if verifiers is not None and groups is not None else None
    return {
        "estimable": estimable,
        "reason": reason,
        "aggregation_method": aggregation_method,
        "evidence_label": rows[0]["evidence_label"],
        "columns": list(SCENARIOS),
        "rows": models,
        "cells": cells,
        "dependency_discrimination": discrimination,
        "measured_dependency_evidence": "none" if rows[0]["evidence_label"] == "SYNTHETIC" else "recorded_in_row_provenance",
    }


def _pairs(rows: list[dict], method: str) -> tuple[dict[str, list[float]], int]:
    full, other = {}, {}
    for row in rows:
        if not _analyzable(row) or row["aggregation_method"] not in {REFERENCE, method}:
            continue
        key = (row["related_group_id"], row["attack_condition"], row["dependency_model"], row["benchmark"])
        target = full if row["aggregation_method"] == REFERENCE else other
        target[key] = row["validation_loss"]
    shared = set(full) & set(other)
    missing = (set(full) | set(other)) - shared
    by_group: dict[str, list[float]] = defaultdict(list)
    for key in shared:
        by_group[key[0]].append(other[key] - full[key])
    return by_group, len(missing)


def _interval(by_group: dict[str, list[float]], *, resamples, confidence_level, seed) -> dict:
    groups = sorted(by_group)
    if resamples is None or confidence_level is None or seed is None:
        return {"lower": None, "upper": None, "reason": "statistical_configuration_pending", "resamples": 0}
    if len(groups) < 2:
        return {"lower": None, "upper": None, "reason": "at_least_two_related_groups_required", "resamples": 0}
    rng = random.Random(seed)
    means = []
    for _ in range(resamples):
        draw = [rng.choice(groups) for _ in groups]
        values = [value for name in draw for value in by_group[name]]
        means.append(sum(values) / len(values))
    tail = (1.0 - confidence_level) / 2.0
    return {"lower": _quantile(means, tail), "upper": _quantile(means, 1.0 - tail), "reason": None, "resamples": resamples}


def paired_loss_differences(rows: list[dict], *, resamples=None, confidence_level=None, seed=None) -> list[dict]:
    validate_rows(rows)
    results = []
    for method in METHODS:
        if method == REFERENCE:
            continue
        by_group, missing = _pairs(rows, method)
        values = [value for group in by_group.values() for value in group]
        interval = _interval(by_group, resamples=resamples, confidence_level=confidence_level, seed=seed)
        results.append({
            "aggregation_method": method,
            "reference": REFERENCE,
            "contrast": CONTRAST,
            "evidence_label": rows[0]["evidence_label"],
            "sample_size": len(values),
            "related_group_count": len(by_group),
            "missing_pairs": missing,
            "mean_loss_difference": _mean(values),
            "zero_difference_count": sum(value == 0 for value in values),
            "confidence_interval": interval,
            "practical_effect": _mean(values),
            "statistical_interval_available": interval["lower"] is not None,
        })
    return results


def protocol_gaps(spec: dict) -> list[str]:
    gaps = []
    visuals = spec.get("visualizations") or {}
    for key in ("aggregation_ablation_grouped_bars", "dependency_robustness_heatmap", "paired_ablation_effect_difference"):
        if key not in visuals:
            gaps.append(f"missing visualization {key}")
    fields = (spec.get("result_schema") or {}).get("required_fields")
    if list(fields or []) != list(REQUIRED_FIELDS):
        gaps.append("result schema is missing required analysis fields")
    analysis = spec.get("analysis") or {}
    if analysis.get("paired_contrast") != CONTRAST or list(analysis.get("pairing_keys") or []) != ["related_group_id", "attack_condition"]:
        gaps.append("paired analysis configuration is incomplete")
    if not analysis.get("missing_data"):
        gaps.append("missing-data policy is absent")
    plot = spec.get("plot_configuration") or {}
    if not plot.get("module") or plot.get("synthetic_figures_are_empirical") is not False:
        gaps.append("plot configuration is incomplete")
    scenarios = spec.get("dependency_scenarios") or {}
    if scenarios.get("columns") != list(SCENARIOS):
        gaps.append("dependency scenario coverage is incomplete")
    heatmap = visuals.get("dependency_robustness_heatmap") or {}
    if heatmap.get("heatmap_estimable") is True and scenarios.get("alternative_models_recorded") is not True:
        gaps.append("heatmap marked estimable without an alternative dependency model")
    return gaps
