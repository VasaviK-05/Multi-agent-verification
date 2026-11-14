"""Diagnose the completed Experiment 3 collection without calling verifiers.

The raw result, metric, bootstrap, and report files are read only. This module
writes under ``empirical/diagnosis/`` and does not call ``execute``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.decision.decision_engine import DecisionEngine, log_odds_weight
from app.game.decision_inputs import FrozenReputationSnapshot
from app.game.strategies import enumerate_strategies
from app.models.schemas import VerificationResult
from evaluation.analysis.experiment3 import binary_correctness
from evaluation.experiments.experiment3.empirical_executor import (
    LOSS,
    VERIFIERS,
    _attacks,
    _condition_reports,
    _matrix,
    _policies,
    experiment_context,
    load_examples,
    score,
)
from evaluation.experiments.experiment3.empirical_runner import METHODS, analyze_recordings
from evaluation.experiments.experiment3.execution_readiness import BUDGET_MS, CALIBRATION_ID, COEFFICIENT, SEED
from evaluation.experiments.experiment3.resource_sensitivity import coefficient_scenarios, frozen_calibration

EMPIRICAL = ROOT / "evaluation/experiments/experiment3/empirical"
DIAGNOSIS = EMPIRICAL / "diagnosis" / "policy_diagnosis.json"
PROTECTED = (
    EMPIRICAL / "results.json",
    EMPIRICAL / "metrics.json",
    EMPIRICAL / "bootstrap_results.json",
    EMPIRICAL / "verifier_reports.jsonl",
    EMPIRICAL / "figures" / "attack_validation_loss.svg",
)
PUBLISHED_HASHES = {
    "results.json": "82324e96da71095bf1f2e75a2c080a396151590671111a91d7a870a6a657f8f8",
    "metrics.json": "2c186172e5f1e9e2c2f344292d0b5a093a11e8fbb746294bde6cb54faeb08c57",
    "bootstrap_results.json": "2b56ac693740bfdbee00dcf788c0bb4a097d7f70c3ad78b3335bd6b120dce53a",
    "verifier_reports.jsonl": "877d0218dd498e8ca525e651f52f8aa1e337cd6f5123583fb277a2a28e01eca5",
    "attack_validation_loss.svg": "8be472c94d29b34caec0829065afcc21eb059b746d0d31f8b2871fc7465b1dd4",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes() -> dict[str, str]:
    return {path.name: sha256(path) for path in PROTECTED}


def _attack_label(row: dict) -> str:
    target = row.get("attack_target") or []
    if target:
        return row["attack_condition"] + " [" + ",".join(target) + "]"
    return row["attack_condition"]


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _metric_block(rows: list[dict]) -> dict:
    classified = [label for label in (binary_correctness(row) for row in rows) if label is not None]
    false_accept = classified.count("false_acceptance")
    false_reject = classified.count("false_rejection")
    correct_accept = classified.count("correct_acceptance")
    correct_reject = classified.count("correct_rejection")
    negative = false_accept + correct_reject
    positive = false_reject + correct_accept
    losses = [row["validation_loss"] for row in rows if row.get("validation_loss") is not None]
    decisions = [row["decision"] for row in rows]
    costs = [row["estimated_cost_ms"] for row in rows]
    return {
        "candidates": len(rows),
        "mean_decision_loss": None if not losses else sum(losses) / len(losses),
        "loss_value_counts": {f"{value:.1f}": count for value, count in sorted(Counter(losses).items())},
        "correct_acceptance": correct_accept,
        "correct_rejection": correct_reject,
        "false_acceptance": false_accept,
        "false_rejection": false_reject,
        "uncertain": decisions.count("uncertain"),
        "coverage": _rate(len(classified), len(rows)),
        "selective_risk": _rate(false_accept + false_reject, len(classified)),
        "false_acceptance_rate": _rate(false_accept, negative),
        "false_rejection_rate": _rate(false_reject, positive),
        "false_acceptance_denominator": negative,
        "false_rejection_denominator": positive,
        "classified": len(classified),
        "team_cost_ms": None if not costs else costs[0],
        "execution_failures": sum(row.get("execution_status") != "complete" for row in rows),
    }


def audit_results(payload: dict, rows: list[dict]) -> dict:
    keys = [(row["candidate_id"], row["attack_id"], row["aggregation_method"]) for row in rows]
    methods = sorted({row["aggregation_method"] for row in rows})
    attacks = sorted({row["attack_id"] for row in rows})
    teams = {method: sorted({tuple(row["selected_verifiers"]) for row in rows if row["aggregation_method"] == method}) for method in methods}
    decisions = defaultdict(dict)
    losses = defaultdict(dict)
    for row in rows:
        key = (row["candidate_id"], row["attack_id"])
        decisions[key][row["aggregation_method"]] = row["decision"]
        losses[key][row["aggregation_method"]] = row["validation_loss"]
    decision_mismatch = 0
    loss_mismatch = 0
    for key, values in decisions.items():
        if len(values) != 3 or len(set(values.values())) != 1:
            decision_mismatch += 1
        if len(set(losses[key].values())) != 1:
            loss_mismatch += 1
    return {
        "status": payload.get("status"),
        "evidence_label": payload.get("evidence_label"),
        "groups": len({row["related_group_id"] for row in rows}),
        "candidates": len({row["candidate_id"] for row in rows}),
        "completed_cells": payload.get("completed_cells"),
        "rows": len(rows),
        "attack_columns": len(attacks),
        "methods": methods,
        "duplicate_keys": len(keys) - len(set(keys)),
        "execution_failures": sum(row.get("execution_status") != "complete" for row in rows),
        "incomplete_status": sum(row.get("execution_status") != "complete" for row in rows),
        "final_test_accessed": payload.get("final_test_accessed"),
        "selected_teams": {method: [list(team) for team in found] for method, found in teams.items()},
        "decision_mismatches": decision_mismatch,
        "loss_mismatches": loss_mismatch,
        "benchmarks": dict(Counter(row["benchmark"] for row in rows if row["aggregation_method"] == "full_minimax")),
    }


def _same(stored, fresh) -> bool:
    if isinstance(stored, float) or isinstance(fresh, float):
        if stored is None or fresh is None:
            return stored is fresh
        return math.isclose(float(stored), float(fresh), rel_tol=0.0, abs_tol=0.0)
    return stored == fresh


def reproduction_check(rows: list[dict], metrics: dict, bootstrap: dict) -> dict:
    fresh = analyze_recordings(rows, evidence_label="EMPIRICAL", resamples=2000, confidence_level=0.95, seed=SEED)
    stored_metrics = metrics["analysis"]["metrics"]
    fields = (
        "rows", "validation_loss", "coverage", "uncertainty_rate", "classified_decisions",
        "correct_acceptance_count", "correct_rejection_count", "false_acceptance_count",
        "false_rejection_count", "false_acceptance_rate", "false_rejection_rate",
        "selective_risk", "execution_failures",
    )
    metric_mismatches = []
    for stored, recomputed in zip(stored_metrics, fresh["metrics"]):
        for field in fields:
            if not _same(stored.get(field), recomputed.get(field)):
                metric_mismatches.append({"field": field, "stored": stored.get(field), "recomputed": recomputed.get(field), "key": [stored["benchmark"], stored["attack_condition"], stored["aggregation_method"]]})
    paired_mismatches = []
    for stored, recomputed in zip(bootstrap["paired_differences"], fresh["paired_differences"]):
        for field in ("mean_loss_difference", "related_group_count", "sample_size", "zero_difference_count"):
            if not _same(stored.get(field), recomputed.get(field)):
                paired_mismatches.append({"field": field, "method": stored["aggregation_method"]})
        for bound in ("lower", "upper", "resamples"):
            if not _same(stored["confidence_interval"].get(bound), recomputed["confidence_interval"].get(bound)):
                paired_mismatches.append({"field": bound, "method": stored["aggregation_method"]})
    return {
        "metrics_match": not metric_mismatches,
        "bootstrap_match": not paired_mismatches,
        "metric_mismatch_count": len(metric_mismatches),
        "paired_mismatch_count": len(paired_mismatches),
        "metric_mismatches": metric_mismatches[:8],
        "paired_differences": fresh["paired_differences"],
        "worst_case_loss": fresh["worst_case_loss"],
    }


def slice_tables(rows: list[dict]) -> dict:
    one = [row for row in rows if row["aggregation_method"] == "full_minimax"]
    by_attack = defaultdict(list)
    by_benchmark = defaultdict(list)
    by_both = defaultdict(list)
    for row in one:
        label = _attack_label(row)
        by_attack[label].append(row)
        by_benchmark[row["benchmark"]].append(row)
        by_both[(row["benchmark"], label)].append(row)
    return {
        "population": "full_minimax rows. The other two methods match these decisions and losses on every cell.",
        "by_attack": [{**{"attack": label}, **_metric_block(chosen)} for label, chosen in sorted(by_attack.items())],
        "by_benchmark": [{**{"benchmark": name}, **_metric_block(chosen)} for name, chosen in sorted(by_benchmark.items())],
        "by_benchmark_and_attack": [
            {**{"benchmark": benchmark, "attack": label}, **_metric_block(chosen)}
            for (benchmark, label), chosen in sorted(by_both.items())
        ],
    }


def verifier_summary(path: Path) -> dict:
    means = frozen_calibration()["means_ms"]
    decisions = Counter()
    reasons = Counter()
    seconds = Counter()
    ok = Counter()
    rows = 0
    for line in path.open(encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        rows += 1
        for name, report in row["reports"].items():
            ok[(name, bool(report.get("ok")))] += 1
            seconds[name] += float(report.get("seconds") or 0.0)
            metadata = ((report.get("result") or {}).get("metadata") or {})
            decisions[(name, row["benchmark"], str(metadata.get("decision")))] += 1
            if metadata.get("abstain_reason"):
                reasons[(name, row["benchmark"], str(metadata["abstain_reason"]))] += 1
    by_verifier = {}
    for name in VERIFIERS:
        recorded_ms = None if rows == 0 else 1000.0 * seconds[name] / rows
        frozen = means[name]
        by_verifier[name] = {
            "ok": ok[(name, True)],
            "failed": ok[(name, False)],
            "mean_recorded_seconds": None if rows == 0 else seconds[name] / rows,
            "mean_recorded_ms": recorded_ms,
            "frozen_calibration_mean_ms": frozen,
            "recorded_minus_frozen_ms": None if recorded_ms is None else recorded_ms - frozen,
            "decisions": {
                benchmark: {
                    decision: decisions[(name, benchmark, decision)]
                    for decision in ("SUPPORT", "REJECT", "UNSURE", "None")
                    if decisions[(name, benchmark, decision)]
                }
                for benchmark in ("GSM8K", "HotpotQA")
            },
        }
    return {
        "reports": rows,
        "by_verifier": by_verifier,
        "abstain_reasons": [
            {"verifier": name, "benchmark": benchmark, "reason": reason, "count": count}
            for (name, benchmark, reason), count in sorted(reasons.items())
        ],
        "cost_note": "Recorded milliseconds are this run's wall time. Frozen means are the feasibility and penalty costs. They are different measurements.",
    }


def _report(name: str, decision: str, score: float) -> VerificationResult:
    return VerificationResult(
        verifier_name=name,
        score=score,
        passed=decision == "SUPPORT",
        metadata={"decision": decision},
    )


def cold_start_controlled_example() -> dict:
    """Show when equal cold-start weights make the aggregations agree or diverge."""
    context = experiment_context()
    snapshot = FrozenReputationSnapshot.from_planning_context(context)
    engine = DecisionEngine(threshold=0.55)
    weight = log_odds_weight(0.5)
    pair = [_report("evidence", "SUPPORT", 1.0), _report("rule", "REJECT", 1.0)]
    triple = [_report("semantic", "SUPPORT", 1.0), _report("evidence", "SUPPORT", 1.0), _report("rule", "REJECT", 0.2)]

    def both(results, team):
        reputation = engine.decide(results, snapshot=snapshot, aggregation="reputation_weighted", team=team, validation_id="controlled")
        dependency = engine.decide(
            results, snapshot=snapshot, aggregation="dependency_group", dependencies=context.dependencies,
            team=team, validation_id="controlled",
        )
        return {
            "reputation_weighted": {"status": reputation[0], "score": reputation[1]},
            "dependency_group": {"status": dependency[0], "score": dependency[1]},
        }

    pair_status = both(pair, ("evidence", "rule"))
    triple_status = both(triple, ("semantic", "evidence", "rule"))
    return {
        "prior_mean": 0.5,
        "log_odds_weight_at_one_half": weight,
        "reliability_strength_at_one_half": max(0.0, 2 * 0.5 - 1),
        "reputation_fallback_when_weight_is_zero": "equal_weight",
        "dependency_fallback_when_reliability_is_zero": "unweighted_members_then_unweighted_groups",
        "one_verifier_per_component": {
            "team": ["evidence", "rule"],
            "reports": "evidence SUPPORT 1, rule REJECT 1",
            "statuses": pair_status,
            "same_decision": pair_status["reputation_weighted"]["status"] == pair_status["dependency_group"]["status"],
        },
        "two_verifiers_in_one_component": {
            "team": ["semantic", "evidence", "rule"],
            "reports": "semantic SUPPORT 1, evidence SUPPORT 1, rule REJECT 0.2",
            "statuses": triple_status,
            "same_decision": triple_status["reputation_weighted"]["status"] == triple_status["dependency_group"]["status"],
            "reason": "Reputation averages the three votes. Dependency averages semantic with evidence first, then averages that component with rule.",
        },
    }


def _strategy_rows(cells: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in cells:
        grouped[(row["strategy_id"], tuple(row["verifiers"]), row["aggregation"], row["estimated_cost_ms"])].append(row)
    summaries = []
    for (strategy_id, verifiers, aggregation, cost), chosen in grouped.items():
        by_attack = defaultdict(list)
        for row in chosen:
            by_attack[_attack_label(row)].append(row["validation_loss"])
        attack_means = {label: sum(values) / len(values) for label, values in sorted(by_attack.items())}
        clean = [row for row in chosen if _attack_label(row) == "clean"]
        classified = [row for row in clean if row["decision"] in {"passed", "failed"}]
        summaries.append({
            "strategy_id": strategy_id,
            "verifiers": list(verifiers),
            "aggregation": aggregation,
            "estimated_cost_ms": cost,
            "decision_loss_by_attack": attack_means,
            "cells": len(chosen),
            "failed_cells": sum(row["execution_status"] != "complete" for row in chosen),
            "clean_candidates": len(clean),
            "clean_coverage": _rate(len(classified), len(clean)),
            "clean_uncertainty": _rate(len(clean) - len(classified), len(clean)),
        })
    return summaries


def _worst(summary: dict, coefficient: float) -> tuple[float, str]:
    penalty = coefficient * summary["estimated_cost_ms"]
    label, loss = max(summary["decision_loss_by_attack"].items(), key=lambda item: item[1] + penalty)
    return loss + penalty, label


def _optimal(summaries: list[dict], coefficient: float, predicate) -> list[dict]:
    chosen = [item for item in summaries if predicate(item)]
    scored = [(_worst(item, coefficient)[0], item) for item in chosen]
    best = min(value for value, _item in scored)
    return [item for value, item in scored if math.isclose(value, best, rel_tol=0.0, abs_tol=1e-9)]


def aggregation_disagreements(cells: list[dict]) -> list[dict]:
    paired = defaultdict(dict)
    for row in cells:
        paired[(tuple(row["verifiers"]), row["candidate_id"], row["attack_id"])][row["aggregation"]] = row["decision"]
    counts = Counter()
    totals = Counter()
    for (verifiers, _candidate, _attack), decisions in paired.items():
        totals[verifiers] += 1
        if len(decisions) == 2 and decisions["reputation_weighted"] != decisions["dependency_group"]:
            counts[verifiers] += 1
    return [
        {"verifiers": list(verifiers), "cells": totals[verifiers], "decision_disagreements": counts[verifiers]}
        for verifiers in sorted(totals)
    ]


def attacked_report_counts(examples: list[dict]) -> list[dict]:
    counts = Counter()
    for example in examples:
        for attack in _attacks():
            reports = _condition_reports(example, attack)
            label = attack.kind if not attack.members else attack.kind + " [" + ",".join(attack.members) + "]"
            for name, report in reports.items():
                if not hasattr(report, "metadata"):
                    counts[(example["benchmark"], label, name, "transform_failed")] += 1
                    continue
                decision = (report.metadata or {}).get("decision")
                counts[(example["benchmark"], label, name, str(decision))] += 1
    return [
        {"benchmark": benchmark, "attack": attack, "verifier": verifier, "decision": decision, "count": count}
        for (benchmark, attack, verifier, decision), count in sorted(counts.items())
    ]


def diagnose_strategies(examples: list[dict], stored_policies: dict) -> dict:
    scored = score(examples)
    matrix = _matrix(scored["strategies"], scored["attacks"], scored["cells"])
    policies = _policies(matrix)
    context = experiment_context()
    enumerated = enumerate_strategies(context)
    summaries = _strategy_rows(scored["cells"])
    means = frozen_calibration()["means_ms"]
    counterfactuals = []
    for scenario in coefficient_scenarios(means):
        coefficient = scenario["value_loss_per_ms"]
        optimal = _optimal(summaries, coefficient, lambda _item: True)
        counterfactuals.append({
            "scenario_id": scenario["id"],
            "loss_per_ms": coefficient,
            "evidence_class": "COUNTERFACTUAL_ON_STORED_EMPIRICAL_REPORTS",
            "optimal_strategies": [
                {"verifiers": item["verifiers"], "aggregation": item["aggregation"], "worst_augmented_loss": _worst(item, coefficient)[0]}
                for item in optimal
            ],
        })
    selected_coefficient_optimal = _optimal(summaries, COEFFICIENT, lambda _item: True)
    by_method = {}
    for method, policy in policies.items():
        modal = next(item for item in summaries if item["strategy_id"] == policy["modal_strategy_id"])
        if method == "fixed_dependency_group":
            restricted = _optimal(summaries, COEFFICIENT, lambda item: item["aggregation"] == "dependency_group")
        elif method == "fixed_reputation_weighted":
            restricted = _optimal(summaries, COEFFICIENT, lambda item: item["aggregation"] == "reputation_weighted")
        else:
            restricted = _optimal(summaries, COEFFICIENT, lambda _item: True)
        by_method[method] = {
            "modal_strategy_id": policy["modal_strategy_id"],
            "stored_modal_strategy_id": stored_policies[method]["modal_strategy_id"],
            "modal_matches_stored_results": policy["modal_strategy_id"] == stored_policies[method]["modal_strategy_id"],
            "game_value": policy["game_value"],
            "stored_game_value": stored_policies[method]["game_value"],
            "verifiers": modal["verifiers"],
            "aggregation": modal["aggregation"],
            "pure": max(probability for _strategy, probability in policy["probabilities"]) >= 1.0 - 1e-8,
            "optimal_strategy_count": len(restricted),
            "optimal_verifiers": [list(team) for team in sorted({tuple(item["verifiers"]) for item in restricted})],
        }
    ranked = []
    for item in summaries:
        worst, attack = _worst(item, COEFFICIENT)
        ranked.append({
            "verifiers": item["verifiers"],
            "aggregation": item["aggregation"],
            "strategy_id": item["strategy_id"],
            "estimated_cost_ms": item["estimated_cost_ms"],
            "resource_penalty": COEFFICIENT * item["estimated_cost_ms"],
            "worst_augmented_loss": worst,
            "worst_attack": attack,
            "decision_loss_by_attack": item["decision_loss_by_attack"],
            "failed_cells": item["failed_cells"],
            "clean_candidates": item["clean_candidates"],
            "clean_coverage": item["clean_coverage"],
            "clean_uncertainty": item["clean_uncertainty"],
        })
    ranked.sort(key=lambda item: (item["worst_augmented_loss"], item["estimated_cost_ms"], item["aggregation"]))
    return {
        "feasible_strategy_count": len(scored["strategies"]),
        "rejected": [
            {"verifiers": list(item.verifiers), "reasons": list(item.reasons)}
            for item in enumerated.rejected
        ],
        "budget_ms": BUDGET_MS,
        "coefficient": COEFFICIENT,
        "minimum_participants": context.minimum_participant_count,
        "strategies": ranked,
        "methods": by_method,
        "selected_coefficient_optimal": [
            {"verifiers": item["verifiers"], "aggregation": item["aggregation"], "worst_augmented_loss": _worst(item, COEFFICIENT)[0]}
            for item in selected_coefficient_optimal
        ],
        "aggregation_disagreements": aggregation_disagreements(scored["cells"]),
        "coefficient_counterfactuals": counterfactuals,
        "tie_break": "The solver returns one distribution. The recorded modal strategy is the maximum of (probability, strategy_id). Strategies with the same worst-case loss are optimal even when that distribution puts probability 1 on only one of them.",
        "attacked_reports": attacked_report_counts(examples),
    }


def build_diagnosis(root: Path | None = None, *, rescore: bool = True) -> dict:
    root = Path(root) if root is not None else ROOT
    empirical = root / "evaluation/experiments/experiment3/empirical"
    results = json.loads((empirical / "results.json").read_text(encoding="utf-8"))
    metrics = json.loads((empirical / "metrics.json").read_text(encoding="utf-8"))
    bootstrap = json.loads((empirical / "bootstrap_results.json").read_text(encoding="utf-8"))
    rows = results["rows"]
    hashes = protected_hashes()
    payload = {
        "record_type": "experiment3_policy_diagnosis_v1",
        "evidence_label": "EMPIRICAL",
        "calibration_id": CALIBRATION_ID,
        "seed": SEED,
        "loss": {"false_accept": LOSS.false_accept, "false_reject": LOSS.false_reject, "uncertain": LOSS.uncertain},
        "hashes": hashes,
        "published_hashes_match": {name: hashes[name] == digest for name, digest in PUBLISHED_HASHES.items()},
        "audit": audit_results(results, rows),
        "reproduction": reproduction_check(rows, metrics, bootstrap),
        "slices": slice_tables(rows),
        "verifier_summary": verifier_summary(empirical / "verifier_reports.jsonl"),
        "cold_start": cold_start_controlled_example(),
    }
    if rescore:
        examples = load_examples(root)
        stored = {}
        reports_path = empirical / "verifier_reports.jsonl"
        with reports_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    item = json.loads(line)
                    stored[item["candidate_id"]] = item["reports"]
        for example in examples:
            example["reports"] = stored[example["candidate_id"]]
        payload["policy"] = diagnose_strategies(examples, results["policies"])
    return payload


def write_diagnosis(root: Path | None = None, *, rescore: bool = True) -> Path:
    before = protected_hashes()
    payload = build_diagnosis(root, rescore=rescore)
    destination = DIAGNOSIS if root is None else Path(root) / "evaluation/experiments/experiment3/empirical/diagnosis/policy_diagnosis.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    after = protected_hashes()
    if before != after:
        raise RuntimeError("diagnosis write changed a protected empirical file")
    return destination


def main() -> None:
    path = write_diagnosis(rescore=True)
    print(path)


if __name__ == "__main__":
    main()
