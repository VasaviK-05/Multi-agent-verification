"""Experiment 3 ablation v1.

Replays the preserved Development verifier reports. It does not call verifiers,
does not write into the historical empirical directory, and does not open Final Test files.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.decision.decision_engine import DecisionEngine
from app.game.decision_inputs import FrozenReputationSnapshot
from app.game.models import PayoffProvenance
from app.game.strategies import enumerate_strategies
from evaluation.experiments.experiment3.ablation_v1.documents import write_documents
from evaluation.experiments.experiment3.ablation_v1.failures import (
    ABSTENTION_POLICY,
    OPERATOR,
    SEED,
    apply_attack,
    declared_registry,
    group_members,
    independent_attacks,
    matched_attacks,
    native_attacks,
    paired_group_difference,
    registries,
    severity,
)
from evaluation.experiments.experiment3.ablation_v1.figures import (
    aggregation_figure,
    dependency_coverage_heatmap,
    dependency_loss_heatmap,
    difference_figure,
)
from evaluation.experiments.experiment3.empirical_executor import (
    LOSS,
    VERIFIERS,
    _attempt,
    _matrix,
    _policies,
    load_examples,
    score,
)
from evaluation.experiments.experiment3.execution_readiness import BUDGET_MS, COEFFICIENT
from evaluation.experiments.experiment3.resource_sensitivity import frozen_calibration

OUTPUT = ROOT / "evaluation/experiments/experiment3/ablation_v1/outputs"
REPORTS = ROOT / "evaluation/experiments/experiment3/empirical/verifier_reports.jsonl"
HISTORICAL_RESULTS = ROOT / "evaluation/experiments/experiment3/empirical/results.json"
ASSUMPTIONS = ("declared_structural", "independent", "fully_correlated")
SCENARIOS = ("independent_failures", "correlated_failures")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _refuse_output(path: Path) -> None:
    text = path.resolve().as_posix().lower()
    if "final_test" in text or text.endswith("/empirical") or "/empirical/" in text:
        raise RuntimeError("refusing to write ablation output over historical or Final Test data")


def _dump(path: Path, payload: dict) -> None:
    _refuse_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_collected(root: Path) -> list[dict]:
    examples = load_examples(root)
    stored = {}
    with REPORTS.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                item = json.loads(line)
                stored[item["candidate_id"]] = item["reports"]
    missing = [example["candidate_id"] for example in examples if example["candidate_id"] not in stored]
    if missing:
        raise RuntimeError(f"{len(missing)} candidates have no saved verifier report")
    for example in examples:
        example["reports"] = stored[example["candidate_id"]]
    return examples


def context_for(registry):
    from tests.test_game_foundation import make_context
    means = frozen_calibration()["means_ms"]
    return make_context(
        names=VERIFIERS, minimum=2, budget=BUDGET_MS,
        attempt_costs=[(name, means[name]) for name in VERIFIERS],
        cost_units="ms", loss_configuration=LOSS, dependencies=registry,
        provenance=PayoffProvenance(
            attack_specification="report_corruption_v1", history_dataset="no-approved-history",
            development_dataset="research-v1-exploratory-v1", final_test_dataset="final-test-excluded",
            matrix_version="experiment3-ablation-v1", loss_configuration=LOSS.version,
            category="general", evidence_kind="empirical"),
    )


def _loss(status: str, correct: bool) -> float:
    if status == "passed":
        return 0.0 if correct else LOSS.false_accept
    if status == "failed":
        return 0.0 if not correct else LOSS.false_reject
    return LOSS.uncertain


def _attempts(example: dict) -> dict:
    return {name: _attempt(name, example["reports"][name]["result"], example["candidate_id"]) for name in VERIFIERS}


def _prepare(example: dict, attack) -> tuple[dict, tuple[dict, ...]]:
    report = example["reports"]
    for name in VERIFIERS:
        if not report[name].get("ok"):
            raise RuntimeError(f"{example['candidate_id']} {name} has no saved successful report")
    transformed, audits = apply_attack(_attempts(example), attack)
    parsed = {}
    for name in VERIFIERS:
        row = transformed[name].report
        if row is None:
            raise RuntimeError(f"{name} report was removed")
        parsed[name] = row
    return parsed, audits


def _rates(decisions: list[str], golds: list[str]) -> dict:
    false_accept = false_reject = negatives = positives = classified = errors = uncertain = 0
    for decision, gold in zip(decisions, golds):
        if decision not in {"passed", "failed"}:
            uncertain += 1
            continue
        classified += 1
        correct = gold == "VERIFIED_CORRECT"
        accepted = decision == "passed"
        if accepted and not correct:
            false_accept += 1
            errors += 1
        elif not accepted and correct:
            false_reject += 1
            errors += 1
        if correct:
            positives += 1
        else:
            negatives += 1
    return {
        "false_acceptance_rate": None if negatives == 0 else false_accept / negatives,
        "false_rejection_rate": None if positives == 0 else false_reject / positives,
        "false_acceptance_count": false_accept,
        "false_rejection_count": false_reject,
        "classified_negatives": negatives,
        "classified_positives": positives,
        "selective_risk": None if classified == 0 else errors / classified,
        "uncertainty_rate": uncertain / len(decisions),
        "coverage": classified / len(decisions),
        "classified": classified,
        "uncertain": uncertain,
    }


def _score_attack(examples, attack, strategies, snapshot, registry, engine: DecisionEngine) -> dict:
    buckets = {
        strategy.strategy_id: {
            "strategy": strategy,
            "losses": [],
            "decisions": [],
            "groups": [],
        }
        for strategy in strategies
    }
    population = {"targeted_count": len(attack.members), "actually_corrupted": 0, "preserved_abstentions": 0, "candidates": 0}
    for example in examples:
        parsed, audits = _prepare(example, attack)
        column = severity(audits, attack)
        population["candidates"] += 1
        population["actually_corrupted"] += column["actually_corrupted_count"]
        population["preserved_abstentions"] += column["preserved_abstention_count"]
        correct = example["gold_label"] == "VERIFIED_CORRECT"
        for strategy in strategies:
            options = {
                "aggregation": strategy.aggregation,
                "team": strategy.verifiers,
                "snapshot": snapshot,
                "validation_id": example["candidate_id"],
            }
            if strategy.aggregation == "dependency_group":
                options["dependencies"] = registry
            status, _score = engine.decide([parsed[name] for name in strategy.verifiers], **options)
            bucket = buckets[strategy.strategy_id]
            bucket["losses"].append(_loss(status, correct))
            bucket["decisions"].append(status)
            bucket["groups"].append(example["related_group_id"])
    return {"buckets": buckets, "population": population, "attack": attack}


def _column_summary(bucket: dict, golds: list[str]) -> dict:
    losses = bucket["losses"]
    mean_loss = sum(losses) / len(losses)
    penalty = COEFFICIENT * bucket["strategy"].estimated_cost
    return {
        "mean_decision_loss": mean_loss,
        "augmented_loss": mean_loss + penalty,
        "resource_penalty": penalty,
        "estimated_cost_ms": bucket["strategy"].estimated_cost,
        "verifiers": list(bucket["strategy"].verifiers),
        "aggregation": bucket["strategy"].aggregation,
        "strategy_id": bucket["strategy"].strategy_id,
        **_rates(bucket["decisions"], golds),
    }


def _select(scored_attacks: list[dict], golds: list[str], aggregation: str | None) -> dict:
    ids = []
    for strategy_id, bucket in scored_attacks[0]["buckets"].items():
        if aggregation is None or bucket["strategy"].aggregation == aggregation:
            ids.append(strategy_id)
    if not ids:
        return {"status": "unavailable", "reason": "no strategy in the requested aggregation", "validation_loss": None, "tie_count": 0}
    ranked = []
    for strategy_id in ids:
        columns = []
        for scored in scored_attacks:
            summary = _column_summary(scored["buckets"][strategy_id], golds)
            summary["attack_members"] = list(scored["attack"].members)
            columns.append(summary)
        worst_index = max(range(len(columns)), key=lambda index: (columns[index]["augmented_loss"], columns[index]["mean_decision_loss"], columns[index]["attack_members"]))
        ranked.append({
            "worst": columns[worst_index],
            "strategy_id": strategy_id,
            "group_losses_by_attack": {
                tuple(scored["attack"].members): _group_losses(scored["buckets"][strategy_id])
                for scored in scored_attacks
            },
        })
    best = min(item["worst"]["augmented_loss"] for item in ranked)
    tied = [item for item in ranked if abs(item["worst"]["augmented_loss"] - best) <= 1e-9]
    unique_loss = len({round(item["worst"]["mean_decision_loss"], 12) for item in tied}) == 1
    chosen = tied[0]
    return {
        "status": "available" if unique_loss else "tie_with_different_decision_loss",
        "reason": None if unique_loss else "tied optimal teams do not share one decision loss",
        "worst_augmented_loss": best,
        "worst_column_decision_loss": None if not unique_loss else chosen["worst"]["mean_decision_loss"],
        "coverage": None if not unique_loss else chosen["worst"]["coverage"],
        "candidates": len(golds),
        "tied_strategies": [
            {
                "strategy_id": item["strategy_id"],
                "verifiers": item["worst"]["verifiers"],
                "aggregation": item["worst"]["aggregation"],
                "worst_column_decision_loss": item["worst"]["mean_decision_loss"],
                "coverage": item["worst"]["coverage"],
                "estimated_cost_ms": item["worst"]["estimated_cost_ms"],
                "false_acceptance_rate": item["worst"]["false_acceptance_rate"],
                "false_rejection_rate": item["worst"]["false_rejection_rate"],
                "selective_risk": item["worst"]["selective_risk"],
                "uncertainty_rate": item["worst"]["uncertainty_rate"],
                "worst_attack_members": item["worst"]["attack_members"],
            }
            for item in tied
        ],
        "selected_losses": chosen["worst"],
        "selected_bucket_id": chosen["strategy_id"],
        "group_losses_by_attack": chosen["group_losses_by_attack"],
        "tie_count": len(tied),
    }


def _group_losses(bucket: dict) -> dict[str, list[float]]:
    grouped: dict[str, list[float]] = {}
    for group, loss in zip(bucket["groups"], bucket["losses"]):
        grouped.setdefault(group, []).append(loss)
    return grouped


def _attack_index(scored_attacks: list[dict], members: list[str]) -> int:
    target = tuple(members)
    for index, attack in enumerate(scored_attacks):
        if tuple(attack["attack"].members) == target:
            return index
    raise KeyError(members)


def reproduce_neutral(examples: list[dict]) -> dict:
    scored = score(examples)
    policies = _policies(_matrix(scored["strategies"], scored["attacks"], scored["cells"]))
    stored = json.loads(HISTORICAL_RESULTS.read_text(encoding="utf-8"))
    comparisons = {}
    disagreements = 0
    compared = 0
    by_key = {}
    for cell in scored["cells"]:
        by_key[(cell["candidate_id"], cell["attack_id"], cell["aggregation"], tuple(cell["verifiers"]))] = cell["decision"]
    aggregations = {}
    for cell in scored["cells"]:
        aggregations.setdefault((cell["candidate_id"], cell["attack_id"], tuple(cell["verifiers"])), {})[cell["aggregation"]] = cell["decision"]
    for decisions in aggregations.values():
        if len(decisions) == 2:
            compared += 1
            if decisions["reputation_weighted"] != decisions["dependency_group"]:
                disagreements += 1
    for method, policy in policies.items():
        modal = policy["modal_strategy_id"]
        losses = [cell["validation_loss"] for cell in scored["cells"] if cell["strategy_id"] == modal and cell["validation_loss"] is not None]
        covered = [cell for cell in scored["cells"] if cell["strategy_id"] == modal]
        coverage = sum(cell["decision"] in {"passed", "failed"} for cell in covered) / len(covered)
        stored_policy = stored["policies"][method]
        fresh = {strategy: probability for strategy, probability in policy["probabilities"]}
        saved = {item[0]: item[1] for item in stored_policy["probabilities"]}
        same_probabilities = fresh.keys() == saved.keys() and all(abs(fresh[key] - saved[key]) <= 1e-8 for key in fresh)
        comparisons[method] = {
            "modal_strategy_id": modal,
            "stored_modal_strategy_id": stored_policy["modal_strategy_id"],
            "modal_matches": modal == stored_policy["modal_strategy_id"],
            "game_value": policy["game_value"],
            "stored_game_value": stored_policy["game_value"],
            "game_value_matches": abs(policy["game_value"] - stored_policy["game_value"]) <= 1e-12,
            "probabilities_match": same_probabilities,
            "mean_decision_loss": sum(losses) / len(losses),
            "coverage": coverage,
            "rows": len(covered),
            "pure_solver_probability_is_not_superiority": True,
        }
    optimal = {}
    for method, policy in policies.items():
        best = max(probability for _strategy, probability in policy["probabilities"])
        optimal[method] = {
            "solver_maximum_probability": best,
            "strategies_with_that_probability": [
                strategy for strategy, probability in policy["probabilities"] if abs(probability - best) <= 1e-8
            ],
        }
    group_losses = {}
    for method, policy in policies.items():
        per_attack = {}
        for cell in scored["cells"]:
            if cell["strategy_id"] != policy["modal_strategy_id"] or cell["validation_loss"] is None:
                continue
            per_attack.setdefault((cell["related_group_id"], cell["attack_id"]), []).append(cell["validation_loss"])
        by_group = {}
        for (group, _attack), values in per_attack.items():
            by_group.setdefault(group, []).append(sum(values) / len(values))
        group_losses[method] = by_group
    match = all(item["modal_matches"] and item["game_value_matches"] and item["probabilities_match"] for item in comparisons.values())
    return {
        "status": "reproduced" if match and disagreements == 0 else "mismatch",
        "reproduction_matches_historical": match and disagreements == 0,
        "decision_disagreements": disagreements,
        "team_attack_cells_compared": compared,
        "methods": comparisons,
        "solver_support": optimal,
        "tie_note": "full_minimax has two optimal evidence-plus-rule rows. The solver probability does not make one aggregation better.",
        "evidence_label": "EMPIRICAL",
        "reputation": "Beta(1, 1), zero approved observations",
        "aggregation_group_losses": group_losses,
    }


def reputation_sensitivity() -> dict:
    path = ROOT / "evaluation/config/experiments/experiment3_reputation_policy_inputs.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": "not_estimable",
        "reason": "No approved non-neutral reputation snapshot exists. Development outcomes are excluded as a reputation source, observations_count is 0, and the update rule is not approved. No substitute reputations were invented.",
        "observations_count": payload.get("observations_count"),
        "approved": payload.get("approved"),
        "update_rule": payload.get("update_rule"),
        "permitted_history": payload.get("permitted_history"),
        "ran": False,
    }


def _population_record(scored_attacks: list[dict]) -> list[dict]:
    rows = []
    for scored in scored_attacks:
        attack = scored["attack"]
        rows.append({
            "members": list(attack.members),
            "targeted_count": len(attack.members),
            "operator": OPERATOR,
            "abstention_policy": ABSTENTION_POLICY,
            **scored["population"],
        })
    return rows


def _cell(selection: dict, golds: list[str]) -> dict:
    if selection["status"] != "available":
        return {
            "status": selection["status"],
            "reason": selection["reason"],
            "worst_column_decision_loss": None,
            "coverage": None,
            "candidates": len(golds),
            "tie_count": selection.get("tie_count", 0),
            "group_losses_by_attack": {},
        }
    rates = selection["selected_losses"]
    return {
        "status": "available",
        "reason": None,
        "worst_column_decision_loss": rates["mean_decision_loss"],
        "coverage": rates["coverage"],
        "uncertainty_rate": rates["uncertainty_rate"],
        "false_acceptance_rate": rates["false_acceptance_rate"],
        "false_rejection_rate": rates["false_rejection_rate"],
        "selective_risk": rates["selective_risk"],
        "estimated_cost_ms": rates["estimated_cost_ms"],
        "resource_penalty": rates["resource_penalty"],
        "candidates": len(golds),
        "verifiers": rates["verifiers"],
        "aggregation": rates["aggregation"],
        "strategy_id": rates["strategy_id"],
        "worst_attack_members": rates["attack_members"],
        "tie_count": selection["tie_count"],
        "tied_strategies": selection["tied_strategies"],
        "group_losses_by_attack": selection["group_losses_by_attack"],
    }


def run_dependency(examples: list[dict]) -> dict:
    engine = DecisionEngine(threshold=0.55)
    golds = [example["gold_label"] for example in examples]
    native = {}
    matched = {}
    group_cache = {}
    for assumption, registry in registries().items():
        context = context_for(registry)
        enumerated = enumerate_strategies(context)
        if enumerated.status != "feasible":
            raise RuntimeError(f"{assumption} admits no strategy")
        snapshot = FrozenReputationSnapshot.from_planning_context(context)
        strategies = enumerated.strategies
        native_sets = native_attacks(assumption)
        native[assumption] = {"groups": [list(members) for members in group_members(registry)], "scenarios": {}}
        for scenario in SCENARIOS:
            print(json.dumps({"scoring": assumption, "scenario": scenario, "columns": len(native_sets[scenario])}), flush=True)
            scored = [_score_attack(examples, attack, strategies, snapshot, registry, engine) for attack in native_sets[scenario]]
            selection = _select(scored, golds, "dependency_group")
            cell = _cell(selection, golds)
            group_cache[(assumption, scenario, "native")] = cell.pop("group_losses_by_attack")
            cell["failure_columns"] = _population_record(scored)
            cell["severity_matched_to_other_rows"] = scenario == "independent_failures"
            native[assumption]["scenarios"][scenario] = cell
        matched[assumption] = {"scenarios": {}}
        for scenario, attacks in matched_attacks().items():
            print(json.dumps({"scoring_matched": assumption, "scenario": scenario, "columns": len(attacks)}), flush=True)
            scored = [_score_attack(examples, attack, strategies, snapshot, registry, engine) for attack in attacks]
            selection = _select(scored, golds, "dependency_group")
            full = _select(scored, golds, None)
            reputation = _select(scored, golds, "reputation_weighted")
            cell = _cell(selection, golds)
            group_cache[(assumption, scenario, "matched")] = cell.pop("group_losses_by_attack")
            cell["failure_columns"] = _population_record(scored)
            cell["full_minimax_tie_count"] = full.get("tie_count")
            cell["full_minimax_status"] = full.get("status")
            cell["full_minimax_worst_column_decision_loss"] = full.get("worst_column_decision_loss")
            cell["reputation_only_tie_count"] = reputation.get("tie_count")
            cell["reputation_only_worst_column_decision_loss"] = reputation.get("worst_column_decision_loss")
            cell["reputation_only_verifiers"] = None if reputation.get("status") != "available" else reputation["selected_losses"]["verifiers"]
            cell["aggregation_disagreements_on_selected_dependency_team"] = _aggregation_disagreements(scored, selection)
            matched[assumption]["scenarios"][scenario] = cell
    return {"native": native, "matched": matched, "group_cache": group_cache, "candidates": len(examples), "groups": len({example["related_group_id"] for example in examples})}


def _aggregation_disagreements(scored_attacks: list[dict], selection: dict) -> int:
    if selection.get("status") != "available":
        return 0
    verifiers = tuple(selection["selected_losses"]["verifiers"])
    disagreements = 0
    for scored in scored_attacks:
        buckets = [bucket for bucket in scored["buckets"].values() if tuple(bucket["strategy"].verifiers) == verifiers]
        if len(buckets) != 2:
            continue
        left, right = buckets
        disagreements += sum(a != b for a, b in zip(left["decisions"], right["decisions"]))
    return disagreements


def _differences(neutral: dict, dependency: dict) -> list[dict]:
    rows = []
    losses = neutral["aggregation_group_losses"]
    for method in ("fixed_reputation_weighted", "fixed_dependency_group"):
        summary = paired_group_difference(losses[method], losses["full_minimax"], seed=SEED)
        rows.append({
            "label": f"{method} minus joint",
            "family": "aggregation_neutral",
            "reference": "full_minimax",
            "mean": summary["mean"],
            "lower": summary["lower"],
            "upper": summary["upper"],
            "exact_ties": summary["exact_ties"],
            "groups": summary["groups"],
            "calculated": True,
            "reason": summary["reason"],
        })
    cache = dependency["group_cache"]
    for scenario in SCENARIOS:
        reference = cache[("declared_structural", scenario, "matched")]
        worst = tuple(dependency["matched"]["declared_structural"]["scenarios"][scenario]["worst_attack_members"])
        if worst not in reference:
            raise RuntimeError("declared worst failure column has no group losses")
        for assumption in ("independent", "fully_correlated"):
            other = cache[(assumption, scenario, "matched")]
            if worst not in other:
                raise RuntimeError(f"{assumption} was not scored on the declared worst column")
            summary = paired_group_difference(other[worst], reference[worst], seed=SEED)
            rows.append({
                "label": f"{assumption} {scenario} minus declared",
                "family": "dependency_matched",
                "reference": "declared_structural",
                "scenario": scenario,
                "mean": summary["mean"],
                "lower": summary["lower"],
                "upper": summary["upper"],
                "exact_ties": summary["exact_ties"],
                "groups": summary["groups"],
                "calculated": True,
                "severity_matched": True,
                "reason": summary["reason"],
            })
    return rows


def _matrix_view(native: dict) -> dict:
    view = {}
    for assumption in ASSUMPTIONS:
        view[assumption] = {}
        for scenario in SCENARIOS:
            cell = native[assumption]["scenarios"][scenario]
            view[assumption][scenario] = {
                "status": cell["status"],
                "worst_column_decision_loss": cell.get("worst_column_decision_loss"),
                "coverage": cell.get("coverage"),
                "candidates": cell.get("candidates"),
                "reason": cell.get("reason"),
            }
    return view


def main() -> int:
    _refuse_output(OUTPUT)
    before = _sha256(REPORTS)
    examples = load_collected(ROOT)
    if len(examples) != 744 or len({example["related_group_id"] for example in examples}) != 372:
        raise RuntimeError("the saved Development population is not 744 candidates and 372 groups")
    neutral = reproduce_neutral(examples)
    if not neutral["reproduction_matches_historical"]:
        _dump(OUTPUT / "neutral_reproduction.json", neutral)
        raise RuntimeError("neutral reproduction does not match the preserved Experiment 3 results")
    dependency = run_dependency(examples)
    differences = _differences(neutral, dependency)
    neutral.pop("aggregation_group_losses", None)
    for row in differences:
        if row["mean"] is None or row["lower"] is None or row["upper"] is None:
            raise RuntimeError("a required paired interval was not calculated")
    after = _sha256(REPORTS)
    if before != after:
        raise RuntimeError("the saved verifier reports changed")
    native_view = _matrix_view(dependency["native"])
    for assumption in ASSUMPTIONS:
        for scenario in SCENARIOS:
            cell = native_view[assumption][scenario]
            if cell["status"] != "available" or cell["worst_column_decision_loss"] is None:
                raise RuntimeError(f"required cell {assumption} {scenario} is not available")
    payload = {
        "record_type": "experiment3_ablation_v1",
        "reports_sha256": before,
        "reports_unchanged": True,
        "candidates": 744,
        "groups": 372,
        "aggregation": {"neutral": neutral, "non_neutral_reputation": reputation_sensitivity()},
        "dependency": {
            "native": dependency["native"],
            "matched": dependency["matched"],
            "native_matrix": native_view,
            "abstention_policy": ABSTENTION_POLICY,
            "operator": OPERATOR,
        },
        "differences": differences,
    }
    # Group-loss maps are large and are not required in the public result file.
    _dump(OUTPUT / "results.json", payload)
    figures = OUTPUT / "figures"
    aggregation_figure(OUTPUT / "results.json", figures / "aggregation_ablation_grouped_bars.svg")
    dependency_loss_heatmap(OUTPUT / "results.json", figures / "dependency_robustness_heatmap.svg")
    dependency_coverage_heatmap(OUTPUT / "results.json", figures / "dependency_coverage_heatmap.svg")
    difference_figure(OUTPUT / "results.json", figures / "ablation_effect_differences.svg")
    docs = ROOT / "evaluation/docs"
    note = OUTPUT / "test_results.md"
    if note.is_file():
        payload["test_results"] = note.read_text(encoding="utf-8")
    write_documents(payload, docs)
    print(json.dumps({"status": "completed", "reports_unchanged": True, "neutral": neutral["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
