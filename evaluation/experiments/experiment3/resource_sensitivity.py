"""SYNTHETIC / CONFIGURATION-SENSITIVITY ANALYSIS for Experiment 3.

The grid is a research-lead choice set. It does not select a coefficient or a
budget, does not collect Development attempts, and does not sign approvals.
"""

from pathlib import Path
import hashlib
import json
import math
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.game.dependencies import DependencyRegistry
from app.game.models import LossConfiguration, PayoffMatrix, PayoffProvenance, content_id
from app.game.offline.evaluation import summarize
from app.game.research.comparison import restricted_matrix
from app.game.solver import solve_minimax
from app.game.strategies import enumerate_strategies
from tests.test_game_foundation import make_context

LABEL = "SYNTHETIC / CONFIGURATION-SENSITIVITY ANALYSIS"
LOSS_PER_MS = "loss_per_ms"
MILLISECONDS = "ms"
VERIFIERS = ("semantic", "evidence", "rule", "confidence")
DECLARED_ATTACKS = ("clean", "forced_support", "forced_rejection", "confidence_inflation")
METHODS = ("full_minimax", "fixed_reputation_weighted", "fixed_dependency_group")
AGGREGATION_OF_METHOD = {
    "fixed_reputation_weighted": "reputation_weighted",
    "fixed_dependency_group": "dependency_group",
}
# Weights implied by every row of the checked-in synthetic fixture. They are
# fixture units, not milliseconds, and they are not a protocol coefficient.
FIXTURE_FALSE_ACCEPT = 1.0
FIXTURE_FALSE_REJECT = 1.0
FIXTURE_UNCERTAIN = 0.2
FIXTURE_RESOURCE_WEIGHT = 0.1
PROPOSAL_FALSE_ACCEPT = 1.0
PROPOSAL_FALSE_REJECT = 1.0
PROPOSAL_UNCERTAIN = 0.2
TOLERANCE = 1e-8

EXPERIMENT = ROOT / "evaluation" / "experiments" / "experiment3"
DEFAULT_DIR = EXPERIMENT / "sensitivity"
DEFAULT_DOC = ROOT / "evaluation" / "docs" / "experiment3_resource_sensitivity.md"
FIXTURE_PATH = EXPERIMENT / "synthetic" / "results.json"
RESOURCE_PROPOSAL = EXPERIMENT / "approval_package" / "resource_configuration_proposal.json"
SETTINGS_PROPOSAL = ROOT / "evaluation" / "config" / "experiments" / "experiment3_settings_proposal.json"
CALIBRATION_FILE = ROOT / "artifacts" / "research-v1-development-cost-calibration-v1" / "calibration.json"
PRESERVED = (
    EXPERIMENT / "synthetic",
    EXPERIMENT / "empirical",
    EXPERIMENT / "approval_package",
    EXPERIMENT / "hypothetical",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _dump(payload) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _fmt(value) -> str:
    return format(value, ".17g")


def _loss_fmt(value) -> str:
    return format(value, ".12g")


def assert_safe_output(path: Path) -> None:
    """Refuse to overwrite preserved synthetic, empirical, or approval artifacts."""
    resolved = path.resolve()
    for preserved in PRESERVED:
        ban = preserved.resolve()
        if resolved == ban or ban in resolved.parents:
            raise RuntimeError(f"refusing to write into preserved artifacts: {resolved}")


def frozen_calibration() -> dict:
    """Means from the frozen calibration. Their sum is recorded and is not a budget."""
    proposal = json.loads(RESOURCE_PROPOSAL.read_text(encoding="utf-8"))
    means = {name: float(proposal["mean_attempt_cost_ms"][name]) for name in VERIFIERS}
    recorded_sum = float(proposal["full_roster_mean_sum_ms"])
    if proposal["resource_coefficient"] is not None or proposal["verifier_budget_ms"] is not None:
        raise RuntimeError("resource proposal unexpectedly contains a selected coefficient or budget")
    if proposal["approved"] is not False:
        raise RuntimeError("resource proposal is not an unsigned proposal")
    calibration_sha = _sha256(CALIBRATION_FILE)
    recorded_sha = proposal["calibration_sha256"]
    return {
        "calibration_id": proposal["calibration_id"],
        "method": proposal["measurement_method"],
        "unit": MILLISECONDS,
        "means_ms": means,
        "recorded_four_verifier_sum_ms": recorded_sum,
        "computed_four_verifier_sum_ms": math.fsum(means[name] for name in VERIFIERS),
        "four_verifier_sum_is_a_selected_budget": False,
        "policy_fitting_or_budget_selection_authorized_by_freeze": False,
        "calibration_sha256": calibration_sha,
        "calibration_sha256_matches_proposal": calibration_sha == recorded_sha,
        "source": str(RESOURCE_PROPOSAL.relative_to(ROOT)).replace("\\", "/"),
    }


def loss_configuration(weight: float) -> LossConfiguration:
    if weight < 0:
        raise ValueError("resource weight must be nonnegative")
    return LossConfiguration(
        version="sensitivity-loss-v1", false_accept=PROPOSAL_FALSE_ACCEPT,
        false_reject=PROPOSAL_FALSE_REJECT, uncertain=PROPOSAL_UNCERTAIN,
        resource_weight=weight, cost_units=MILLISECONDS)


def coefficient_scenarios(means: dict) -> list[dict]:
    """Loss-per-ms translations of the proposed decision-loss scale. None is selected."""
    confidence = means["confidence"]
    semantic = means["semantic"]
    specs = (
        ("no_resource_penalty", "no resource penalty", 0.0, True,
         "LossConfiguration.resource_weight allows zero. The penalty term is then identically zero. "
         "This is a decision-only reference, not a recommendation to drop cost from the protocol."),
        ("low", "low", PROPOSAL_UNCERTAIN / confidence, False,
         "Proposed uncertainty loss 0.2 divided by the frozen confidence mean. "
         "One confidence attempt then costs the same as one uncertain decision."),
        ("moderate", "moderate", PROPOSAL_FALSE_ACCEPT / confidence, False,
         "Proposed false-acceptance loss 1.0 divided by the frozen confidence mean. "
         "One confidence attempt then costs the same as one false acceptance."),
        ("high", "high", PROPOSAL_UNCERTAIN / semantic, False,
         "Proposed uncertainty loss 0.2 divided by the frozen semantic mean. "
         "One semantic attempt then costs the same as one uncertain decision, so a confidence "
         "attempt costs many false-acceptance losses. Rule is not the denominator: its mean is "
         "under a tenth of a millisecond and would only inflate the same ratio."),
    )
    rows = []
    for identifier, name, value, reference, derivation in specs:
        rows.append({
            "id": identifier,
            "name": name,
            "value_loss_per_ms": value,
            "unit": LOSS_PER_MS,
            "reference_only": reference,
            "selected": False,
            "derivation": derivation,
        })
    return rows


def planning_context(budget: float, weight: float, minimum: int):
    """Synthetic plan: equal capabilities, frozen millisecond costs, real feasibility rule."""
    means = frozen_calibration()["means_ms"]
    loss = loss_configuration(weight)
    return make_context(
        names=VERIFIERS, minimum=minimum, budget=budget,
        attempt_costs=[(name, means[name]) for name in VERIFIERS],
        cost_units=MILLISECONDS, loss_configuration=loss,
        dependencies=DependencyRegistry(version="sensitivity_shared_unknown_v1", unresolved=VERIFIERS),
        provenance=PayoffProvenance(
            attack_specification="single_group_v1", history_dataset="history-v1",
            development_dataset="development-v1", final_test_dataset="test-v1",
            matrix_version="matrix-v1", loss_configuration=loss.version,
            category="general", evidence_kind="synthetic_test_fixture"))


def _team_key(verifiers) -> tuple[str, ...]:
    return tuple(verifiers)


def roster_costs() -> dict:
    """Team costs from enumerate_strategies, not from a hand-added budget."""
    context = planning_context(budget=1e9, weight=0.0, minimum=2)
    result = enumerate_strategies(context)
    if result.status != "feasible":
        raise RuntimeError("large synthetic budget produced no feasible strategy")
    costs = {}
    for strategy in result.strategies:
        team = _team_key(strategy.verifiers)
        costs.setdefault(team, strategy.estimated_cost)
        if not math.isclose(costs[team], strategy.estimated_cost, rel_tol=0.0, abs_tol=0.0):
            raise RuntimeError("one team has two estimated costs")
    if context.minimum_participant_count != 2:
        raise RuntimeError("easy/medium floor did not resolve to 2")
    hard = planning_context(budget=1e9, weight=0.0, minimum=3)
    if hard.minimum_participant_count != 3:
        raise RuntimeError("hard floor did not resolve to 3")
    return costs


def budget_scenarios(costs: dict) -> list[dict]:
    """Restrictive, moderate, and permissive caps, plus the confidence-entry boundary."""
    def cost_of(predicate):
        teams = [team for team in costs if predicate(team)]
        if not teams:
            raise RuntimeError("budget threshold has no team")
        team = min(teams, key=lambda item: (costs[item], item))
        return team, costs[team]

    cheapest_pair, pair_cost = cost_of(lambda team: len(team) == 2)
    nonconfidence, nonconfidence_cost = cost_of(
        lambda team: len(team) == 3 and "confidence" not in team)
    confidence_triple, confidence_cost = cost_of(
        lambda team: len(team) == 3 and "confidence" in team)
    full, full_cost = cost_of(lambda team: len(team) == 4)
    specs = (
        ("restrictive", "restrictive", cheapest_pair, pair_cost, False,
         "Estimated cost of the cheapest two-verifier team under enumerate_strategies. "
         "At the easy/medium floor this admits only that pair. At the hard floor it admits nothing, "
         "because every size-3 team costs more."),
        ("moderate", "moderate", nonconfidence, nonconfidence_cost, False,
         "Estimated cost of the only three-verifier team that excludes confidence. "
         "Every confidence team costs more, so confidence is infeasible at both participant floors. "
         "Equality is feasible: enumerate_strategies rejects only a strict cost excess."),
        ("confidence_entry", "confidence boundary", confidence_triple, confidence_cost, False,
         "Estimated cost of the cheapest three-verifier team that includes confidence. "
         "This is the smallest cap at which the hard floor can field confidence. "
         "It is a boundary used to explain the confidence cost, not a fourth protocol level."),
        ("permissive", "permissive", full, full_cost, True,
         "Estimated cost of the four-verifier team. It equals the sum of the frozen means and is "
         "the smallest cap that admits every team. The sum is not a selected protocol budget."),
    )
    rows = []
    for identifier, name, team, value, sum_threshold, derivation in specs:
        rows.append({
            "id": identifier,
            "name": name,
            "value_ms": value,
            "unit": MILLISECONDS,
            "defining_team": list(team),
            "not_a_protocol_budget": True,
            "uses_four_verifier_sum": sum_threshold,
            "selected": False,
            "derivation": derivation,
        })
    return rows


def floors() -> list[dict]:
    return [
        {"id": "participant_floor_2", "minimum_participant_count": 2, "selected": False,
         "implementation": "Non-hard PlanningContext uses max(2, plan.minimum_count). "
         "The default easy and medium bands are (2, 2) and (2, 3)."},
        {"id": "participant_floor_3", "minimum_participant_count": 3, "selected": False,
         "implementation": "The default hard band is (3, 4), and a hard plan uses plan.minimum_count. "
         "This context sets that minimum to 3."},
    ]


def _recover_decision(row: dict) -> tuple[float, float, float]:
    decision = (row["false_acceptance"] * FIXTURE_FALSE_ACCEPT
                + row["false_rejection"] * FIXTURE_FALSE_REJECT
                + row["uncertainty"] * FIXTURE_UNCERTAIN)
    penalty = FIXTURE_RESOURCE_WEIGHT * row["cost"]
    return decision, penalty, decision + penalty - row["loss"]


def fixture_decision(path: Path = FIXTURE_PATH) -> dict:
    """Split the checked-in synthetic losses. The file is not rewritten."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("output_class") != "SYNTHETIC" or payload.get("empirical_claim") is not False:
        raise RuntimeError("synthetic fixture is not labeled as a non-empirical result")
    configurations = {}
    checked = 0
    max_error = 0.0
    for name, block in payload["configurations"].items():
        methods = {}
        attack_ids = None
        for method in METHODS:
            rows = []
            for attack in block["methods"][method]["attacks"]:
                decision, penalty, error = _recover_decision(attack)
                checked += 1
                max_error = max(max_error, abs(error))
                item = attack["attack"]
                rows.append({
                    "attack_id": item["attack_id"],
                    "kind": item["kind"],
                    "members": list(item["members"]),
                    "declared": item["kind"] in DECLARED_ATTACKS,
                    "false_acceptance": attack["false_acceptance"],
                    "false_rejection": attack["false_rejection"],
                    "uncertainty": attack["uncertainty"],
                    "coverage": attack["coverage"],
                    "selective_risk": attack["selective_risk"],
                    "fixture_recorded_loss": attack["loss"],
                    "fixture_estimated_cost": attack["cost"],
                    "decision_loss": decision,
                    "fixture_resource_penalty": penalty,
                })
            ids = [row["attack_id"] for row in rows]
            if attack_ids is None:
                attack_ids = ids
            elif ids != attack_ids:
                raise RuntimeError(f"{name} methods do not share one attack-column list")
            declared = [row for row in rows if row["declared"]]
            worst = max(row["decision_loss"] for row in declared)
            methods[method] = {
                "attacks": rows,
                "worst_case_decision_loss": worst,
                "worst_case_attacks": [row["attack_id"] for row in declared if row["decision_loss"] == worst],
                "fixture_aggregation_frequencies": block["methods"][method]["aggregation_selection_frequencies"],
                "fixture_verifier_inclusion": block["methods"][method]["verifier_inclusion_frequencies"],
            }
        configurations[name] = {"methods": methods, "evidence_label": block["evidence_label"]}
    if max_error > 1e-9:
        raise RuntimeError("synthetic fixture loss does not split into decision loss plus 0.1 times cost")
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": _sha256(path),
        "evidence_label": "SYNTHETIC",
        "fixture_verifiers": ["a", "b", "c"],
        "calibrated_roster_scored_by_fixture": False,
        "rows_checked": checked,
        "max_abs_decomposition_error": max_error,
        "decomposition": "decision_loss = 1*false_acceptance + 1*false_rejection + 0.2*uncertainty; "
                         "fixture_resource_penalty = 0.1*fixture_cost; recorded loss is their sum. "
                         "The 0.1 weight is the fixture's own unitless weight, not loss per millisecond.",
        "statistical_uncertainty": "Not estimated. The fixture is one deterministic synthetic case. "
                                   "No bootstrap interval was computed or invented.",
        "configurations": configurations,
    }


def _enumerate(budget: float, minimum: int):
    context = planning_context(budget, 0.0, minimum)
    result = enumerate_strategies(context)
    eligible = sorted(candidate.verifier_name for candidate in context.plan.candidates if candidate.eligible)
    if eligible != sorted(VERIFIERS):
        raise RuntimeError("synthetic plan did not keep the four calibrated verifiers eligible")
    teams = []
    seen = set()
    for strategy in result.strategies:
        team = _team_key(strategy.verifiers)
        if team not in seen:
            seen.add(team)
            teams.append({"verifiers": list(team), "estimated_cost_ms": strategy.estimated_cost,
                          "includes_confidence": "confidence" in team})
    rejected = {}
    for item in result.rejected:
        rejected[tuple(item.verifiers)] = list(item.reasons)
    return context, result, teams, rejected


def _matrix(strategies, attack_ids, decisions, weight: float, compatibility: str) -> PayoffMatrix:
    values = []
    for strategy in strategies:
        penalty = weight * strategy.estimated_cost
        values.append(tuple(decisions[strategy.aggregation][attack] + penalty for attack in attack_ids))
    return PayoffMatrix(
        strategy_ids=tuple(strategy.strategy_id for strategy in strategies),
        strategy_definitions=tuple(strategies), attack_ids=tuple(attack_ids),
        values=tuple(values), compatibility_id=compatibility)


def _solve(matrix: PayoffMatrix) -> dict:
    solution = solve_minimax(matrix)
    worst = [max(row) for row in matrix.values]
    best = min(worst)
    optimal = []
    for strategy, value in zip(matrix.strategy_definitions, worst):
        if value <= best + TOLERANCE:
            optimal.append({"verifiers": list(strategy.verifiers), "aggregation": strategy.aggregation,
                            "estimated_cost_ms": strategy.estimated_cost, "worst_case_loss": value})
    positive = [(name, probability) for name, probability in solution.probabilities if probability > TOLERANCE]
    return {
        "status": solution.status,
        "game_value": solution.game_value,
        "optimal_strategies": optimal,
        "solver_positive_support": [{"strategy_id": name, "probability": probability} for name, probability in positive],
    }


def _overlay(result, fixture_configuration: dict, weight: float, compatibility: str) -> dict:
    if result.status != "feasible":
        return {method: {"status": "not_called", "reason": "no_feasible_strategy"} for method in METHODS}
    reputation = fixture_configuration["methods"]["fixed_reputation_weighted"]["attacks"]
    dependency = fixture_configuration["methods"]["fixed_dependency_group"]["attacks"]
    declared = [row for row in reputation if row["declared"]]
    by_id = {row["attack_id"]: row for row in dependency}
    decisions = {"reputation_weighted": {}, "dependency_group": {}}
    attack_ids = []
    for row in declared:
        attack_ids.append(row["attack_id"])
        decisions["reputation_weighted"][row["attack_id"]] = row["decision_loss"]
        decisions["dependency_group"][row["attack_id"]] = by_id[row["attack_id"]]["decision_loss"]
    full = _matrix(result.strategies, attack_ids, decisions, weight, compatibility)
    solved = {"full_minimax": _solve(full)}
    for method, aggregation in AGGREGATION_OF_METHOD.items():
        solved[method] = _solve(restricted_matrix(full, aggregation))
    return solved


def analyze() -> dict:
    calibration = frozen_calibration()
    if not calibration["calibration_sha256_matches_proposal"]:
        raise RuntimeError("calibration.json hash does not match the resource proposal")
    means = calibration["means_ms"]
    costs = roster_costs()
    coefficients = coefficient_scenarios(means)
    budgets = budget_scenarios(costs)
    floor_rows = floors()
    fixture = fixture_decision()
    enumerations = {}
    cells = []
    for floor in floor_rows:
        for budget in budgets:
            context, result, teams, rejected = _enumerate(budget["value_ms"], floor["minimum_participant_count"])
            if context.minimum_participant_count != floor["minimum_participant_count"]:
                raise RuntimeError("participant floor drifted from the implementation property")
            enumerations[(floor["id"], budget["id"])] = (result, teams, rejected, context.compatibility_id)
            cheapest = min(teams, key=lambda item: (item["estimated_cost_ms"], item["verifiers"])) if teams else None
            for coefficient in coefficients:
                weight = coefficient["value_loss_per_ms"]
                compatibility = content_id(["experiment3-resource-sensitivity", context.compatibility_id,
                                             coefficient["id"], fixture["sha256"]])
                overlays = {name: _overlay(result, block, weight, content_id([compatibility, name]))
                            for name, block in fixture["configurations"].items()}
                penalty = None if cheapest is None else weight * cheapest["estimated_cost_ms"]
                cells.append({
                    "coefficient_id": coefficient["id"],
                    "budget_id": budget["id"],
                    "floor_id": floor["id"],
                    "selected": False,
                    "feasible": result.status == "feasible",
                    "enumeration_status": result.status,
                    "minimum_participant_count": floor["minimum_participant_count"],
                    "feasible_teams": teams,
                    "feasible_strategy_count": len(result.strategies),
                    "confidence_feasible": any(team["includes_confidence"] for team in teams),
                    "full_roster_feasible": any(len(team["verifiers"]) == 4 for team in teams),
                    "cheapest_team": None if cheapest is None else cheapest["verifiers"],
                    "cheapest_team_cost_ms": None if cheapest is None else cheapest["estimated_cost_ms"],
                    "resource_penalty_on_cheapest_team": penalty,
                    "rejected_team_count": len(rejected),
                    "overlays": overlays,
                })
    return {
        "label": LABEL,
        "output_class": "SYNTHETIC",
        "analysis_class": "CONFIGURATION-SENSITIVITY ANALYSIS",
        "empirical_claim": False,
        "selected_configuration": None,
        "collection_executed": False,
        "approval_records_modified": False,
        "calibration": calibration,
        "loss_scale": {
            "false_accept": PROPOSAL_FALSE_ACCEPT,
            "false_reject": PROPOSAL_FALSE_REJECT,
            "uncertain": PROPOSAL_UNCERTAIN,
            "approved": False,
            "source": str(SETTINGS_PROPOSAL.relative_to(ROOT)).replace("\\", "/"),
            "role": "Scale used only to translate milliseconds into loss. Not an approved coefficient.",
        },
        "assumptions": [
            "Attempt costs are the frozen per-verifier means. Measurement variance is not propagated.",
            "Every candidate is given the same synthetic expected capability, so expected coverage does not remove teams. This is not the production capability map.",
            "The dependency registry is shared_unknown for the four names. Dependency groups do not enter the budget test.",
            "Fixture decision losses belong to verifiers a, b, and c. They are overlaid onto every calibrated team of the same aggregation. They are not empirical roster payoffs.",
            "Suppression rows stay in the fixture extract and are excluded from the overlay because the settings proposal sets suppression to unavailable.",
            "resource_weight does not enter enumerate_strategies. The budget does.",
        ],
        "coefficients": coefficients,
        "budgets": budgets,
        "floors": floor_rows,
        "team_costs_ms": [{"verifiers": list(team), "estimated_cost_ms": cost}
                          for team, cost in sorted(costs.items(), key=lambda item: (item[1], item[0]))],
        "fixture": fixture,
        "cells": cells,
        "findings": _findings(cells, coefficients, fixture),
        "recommendation": {
            "coefficient_scientifically_derived": False,
            "budget_scientifically_derived": False,
            "selected_coefficient_id": None,
            "selected_budget_id": None,
            "reason": "The calibration measures milliseconds. The synthetic fixture measures decision loss for verifiers a, b, and c. Neither source identifies a loss-per-millisecond utility.",
        },
    }


def _findings(cells: list, coefficients: list, fixture: dict) -> dict:
    infeasible = [{"coefficient_id": cell["coefficient_id"], "budget_id": cell["budget_id"],
                   "floor_id": cell["floor_id"]}
                  for cell in cells if not cell["feasible"]]
    rankings = {}
    for name, block in fixture["configurations"].items():
        per_attack = []
        declared = [row for row in block["methods"]["full_minimax"]["attacks"] if row["declared"]]
        for attack in declared:
            order = []
            for method in METHODS:
                row = next(item for item in block["methods"][method]["attacks"]
                           if item["attack_id"] == attack["attack_id"])
                order.append((row["decision_loss"], method))
            order.sort()
            per_attack.append({"attack_id": attack["attack_id"], "kind": attack["kind"],
                               "ranking": [method for _loss, method in order]})
        worst_order = sorted((block["methods"][method]["worst_case_decision_loss"], method) for method in METHODS)
        rankings[name] = {
            "by_declared_attack": per_attack,
            "by_worst_case_decision_loss": [method for _loss, method in worst_order],
            "attack_rankings_identical": len({tuple(row["ranking"]) for row in per_attack}) == 1,
        }
    positive = [cell for cell in cells if cell["coefficient_id"] != "no_resource_penalty" and cell["feasible"]]
    zero = [cell for cell in cells if cell["coefficient_id"] == "no_resource_penalty" and cell["feasible"]]

    def teams(cell, method, configuration):
        return {tuple(item["verifiers"]) for item in cell["overlays"][configuration][method]["optimal_strategies"]}

    def cheapest(cell):
        return {tuple(cell["cheapest_team"])}

    def feasible(cell):
        return {tuple(team["verifiers"]) for team in cell["feasible_teams"]}

    configuration_names = list(fixture["configurations"])
    positive_is_cheapest = all(
        teams(cell, method, name) == cheapest(cell)
        for cell in positive for name in configuration_names for method in METHODS)
    zero_is_all_feasible = all(
        teams(cell, method, name) == feasible(cell)
        for cell in zero for name in configuration_names for method in METHODS)
    by_floor = {}
    for cell in positive:
        by_floor.setdefault(cell["floor_id"], set()).add(tuple(cell["cheapest_team"]))
    stable_within_floor = {floor: len(chosen) <= 1 for floor, chosen in by_floor.items()}
    weights = {row["id"]: row["value_loss_per_ms"] for row in coefficients}
    return {
        "infeasible_cells": infeasible,
        "method_rankings_by_decision_loss": rankings,
        "positive_coefficient_selects_cheapest_feasible_team": positive_is_cheapest,
        "zero_weight_selects_every_feasible_team": zero_is_all_feasible,
        "positive_coefficient_team_stable_across_budgets_within_floor": stable_within_floor,
        "confidence_switch_loss": {
            row["id"]: {floor: weights[row["id"]] * _confidence_gap(cells, floor)
                        for floor in ("participant_floor_2", "participant_floor_3")}
            for row in coefficients
        },
    }


def _confidence_gap(cells: list, floor: str) -> float:
    """Millisecond gap from the cheapest feasible team to the cheapest confidence team."""
    sample = next(cell for cell in cells if cell["floor_id"] == floor and cell["budget_id"] == "permissive"
                  and cell["coefficient_id"] == "no_resource_penalty")
    cheap = sample["cheapest_team_cost_ms"]
    confidence_costs = [team["estimated_cost_ms"] for team in sample["feasible_teams"] if team["includes_confidence"]]
    if cheap is None or not confidence_costs:
        raise RuntimeError("permissive floor has no confidence comparison")
    return min(confidence_costs) - cheap


def scenario_document(analysis: dict) -> dict:
    keys = ("label", "output_class", "analysis_class", "empirical_claim", "selected_configuration",
            "calibration", "loss_scale", "assumptions", "coefficients", "budgets", "floors")
    return {key: analysis[key] for key in keys}


def results_document(analysis: dict) -> dict:
    keys = ("label", "output_class", "analysis_class", "empirical_claim", "selected_configuration",
            "collection_executed", "approval_records_modified", "team_costs_ms", "fixture",
            "cells", "findings", "recommendation")
    return {key: analysis[key] for key in keys}


def render_document(analysis: dict) -> str:
    calibration = analysis["calibration"]
    means = calibration["means_ms"]
    findings = analysis["findings"]
    lines = [
        "# Experiment 3 resource-configuration sensitivity",
        "",
        LABEL,
        "",
        "This is a synthetic configuration analysis for the research lead. It is not an empirical "
        "Development result, not a Final Test result, and not a protocol approval. No coefficient "
        "and no budget is selected. Empirical collection was not run. Approval records were not modified.",
        "",
        "## Calibration",
        "",
        f"Frozen method `{calibration['method']}`, calibration `{calibration['calibration_id']}`, "
        f"unit milliseconds. The calibration file hash matches the resource proposal: "
        f"`{calibration['calibration_sha256']}`. The freeze does not authorize budget selection.",
        "",
        "| Verifier | Mean attempt cost (ms) |",
        "|---|---:|",
    ]
    for name in VERIFIERS:
        lines.append(f"| {name} | {_fmt(means[name])} |")
    lines.extend([
        "",
        f"The four means sum to {_fmt(calibration['computed_four_verifier_sum_ms'])} ms. "
        "That sum is the cost of using every verifier once. It is not used here as a protocol budget. "
        "The permissive grid point is the enumerated four-verifier team cost, which is this same sum, "
        "and it is marked `not_a_protocol_budget`.",
        "",
        "Proposed decision-loss scale, still unapproved: false acceptance 1.0, false rejection 1.0, "
        "uncertainty 0.2. Those numbers convert milliseconds into loss. They are not themselves a resource coefficient.",
        "",
        "## Coefficients",
        "",
        "Each value is loss per millisecond. A scientifically justified coefficient cannot be derived "
        "from the calibration or from the synthetic fixture: the calibration has no utility scale, and "
        "the fixture does not score this roster. The rows are translations for the lead to choose among.",
        "",
        "| Id | Loss per ms | How it is obtained |",
        "|---|---:|---|",
    ])
    for row in analysis["coefficients"]:
        lines.append(f"| {row['id']} | {_fmt(row['value_loss_per_ms'])} | {row['derivation']} |")
    lines.extend([
        "",
        "The zero weight is included because `LossConfiguration.resource_weight` allows it (`ge=0`). "
        "`0.1/budget` is not included. The settings proposal rejects it because the penalty would change whenever the budget changes.",
        "",
        "## Budgets",
        "",
        "Budgets are milliseconds. They are the estimated costs `enumerate_strategies` assigns to "
        "particular teams, so a team at the cap is feasible and a team above the cap is not. "
        "None is a protocol budget.",
        "",
        "| Id | Budget (ms) | Defining team | Role |",
        "|---|---:|---|---|",
    ])
    for row in analysis["budgets"]:
        team = ", ".join(row["defining_team"])
        lines.append(f"| {row['id']} | {_fmt(row['value_ms'])} | {team} | {row['derivation']} |")
    lines.extend([
        "",
        "Participant floors come from the implementation, not from an Experiment 3 approval. "
        "Floor 2 is the non-hard minimum (`max(2, plan.minimum_count)` with the easy/medium default). "
        "Floor 3 is the hard-band minimum. The same budget is offered to `full_minimax`, "
        "`fixed_reputation_weighted`, and `fixed_dependency_group`.",
        "",
        "The synthetic plan gives every verifier the same expected capability. Expected coverage "
        "therefore does not eliminate teams. Real capability descriptors are not applied. "
        "Dependency structure does not enter the budget test.",
        "",
        "## Feasibility",
        "",
        "A configuration is infeasible when `enumerate_strategies` returns no strategy. "
        "Infeasible cells are every coefficient at the restrictive budget and the hard floor of 3. "
        f"There are {len(findings['infeasible_cells'])} such cells. The coefficient does not change "
        "feasibility. Confidence is absent from every moderate-budget team and present in every "
        "confidence-entry and permissive team.",
        "",
        "Once any team is feasible, the cheapest team remains feasible at every higher budget. "
        "Raising the budget adds expensive teams. It does not replace the cheapest team.",
        "",
        "## Decision loss and resource penalty",
        "",
        "The checked-in synthetic fixture (`evaluation/experiments/experiment3/synthetic/results.json`) "
        "is read and not rewritten. Its verifiers are a, b, and c. Its recorded loss splits exactly into",
        "",
        "```",
        "decision loss = 1*false_acceptance + 1*false_rejection + 0.2*uncertainty",
        "fixture resource penalty = 0.1 * fixture cost",
        "```",
        "",
        "on every row. The fixture cost is 2.0 in the fixture's own units. That 0.1 is not applied to milliseconds.",
        "",
        "`Metrics.validation_loss` is the decision term. `summarize` adds `resource_weight * estimated_cost` "
        "to produce `mean_loss`. This analysis reports those terms separately. The overlay game is",
        "",
        "```",
        "cell loss = fixture decision loss for that aggregation and attack + coefficient * team cost in ms",
        "```",
        "",
        "The same fixture decision loss is assigned to every calibrated team that uses that aggregation. "
        "That is a sensitivity assumption, not a measurement of semantic, evidence, rule, or confidence.",
        "",
        "No sampling uncertainty is available. The fixture is one deterministic synthetic case. "
        "Coverage and uncertainty below are the fixture's recorded rates, not rates for the calibrated roster.",
        "",
        "| Configuration | Method | Worst decision loss | Coverage on that worst attack | Uncertainty on that worst attack |",
        "|---|---|---:|---:|---:|",
    ])
    for name, block in analysis["fixture"]["configurations"].items():
        for method in METHODS:
            method_block = block["methods"][method]
            worst_ids = set(method_block["worst_case_attacks"])
            worst_rows = [row for row in method_block["attacks"] if row["attack_id"] in worst_ids]
            lines.append(
                f"| {name} | {method} | {_loss_fmt(method_block['worst_case_decision_loss'])} | "
                f"{_loss_fmt(min(row['coverage'] for row in worst_rows))} | "
                f"{_loss_fmt(max(row['uncertainty'] for row in worst_rows))} |")
    lines.extend([
        "",
        "Declared-attack decision loss. Duplicate member lists with the same three losses are one row. "
        "Coverage and uncertainty for every row are in `sensitivity/results.json`.",
        "",
        "| Configuration | Attack | Members | full_minimax | fixed reputation | fixed dependency |",
        "|---|---|---|---:|---:|---:|",
    ])
    seen = set()
    for name, block in analysis["fixture"]["configurations"].items():
        attacks = block["methods"]["full_minimax"]["attacks"]
        for attack in attacks:
            if not attack["declared"]:
                continue
            losses = tuple(
                next(row["decision_loss"] for row in block["methods"][method]["attacks"]
                     if row["attack_id"] == attack["attack_id"])
                for method in METHODS)
            key = (name, attack["kind"], tuple(attack["members"]), losses)
            if key in seen:
                continue
            seen.add(key)
            members = ", ".join(attack["members"]) if attack["members"] else "none"
            lines.append(
                f"| {name} | {attack['kind']} | {members} | "
                + " | ".join(_loss_fmt(value) for value in losses) + " |")
    lines.extend([
        "",
        "Suppression rows are in the machine-readable extract and out of the overlay. "
        "The settings proposal sets suppression to unavailable.",
        "",
        "Where the selected policy changes:",
        "",
        "- The coefficient does not change which teams are feasible. The budget and the participant floor do.",
        "- At zero weight, decision loss does not depend on the team, so every feasible team is optimal. "
        "Shared-unknown still keeps only reputation-weighted aggregation, because its worst decision loss is 1.0 "
        "against 0.2 for the other methods. The controlled two-group fixture ties all three methods at a worst "
        "decision loss of 0.2, so both aggregations stay optimal.",
        "- Any positive coefficient, low or high, drops every team except the cheapest. Low, moderate, and high "
        "select that same team. They change the penalty level, not the argmin.",
        "- Inside one floor the cheapest team does not change as the budget grows. Floor 2 selects rule and semantic. "
        "Floor 3 cannot field a pair, so it selects semantic, evidence, and rule. The restrictive cap at floor 3 "
        "has no feasible policy.",
        "- Attack-level method order is not stable. In the controlled fixture, fixed reputation has decision loss "
        "0.2 on clean, forced support, and confidence inflation, while the other two methods have 0, and all three "
        "tie at 0.2 on forced rejection. In shared-unknown, fixed dependency is best on clean, forced support, and "
        "confidence inflation (0 versus 0.2) and worst on forced rejection (1 versus 0.2). Worst-case minimax follows "
        "the forced-rejection column there and keeps reputation-weighted aggregation. Adding the same millisecond "
        "cost to every method does not reverse those orders.",
        "",
        "Neither fixture configuration is empirical dependence.",
        "",
        "## Confidence cost",
        "",
        f"Confidence is {_fmt(means['confidence'])} ms, "
        f"{_fmt(means['confidence'] / calibration['computed_four_verifier_sum_ms'])} of the four-mean sum. "
        "Any cap below the confidence mean excludes confidence even before the participant floor. "
        "At floor 2 the cheapest confidence team is confidence plus rule. "
        "At floor 3 it is confidence plus semantic plus rule, because a pair is too small.",
        "",
        "The loss gap that confidence must beat, relative to the cheapest team at the permissive cap, is "
        "`coefficient * (confidence team cost - cheapest team cost)`:",
        "",
        "| Coefficient | Floor 2 gap (loss) | Floor 3 gap (loss) | Larger than 0.2 | Larger than 1.0 |",
        "|---|---:|---:|---|---|",
    ])
    for row in analysis["coefficients"]:
        gaps = findings["confidence_switch_loss"][row["id"]]
        lines.append(
            f"| {row['id']} | {_fmt(gaps['participant_floor_2'])} | {_fmt(gaps['participant_floor_3'])} | "
            f"{gaps['participant_floor_2'] > PROPOSAL_UNCERTAIN} | "
            f"{gaps['participant_floor_2'] > PROPOSAL_FALSE_ACCEPT} |")
    lines.extend([
        "",
        "Low prices one confidence attempt at 0.2. The gap versus the cheap pair is just under 0.2, "
        "so a team that removed one uncertain decision could still prefer confidence. "
        "Moderate prices that attempt at 1.0. The gap is just under one false acceptance, so only a "
        "near-complete error reduction would pay for confidence. "
        "High prices one semantic attempt at 0.2 and therefore prices confidence far above 1.0. "
        "On the proposed loss scale, no decision improvement can justify confidence, and a permissive "
        "budget would not change the cost-augmented optimum.",
        "",
        "The high coefficient is the case in which resource cost dominates decision loss for any team "
        "that includes confidence. The low and moderate coefficients do not, except as the near-ties above. "
        "On the cheapest floor-2 team the penalties stay small, because that team excludes confidence.",
        "",
        "## Recommendation",
        "",
        "Do not freeze a coefficient or a budget from this file.",
        "",
        "A scientifically justified coefficient cannot be derived from the existing evidence. "
        "The frozen calibration is a millisecond measurement. The synthetic fixture is a decision-loss "
        "example for a different verifier set. `research_settings_proposal_v1` and "
        "`experiment3_settings_proposal.json` both leave the coefficient unset and reject `0.1/budget`.",
        "",
        "Alternatives for the research lead:",
        "",
        "| Alternative | Consequence in this grid | Why it is not selected here |",
        "|---|---|---|",
        "| Leave both null | The approval gate cannot reach collection. Decision-only loss stays definable. | This is the current unsigned state. |",
        "| Zero weight, budget still chosen | Decision loss is unmixed with cost. Feasibility still depends on the cap. At zero, every feasible team is optimal when decision losses do not differ by team. | Zero is a reference the implementation allows. It does not answer how expensive confidence should be. |",
        "| Low, 0.2 / confidence mean | Confidence costs one uncertain decision. It can be worth that much, and not much more. | The 0.2 is the unapproved uncertainty weight, not a measured utility. |",
        "| Moderate, 1.0 / confidence mean | Confidence costs one false acceptance. It is rarely worth fielding unless it removes almost a whole error. | The 1.0 is the unapproved error weight. |",
        "| High, 0.2 / semantic mean | Confidence's penalty exceeds every loss on the proposed scale. The optimum ignores it even when the budget allows it. | This makes the resource term dominate. That may be what the lead wants, but it is not identified by the data. |",
        "| Permissive cap at the four-mean sum | Every team is feasible. The cost-minimizing team is still the cheapest team. | The sum is a scale fact. The freeze says it does not authorize budget selection. |",
        "| Restrictive cap at the cheapest pair | Floor 2 can field only rule and semantic. Floor 3 has no policy. | An infeasible hard question would confound aggregation with roster availability. |",
        "",
        "What the grid does support is a choice rule, not a number. Pick the coefficient whose confidence "
        "gap is the smallest decision-loss improvement that should justify paying for confidence. "
        "Pick one shared budget at or above the participant floor the lead actually adopts, and do not "
        "give the three methods different caps. If the hard floor of 3 is in force, the restrictive cap "
        "in this grid is not a usable matched budget.",
        "",
        "## Reproducibility",
        "",
        "```",
        "python evaluation/experiments/experiment3/resource_sensitivity.py",
        "```",
        "",
        "Outputs, all labeled SYNTHETIC / CONFIGURATION-SENSITIVITY ANALYSIS:",
        "",
        "- `evaluation/experiments/experiment3/sensitivity/scenarios.json`",
        "- `evaluation/experiments/experiment3/sensitivity/results.json`",
        "- `evaluation/experiments/experiment3/sensitivity/reproducibility_manifest.json`",
        "",
        "The manifest hashes those files, this document, the synthetic fixture, and the calibration file. "
        "Existing synthetic figures, `synthetic/results.json`, empirical outputs, and the approval package are not rewritten.",
        "",
    ])
    return "\n".join(lines)


def _git_revision() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def write_outputs(directory: Path | None = None, document: Path | None = None) -> dict:
    directory = Path(directory) if directory is not None else DEFAULT_DIR
    document = Path(document) if document is not None else DEFAULT_DOC
    assert_safe_output(directory)
    assert_safe_output(document)
    analysis = analyze()
    directory.mkdir(parents=True, exist_ok=True)
    files = {
        "scenarios.json": _dump(scenario_document(analysis)),
        "results.json": _dump(results_document(analysis)),
    }
    for name, text in files.items():
        (directory / name).write_text(text, encoding="utf-8", newline="\n")
    document.parent.mkdir(parents=True, exist_ok=True)
    document.write_text(render_document(analysis), encoding="utf-8", newline="\n")
    hashed = {
        "scenarios.json": directory / "scenarios.json",
        "results.json": directory / "results.json",
        "document": document,
        "analysis_module": Path(__file__),
        "synthetic_fixture": FIXTURE_PATH,
        "calibration_file": CALIBRATION_FILE,
        "resource_proposal": RESOURCE_PROPOSAL,
    }
    manifest = {
        "label": LABEL,
        "output_class": "SYNTHETIC",
        "analysis_class": "CONFIGURATION-SENSITIVITY ANALYSIS",
        "empirical_claim": False,
        "selected_configuration": None,
        "collection_executed": False,
        "approval_records_modified": False,
        "git_revision": _git_revision(),
        "files": {
            name: {"path": str(path.resolve().relative_to(ROOT)).replace("\\", "/"),
                   "sha256": _sha256(path), "bytes": path.stat().st_size}
            for name, path in hashed.items()
        },
        "preserved_not_modified": [str(path.relative_to(ROOT)).replace("\\", "/") for path in PRESERVED],
    }
    manifest_path = directory / "reproducibility_manifest.json"
    manifest_path.write_text(_dump(manifest), encoding="utf-8", newline="\n")
    manifest["files"]["reproducibility_manifest.json"] = {
        "path": str(manifest_path.resolve().relative_to(ROOT)).replace("\\", "/"),
        "sha256": _sha256(manifest_path),
        "bytes": manifest_path.stat().st_size,
        "note": "Hash of the manifest body that lists the other files. The manifest does not include its own hash.",
    }
    return manifest


def main() -> None:
    manifest = write_outputs()
    print(LABEL)
    print("selected_configuration: null")
    print("scenarios: " + manifest["files"]["scenarios.json"]["sha256"])
    print("results: " + manifest["files"]["results.json"]["sha256"])


if __name__ == "__main__":
    main()
