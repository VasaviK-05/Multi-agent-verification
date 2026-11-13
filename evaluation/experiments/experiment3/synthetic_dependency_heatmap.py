"""Synthetic dependency-robustness heatmap.

Scores three declared failure-group assumptions with the existing offline game.
The reports are a hand-built fixture. This is not a Development recording and
not a measured dependency.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.analysis.models import QuestionAnalysis, QuestionResearchContext
from app.game.dependencies import Dependency, DependencyRegistry
from app.game.models import LossConfiguration, PayoffProvenance, capture_context
from app.game.offline.attacks import AttackSpecification
from app.game.offline.attacks import enumerate_attacks
from app.game.offline.evaluation import bind_evaluation, fit_policy
from app.game.offline.records import Attempt, DatasetManifest, Example, Partition
from app.game.offline.replay import ReplayContract
from app.game.research.comparison import restricted_matrix
from app.game.solver import solve_minimax, validate_solution
from app.models.schemas import VerificationResult
from app.selection.capabilities import CapabilityDescriptor
from app.selection.verifier_selector import VerifierSelector
from app.verifiers.base_verifier import BaseVerifier
from evaluation.analysis.visualization.experiment3 import assumption_heatmap

VERIFIERS = ("semantic", "evidence", "rule", "confidence")
ADAPTERS = {"semantic": "semantic_v1", "evidence": "evidence_v1", "rule": "rule_v1", "confidence": "confidence_v1"}
METHODS = ("full_minimax", "fixed_reputation_weighted", "fixed_dependency_group")
ATTACKS = ("clean", "forced_support", "forced_rejection", "confidence_inflation")
PATHWAY = "controlled_synthetic_assumption"
DESTINATION = ROOT / "evaluation/experiments/experiment3/synthetic/figures"


class _FixtureVerifier(BaseVerifier):
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def verify(self, question: str, answer: str, context: str | None = None) -> VerificationResult:
        raise RuntimeError("synthetic dependency scoring replays recordings and does not call verifiers")


def registry_for(kind: str) -> DependencyRegistry:
    if kind == "independent":
        dependencies = tuple(Dependency(resource_id=name, compromise_pathway=PATHWAY, verifiers=(name,)) for name in VERIFIERS)
        return DependencyRegistry(version="synthetic-independent-v1", dependencies=dependencies)
    if kind == "correlated_semantic_evidence":
        dependencies = (
            Dependency(resource_id="semantic-evidence", compromise_pathway=PATHWAY, verifiers=("semantic", "evidence")),
            Dependency(resource_id="rule", compromise_pathway=PATHWAY, verifiers=("rule",)),
            Dependency(resource_id="confidence", compromise_pathway=PATHWAY, verifiers=("confidence",)),
        )
        return DependencyRegistry(version="synthetic-correlated-text-v1", dependencies=dependencies)
    if kind == "fully_correlated":
        return DependencyRegistry(version="synthetic-fully-correlated-v1", unresolved=VERIFIERS)
    raise ValueError(f"unknown synthetic dependency assumption: {kind}")


def _analysis():
    return QuestionAnalysis("general", "hard", 0.8, domain_status="known", verification_types=["arithmetic"],
        research_context=QuestionResearchContext("question_context_v1", ["arithmetic"], {"arithmetic": 1.0}, True,
            None, "known", "heuristic", "rubric_v1"))


def _attempt(name: str, role: str) -> Attempt:
    # History is abstention. A mixed directional history was rejected by bind_evaluation
    # because it did not establish the reputation snapshot. Development reports stay directional and correct.
    if role == "history":
        row = VerificationResult(verifier_name=name, passed=False, score=0.0, metadata={"decision": "UNSURE"})
        state = "abstention"
    else:
        row = VerificationResult(verifier_name=name, passed=True, score=1.0,
            metadata={"decision": "SUPPORT", "rule_kind": "factual", "rule": "arithmetic_addition"})
        state = "directional"
    return Attempt(verifier_name=name, state=state, report_json=row.model_dump_json(), execution_id=role,
        configuration_id="synthetic-dependency-heatmap-v1", report_provenance="synthetic_recording", adapter=ADAPTERS[name])


def _expected_loss(matrix, probabilities, attack_index: int) -> float:
    weight = dict(probabilities)
    return sum(weight[strategy_id] * row[attack_index] for strategy_id, row in zip(matrix.strategy_ids, matrix.values))


def _policies(policy, development):
    solved = {"full_minimax": (development.matrix, policy.solution.probabilities)}
    for method, aggregation in (("fixed_reputation_weighted", "reputation_weighted"), ("fixed_dependency_group", "dependency_group")):
        current = restricted_matrix(development.matrix, aggregation)
        certificate = solve_minimax(current, tolerance=1e-8)
        validate_solution(current, certificate)
        solved[method] = (current, certificate.probabilities)
    return solved


def _study(kind: str):
    registry = registry_for(kind)
    attacks = AttackSpecification(version="report_corruption_v1", suppression="unavailable")
    selector = VerifierSelector(verifiers=[_FixtureVerifier(name) for name in VERIFIERS],
        difficulty_range={"easy": (1, 1), "hard": (1, 1)},
        capabilities={name: CapabilityDescriptor(("arithmetic",)) for name in VERIFIERS})
    loss = LossConfiguration(version="explicit-test-loss-v1", false_accept=1.0, false_reject=1.0, uncertain=0.2,
        resource_weight=0.1, cost_units="estimated_attempt_units")
    context = capture_context(selector, _analysis(), attempt_costs=[(name, 1.0) for name in VERIFIERS], budget=10,
        cost_units="estimated_attempt_units", dependencies=registry, loss_configuration=loss,
        aggregation_versions=[("reputation_weighted", "log_odds_v1"), ("dependency_group", "groups_v1")],
        provenance=PayoffProvenance(attack_specification=attacks.specification_id, history_dataset="history-v1",
            development_dataset="development-v1", final_test_dataset="synthetic-placeholder-v1", matrix_version="matrix-v1",
            loss_configuration="explicit-test-loss-v1", category="general", evidence_kind="synthetic_test_fixture"))
    contract = ReplayContract(version="offline_public_decision_v1", coverage_version="factual_output_contract_v1",
        contributor_version="baseline_log_odds_active_group_v1", threshold=0.55, failure_contract="all_selected_returned",
        execution_configuration_id="synthetic-dependency-heatmap-v1", history_prior_alpha=1.0, history_prior_beta=1.0)
    parts = []
    for role, dataset in (("history", "history-v1"), ("development", "development-v1"), ("final_test", "synthetic-placeholder-v1")):
        example = Example(example_id=role, split_identity=role, question_id=role, question=role + " synthetic question",
            answer="synthetic answer", reference=None, domain="general", planning_category=context.compatibility_id,
            answer_is_correct=True, label_source="synthetic-fixture-label", label_method="independent_ground_truth",
            validation_id=role, execution_configuration_id=contract.execution_configuration_id,
            cache_contract="complete_team_independent_v1",
            attempts=tuple(_attempt(name, role) for name in VERIFIERS))
        parts.append(Partition(role=role, dataset_id=dataset, examples=(example,)))
    manifest = DatasetManifest(version="synthetic-dependency-heatmap-v1", evidence_kind="synthetic_test_fixture", partitions=tuple(parts))
    context = bind_evaluation(context, manifest, contract, attacks)
    return context, manifest, contract, attacks, registry


def evaluate() -> dict:
    cells = []
    scenarios = []
    for kind, statement in (
        ("independent", "Semantic, evidence, rule, and confidence are separate failure groups."),
        ("correlated_semantic_evidence", "Semantic and evidence share one failure group. Rule and confidence are separate."),
        ("fully_correlated", "All four verifiers share one failure group."),
    ):
        context, manifest, contract, attacks, registry = _study(kind)
        groups = registry.groups(VERIFIERS)
        scenarios.append({"assumption": kind, "statement": statement, "measured_dependence": False,
            "groups": [list(group.verifiers) for group in groups]})
        policy, development = fit_policy(context, manifest, contract, attacks)
        enumerated = enumerate_attacks(registry, attacks)
        if tuple(attack.attack_id for attack in enumerated) != development.matrix.attack_ids:
            raise RuntimeError("attack columns differ from the fitted payoff matrix")
        for method, (matrix, probabilities) in _policies(policy, development).items():
            per_attack = []
            by_kind: dict[str, list[float]] = {name: [] for name in ATTACKS}
            if matrix.attack_ids != development.matrix.attack_ids:
                raise RuntimeError("restricted matrix changed the attack columns")
            for index, attack in enumerate(enumerated):
                loss = _expected_loss(matrix, probabilities, index)
                record = {"attack": attack.kind, "members": list(attack.members), "validation_loss": loss}
                per_attack.append(record)
                if attack.kind in by_kind:
                    by_kind[attack.kind].append(loss)
            for attack_kind, losses in by_kind.items():
                if not losses:
                    raise RuntimeError(f"{kind} {method} produced no {attack_kind} column")
                cells.append({"dependency_assumption": kind, "aggregation_method": method, "attack_condition": attack_kind,
                    "validation_loss": max(losses), "group_losses": losses,
                    "attacks": [row for row in per_attack if row["attack"] == attack_kind],
                    "reduction": "worst group loss for this attack kind", "evidence_label": "SYNTHETIC"})
    return {"evidence_label": "SYNTHETIC", "empirical_claim": False, "measured_dependence": False,
        "sample": "one hand-built development example per assumption, not the 372 Development groups",
        "loss_definition": "Engine Metrics.mean_loss: decision loss plus resource_weight times estimated attempt cost.",
        "loss_configuration": {"false_accept": 1.0, "false_reject": 1.0, "uncertain": 0.2, "resource_weight": 0.1,
            "cost_units": "estimated_attempt_units"},
        "attacks": list(ATTACKS), "methods": list(METHODS), "scenarios": scenarios, "cells": cells,
        "scoring_path": "fit_policy, restricted_matrix, and solve_minimax. The research readiness gate is not used because an evidence adapter requires a resource-bound validation this fixture does not have. No resource observation was invented. The schema-required final_test partition is synthetic and is not scored.",
        "existing_synthetic_results_modified": False}


def write_outputs(destination: Path, payload: dict | None = None) -> dict:
    text = destination.as_posix().lower()
    if "empirical" in text or text.endswith("/results") or "/results/" in text:
        raise ValueError("synthetic figure cannot be written to an empirical result directory")
    payload = payload or evaluate()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "dependency_robustness_metrics.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    paths = {"json": destination / "dependency_robustness_metrics.json"}
    for method in METHODS:
        stem = f"dependency_robustness_{method}"
        svg = assumption_heatmap(payload, destination / f"{stem}.svg", method=method)
        png = assumption_heatmap(payload, destination / f"{stem}.png", method=method)
        paths[method] = {"svg": svg, "png": png}
    return paths


def main() -> int:
    paths = write_outputs(DESTINATION)
    print(json.dumps({"evidence_label": "SYNTHETIC", "json": str(paths["json"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
