"""Execute Experiment 3 on Development verifier inputs.

This module calls the repository verifiers. It does not invent reports, labels,
or reputation observations, and it does not open Final Test files.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.decision.decision_engine import DecisionEngine
from app.game.decision_inputs import FrozenReputationSnapshot
from app.decision.vote_normalization import is_abstention
from app.game.dependencies import Dependency, DependencyRegistry
from app.game.models import LossConfiguration, PayoffMatrix, canonical_json
from app.game.offline.attacks import AttackSpecification, enumerate_attacks, transform
from app.game.offline.records import Attempt
from app.game.research.comparison import restricted_matrix
from app.game.solver import solve_minimax
from app.game.strategies import enumerate_strategies
from app.models.schemas import VerificationResult
from evaluation.experiments.experiment3.development_roster import load_roster
from evaluation.experiments.experiment3.empirical_runner import (
    CONDITIONS,
    METHODS,
    analyze_recordings,
    assert_unique_recordings,
)
from evaluation.experiments.experiment3.execution_readiness import (
    BUDGET_MS,
    CALIBRATION_ID,
    COEFFICIENT,
    INPUTS_RELATIVE,
    SEED,
    execution_report,
)

VERIFIERS = ("semantic", "evidence", "rule", "confidence")
ADAPTERS = {"rule": "rule_v1", "evidence": "evidence_v1", "confidence": "confidence_v1", "semantic": "semantic_v1"}
SPECIFICATION = AttackSpecification(version="report_corruption_v1", suppression="unavailable")
LOSS = LossConfiguration(
    version="experiment3-selected-loss-v1",
    false_accept=1.0,
    false_reject=1.0,
    uncertain=0.2,
    resource_weight=COEFFICIENT,
    cost_units="ms",
)


def _dump(path: Path, payload: dict) -> None:
    def convert(value):
        if isinstance(value, tuple):
            return list(value)
        raise TypeError(f"cannot serialize {type(value).__name__}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=convert) + "\n", encoding="utf-8")


def _reference(raw) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
        return text or None
    if isinstance(raw, list):
        parts = []
        for item in raw:
            if isinstance(item, str) and item.strip():
                parts.append(item.strip())
            elif isinstance(item, dict):
                parts.append(json.dumps(item, sort_keys=True))
        text = "\n".join(parts).strip()
        return text or None
    return None


def load_examples(root: Path) -> list[dict]:
    roster = load_roster(root)
    allowed = {}
    for group in roster["paired_groups"]:
        for candidate in group["candidates"]:
            allowed[candidate["candidate_id"]] = {
                "related_group_id": group["related_group_id"],
                "benchmark": group["benchmark"],
                "question_id": group["question_id"],
                "gold_label": candidate["label_class"],
                "human_verified": candidate["human_verified"],
                "label_method": candidate["label_method"],
            }
    path = root / INPUTS_RELATIVE
    if "final_test" in path.as_posix().lower():
        raise RuntimeError("refusing to read a Final Test path")
    found = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("partition") != "development":
                raise RuntimeError("verifier inputs contain a non-development partition")
            candidate_id = row.get("candidate_id")
            if candidate_id not in allowed:
                continue
            if candidate_id in found:
                raise RuntimeError(f"duplicate development verifier input for {candidate_id}")
            question = row.get("question")
            answer = row.get("candidate_answer")
            if not isinstance(question, str) or not question.strip() or not isinstance(answer, str) or not answer.strip():
                raise RuntimeError(f"development input {candidate_id} has no question or answer")
            found[candidate_id] = {
                **allowed[candidate_id],
                "candidate_id": candidate_id,
                "question": question,
                "answer": answer,
                "context": _reference(row.get("evidence_context")),
            }
    missing = sorted(set(allowed) - set(found))
    if missing:
        raise RuntimeError(f"{len(missing)} eligible candidates have no development verifier input")
    return [found[candidate["candidate_id"]] for group in roster["paired_groups"] for candidate in group["candidates"]]


def structural_registry() -> DependencyRegistry:
    groups = (
        ("deterministic_rule", ("rule",)),
        ("embedding_minilm", ("semantic", "evidence")),
        ("nli_deberta", ("evidence", "confidence")),
        ("ollama_generator", ("confidence",)),
    )
    return DependencyRegistry(
        version="structural_shared_resource_v1",
        dependencies=tuple(Dependency(resource_id=name, compromise_pathway="structural_assumption", verifiers=members) for name, members in groups),
        unresolved=(),
    )


def experiment_context():
    """Budget and frozen costs. Capabilities are uniform so coverage does not drop teams.

    The planning context records a Beta(1, 1) prior. It does not contain historical
    reputation observations. Stub selectors only supply that planning record.
    """
    from app.game.models import PayoffProvenance
    from evaluation.experiments.experiment3.resource_sensitivity import frozen_calibration
    from tests.test_game_foundation import make_context
    means = frozen_calibration()["means_ms"]
    return make_context(
        names=VERIFIERS, minimum=2, budget=BUDGET_MS,
        attempt_costs=[(name, means[name]) for name in VERIFIERS],
        cost_units="ms", loss_configuration=LOSS, dependencies=structural_registry(),
        provenance=PayoffProvenance(
            attack_specification="report_corruption_v1", history_dataset="no-approved-history",
            development_dataset="research-v1-exploratory-v1", final_test_dataset="final-test-excluded",
            matrix_version="experiment3-development-v1", loss_configuration=LOSS.version,
            category="general", evidence_kind="empirical"))


def feasible_strategies():
    enumerated = enumerate_strategies(experiment_context())
    if enumerated.status != "feasible":
        raise RuntimeError("selected budget admits no strategy")
    return enumerated.strategies


def _attacks():
    """One column per structural failure group.

    ``structural_shared_resource_v1`` connects semantic, evidence, and confidence
    and leaves rule alone. The four protocol kinds still apply, but a kind other
    than clean is one column per group. Suppression is emitted by the enumerator
    and dropped because the selected protocol sets it to unavailable.
    """
    return tuple(attack for attack in enumerate_attacks(structural_registry(), SPECIFICATION) if attack.kind != "suppression")


def build_verifiers(root: Path):
    from app.verifiers.confidence_verifier import ConfidenceVerifier
    from app.verifiers.evidence_verifier import EvidenceVerifier
    from app.verifiers.rule_verifier import RuleVerifier
    from app.verifiers.semantic_verifier import SemanticVerifier
    corpus = root / "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json"
    return {
        "semantic": SemanticVerifier(),
        "evidence": EvidenceVerifier(corpus_path=str(corpus)),
        "rule": RuleVerifier(),
        "confidence": ConfidenceVerifier(),
    }


def _call(verifier, question: str, answer: str, context: str | None) -> dict:
    started = time.perf_counter()
    try:
        result = verifier.verify(question, answer, context)
        elapsed = time.perf_counter() - started
        if not isinstance(result, VerificationResult):
            return {"ok": False, "seconds": elapsed, "error": "verifier did not return VerificationResult"}
        return {"ok": True, "seconds": elapsed, "result": result.model_dump(mode="json")}
    except Exception as exc:
        return {"ok": False, "seconds": time.perf_counter() - started, "error": f"{type(exc).__name__}: {exc}"}


def collect_reports(root: Path, examples: list[dict], destination: Path, *, limit: int | None) -> list[dict]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    stored = {}
    if destination.is_file():
        with destination.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    stored[row["candidate_id"]] = row
    selected = examples if limit is None else examples[:limit]
    pending = [example for example in selected if example["candidate_id"] not in stored]
    if pending:
        verifiers = build_verifiers(root)
        with destination.open("a", encoding="utf-8") as handle:
            for index, example in enumerate(pending, start=1):
                reports = {}
                for name in VERIFIERS:
                    reports[name] = _call(verifiers[name], example["question"], example["answer"], example["context"])
                row = {
                    "candidate_id": example["candidate_id"],
                    "related_group_id": example["related_group_id"],
                    "benchmark": example["benchmark"],
                    "evidence_label": "EMPIRICAL",
                    "reports": reports,
                }
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.flush()
                stored[example["candidate_id"]] = row
                print(json.dumps({"collected": index, "candidate_id": example["candidate_id"], "benchmark": example["benchmark"]}), flush=True)
    ordered = []
    for example in selected:
        row = stored.get(example["candidate_id"])
        if row is None:
            raise RuntimeError(f"verifier report missing for {example['candidate_id']}")
        ordered.append({**example, "reports": row["reports"]})
    return ordered


def _attempt(name: str, payload: dict, execution_id: str) -> Attempt:
    result = VerificationResult.model_validate(payload)
    state = "abstention" if is_abstention(result) else "directional"
    return Attempt(
        verifier_name=name,
        state=state,
        report_json=canonical_json(result.model_dump(mode="json")),
        execution_id=execution_id,
        configuration_id="experiment3-development-v1",
        report_provenance="development-verifier-call",
        adapter=ADAPTERS[name],
    )


def _condition_reports(example: dict, attack: Attack) -> dict[str, VerificationResult | str]:
    """Returned reports keyed by verifier. A string value is that verifier's failure."""
    results: dict[str, VerificationResult | str] = {}
    for name in VERIFIERS:
        report = example["reports"].get(name) or {}
        if not report.get("ok"):
            results[name] = report.get("error") or f"{name} did not return a report"
            continue
        try:
            attempt = _attempt(name, report["result"], example["candidate_id"])
            transformed, _audit = transform(attempt, attack, SPECIFICATION)
        except Exception as exc:
            results[name] = f"{name} attack transform failed: {type(exc).__name__}: {exc}"
            continue
        if transformed.report is None:
            results[name] = f"{name} report was removed"
        else:
            results[name] = transformed.report
    return results


def _loss(status: str, correct: bool) -> float:
    if status == "passed":
        return 0.0 if correct else LOSS.false_accept
    if status == "failed":
        return 0.0 if not correct else LOSS.false_reject
    return LOSS.uncertain


def score(examples: list[dict]) -> dict:
    context = experiment_context()
    enumerated = enumerate_strategies(context)
    if enumerated.status != "feasible":
        raise RuntimeError("selected budget admits no strategy")
    strategies = enumerated.strategies
    attacks = _attacks()
    registry = context.dependencies
    snapshot = FrozenReputationSnapshot.from_planning_context(context)
    engine = DecisionEngine(threshold=0.55)
    cells = []
    for example in examples:
        correct = example["gold_label"] == "VERIFIED_CORRECT"
        for attack in attacks:
            reports = _condition_reports(example, attack)
            for strategy in strategies:
                missing = [name for name in strategy.verifiers if not isinstance(reports.get(name), VerificationResult)]
                subset = [reports[name] for name in strategy.verifiers if isinstance(reports.get(name), VerificationResult)]
                if missing:
                    status, decision_loss, failure = "uncertain", None, "; ".join(str(reports.get(name)) for name in missing)
                    complete = False
                else:
                    try:
                        options = {"aggregation": strategy.aggregation, "team": strategy.verifiers, "snapshot": snapshot, "validation_id": example["candidate_id"]}
                        if strategy.aggregation == "dependency_group":
                            options["dependencies"] = registry
                        status, _score = engine.decide(subset, **options)
                        decision_loss = _loss(status, correct)
                        failure = None
                        complete = True
                    except Exception as exc:
                        status, decision_loss, failure, complete = "uncertain", None, f"{type(exc).__name__}: {exc}", False
                cells.append({
                    "candidate_id": example["candidate_id"],
                    "related_group_id": example["related_group_id"],
                    "benchmark": example["benchmark"],
                    "question_id": example["question_id"],
                    "gold_label": example["gold_label"],
                    "attack_id": attack.attack_id,
                    "attack_condition": attack.kind,
                    "attack_target": list(attack.members),
                    "strategy_id": strategy.strategy_id,
                    "verifiers": list(strategy.verifiers),
                    "aggregation": strategy.aggregation,
                    "estimated_cost_ms": strategy.estimated_cost,
                    "decision": status if complete else "uncertain",
                    "validation_loss": decision_loss,
                    "resource_penalty": COEFFICIENT * strategy.estimated_cost,
                    "execution_status": "complete" if complete else "failed",
                    "failure_reason": failure,
                    "human_verified": example["human_verified"],
                })
    return {"strategies": strategies, "attacks": attacks, "cells": cells, "registry_groups": [list(group.verifiers) for group in registry.groups(VERIFIERS)]}


def _matrix(strategies, attacks, cells):
    lookup = {(row["strategy_id"], row["attack_id"], row["candidate_id"]): row for row in cells}
    candidates = sorted({row["candidate_id"] for row in cells})
    usable = []
    values = []
    for strategy in strategies:
        row = []
        for attack in attacks:
            losses = []
            for candidate in candidates:
                item = lookup[(strategy.strategy_id, attack.attack_id, candidate)]
                if item["execution_status"] != "complete":
                    continue
                losses.append(item["validation_loss"] + item["resource_penalty"])
            if not losses:
                row = None
                break
            row.append(sum(losses) / len(losses))
        if row is not None:
            usable.append(strategy)
            values.append(tuple(row))
    if not usable:
        raise RuntimeError("no strategy has a complete cell in every condition")
    matrix = PayoffMatrix(
        strategy_ids=tuple(strategy.strategy_id for strategy in usable),
        strategy_definitions=tuple(usable),
        attack_ids=tuple(attack.attack_id for attack in attacks),
        values=tuple(values),
        compatibility_id="experiment3-development-v1",
    )
    return matrix


def _policies(matrix: PayoffMatrix) -> dict:
    solved = {
        "full_minimax": solve_minimax(matrix),
        "fixed_reputation_weighted": solve_minimax(restricted_matrix(matrix, "reputation_weighted")),
        "fixed_dependency_group": solve_minimax(restricted_matrix(matrix, "dependency_group")),
    }
    policies = {}
    for method, result in solved.items():
        if result.status != "optimal":
            raise RuntimeError(f"{method} solver status {result.status}: {result.message}")
        best = max(result.probabilities, key=lambda item: (item[1], item[0]))
        policies[method] = {"probabilities": result.probabilities, "modal_strategy_id": best[0], "game_value": result.game_value}
    return policies


def result_rows(scored: dict, policies: dict) -> list[dict]:
    from evaluation.experiments.experiment3.resource_sensitivity import frozen_calibration
    means = frozen_calibration()["means_ms"]
    by_strategy = {}
    for row in scored["cells"]:
        by_strategy.setdefault((row["candidate_id"], row["attack_id"], row["strategy_id"]), row)
    rows = []
    for (candidate_id, attack_id, strategy_id), cell in by_strategy.items():
        for method, policy in policies.items():
            probabilities = dict(policy["probabilities"])
            if strategy_id != policy["modal_strategy_id"]:
                continue
            weight = probabilities.get(strategy_id, 0.0)
            rows.append({
                "experiment_id": "experiment3",
                "related_group_id": cell["related_group_id"],
                "candidate_id": candidate_id,
                "benchmark": cell["benchmark"],
                "question_id": cell["question_id"],
                "attack_id": attack_id,
                "attack_condition": cell["attack_condition"],
                "attack_target": cell["attack_target"],
                "dependency_model": "structural_shared_resource_v1",
                "dependency_scenario": "structural_assumed",
                "aggregation_method": method,
                "decision": cell["decision"],
                "gold_label": cell["gold_label"],
                "validation_loss": cell["validation_loss"],
                "coverage": 1.0 if cell["decision"] in {"passed", "failed"} else 0.0,
                "uncertainty": 1.0 if cell["decision"] not in {"passed", "failed"} else 0.0,
                "verifier_reports": cell["verifiers"],
                "verifier_costs": [{"verifier": name, "cost": means[name], "cost_ms": means[name], "source": "frozen_calibration_mean"} for name in cell["verifiers"]],
                "estimated_cost_ms": cell["estimated_cost_ms"],
                "resource_penalty": cell["resource_penalty"],
                "execution_status": cell["execution_status"],
                "failure_reason": cell["failure_reason"],
                "provenance": {
                    "configuration_id": "experiment3-selected-v1",
                    "calibration_id": CALIBRATION_ID,
                    "modal_strategy_id": strategy_id,
                    "modal_probability": weight,
                    "policy_is_pure": weight >= 1.0 - 1e-8,
                    "human_verified_label": cell["human_verified"],
                    "synthetic_incorrect_is_human_verified": False,
                },
                "configuration_id": "experiment3-selected-v1",
                "evidence_label": "EMPIRICAL",
                "result_class": "EMPIRICAL",
                "selected_verifiers": cell["verifiers"],
                "label_provenance": "development_eligibility_manifest",
            })
    assert_unique_recordings(rows)
    return rows


def preserve_prior(destination: Path) -> None:
    prior = destination / "prior_not_collected"
    if prior.exists():
        return
    names = ("run_manifest.json", "results.json", "metrics.json", "bootstrap_results.json")
    if not any((destination / name).is_file() for name in names):
        return
    prior.mkdir(parents=True)
    for name in names:
        source = destination / name
        if source.is_file():
            (prior / name).write_bytes(source.read_bytes())


def execute(root: Path | None = None, *, limit: int | None = None, destination: Path | None = None) -> dict:
    root = Path(root) if root is not None else ROOT
    report = execution_report(root)
    if not report["authorized_by_research_lead"]:
        raise RuntimeError("execution configuration failed automated validation: " + "; ".join(report["blockers"]))
    if not report["verifiers_available"]:
        raise RuntimeError("verifiers are not available: " + "; ".join(report["verifier_gaps"]))
    if "final_test" in str(destination or "").lower():
        raise RuntimeError("refusing to write Experiment 3 output under a Final Test path")
    examples = load_examples(root)
    output = destination or (root / "evaluation/experiments/experiment3/empirical")
    if limit is None:
        preserve_prior(output)
        reports_path = output / "verifier_reports.jsonl"
        smoke = output / "smoke_reports.jsonl"
        if smoke.is_file() and not reports_path.is_file():
            reports_path.write_bytes(smoke.read_bytes())
    else:
        reports_path = output / "smoke_reports.jsonl"
    collected = collect_reports(root, examples, reports_path, limit=limit)
    scored = score(collected)
    matrix = _matrix(scored["strategies"], scored["attacks"], scored["cells"])
    policies = _policies(matrix)
    rows = result_rows(scored, policies)
    complete = sum(row["execution_status"] == "complete" for row in rows)
    attacks = len({row["attack_id"] for row in rows}) or len(CONDITIONS)
    expected = len(collected) * attacks * len(METHODS)
    structural_expected = 744 * 7 * len(METHODS)
    status = "SMOKE" if limit else ("COMPLETE" if complete == expected == structural_expected else "PARTIAL")
    analysis = analyze_recordings(rows, evidence_label="EMPIRICAL", resamples=2000, confidence_level=0.95, seed=SEED) if complete else None
    payload = {
        "record_type": "experiment3_empirical_results_v1",
        "evidence_label": "EMPIRICAL",
        "status": status,
        "rows": rows,
        "completed_cells": complete,
        "expected_cells": expected,
        "protocol_kind_count": len(CONDITIONS),
        "structural_attack_columns": attacks,
        "cell_count_note": "744 x 4 conditions x 3 methods = 8928 assumes one attack column per kind. structural_shared_resource_v1 has two failure groups, so each non-clean kind is two columns and suppression is excluded: 744 x 7 x 3 = 15624.",
        "candidates_collected": len(collected),
        "dependency_components": scored["registry_groups"],
        "policies": {method: {"modal_strategy_id": item["modal_strategy_id"], "game_value": item["game_value"], "probabilities": item["probabilities"]} for method, item in policies.items()},
        "final_test_accessed": False,
        "selected_configuration_is_empirically_optimized": False,
        "independent_human_approval": False,
    }
    if limit is None:
        _dump(output / "results.json", payload)
        _dump(output / "metrics.json", {"record_type": "experiment3_empirical_metrics_v1", "status": status, "evidence_label": "EMPIRICAL", "analysis": analysis})
        _dump(output / "bootstrap_results.json", {"record_type": "experiment3_empirical_bootstrap_v1", "status": status, "evidence_label": "EMPIRICAL", "resamples": 2000, "confidence_level": 0.95, "seed": SEED, "paired_differences": None if analysis is None else analysis["paired_differences"]})
    else:
        _dump(output / "smoke_results.json", payload)
    return payload


def main() -> int:
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    payload = execute(limit=limit)
    print(json.dumps({"status": payload["status"], "completed_cells": payload["completed_cells"], "candidates": payload["candidates_collected"], "final_test_accessed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
