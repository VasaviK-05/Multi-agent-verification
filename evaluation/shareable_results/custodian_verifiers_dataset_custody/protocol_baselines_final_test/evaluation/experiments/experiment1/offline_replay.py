"""Experiment 1 offline replay on frozen Experiment 3 verifier reports.

This module does not call verifiers and does not write under the Experiment 3
empirical directory. Full minimax, uniform, and the deterministic fixed strategy
use the preexisting comparison rules. Greedy uses the coverage selector on the
heuristic question analysis. A selector team that is infeasible under the
Experiment 3 budget is left infeasible.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.analysis.heuristic import heuristic_analysis
from app.analysis.research_context import build_research_context
from app.game.research.comparison import deterministic_id
from app.models.schemas import VerificationResult
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.selection.verifier_selector import DEFAULT_VERIFIER_ORDER, VerifierSelector
from app.verifiers.base_verifier import BaseVerifier
from evaluation.analysis.experiment3 import binary_correctness
from evaluation.experiments.experiment3.empirical_executor import (
    _matrix,
    _policies,
    load_examples,
    score,
)
from evaluation.experiments.experiment3.execution_readiness import SEED


class _NamedVerifier(BaseVerifier):
    """Selector registration only. verify() is never called."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def verify(self, question: str, answer: str, context: str | None = None) -> VerificationResult:
        raise RuntimeError("Experiment 1 replay does not call verifiers")

EXPERIMENT_ID = "experiment1"
METHODS = ("full_minimax", "coverage_aware_greedy", "uniform", "deterministic_minimax")
GREEDY_AGGREGATION = "reputation_weighted"
DESTINATION = ROOT / "evaluation/experiments/experiment1/development"
PROTECTED = (
    ROOT / "evaluation/experiments/experiment3/empirical/results.json",
    ROOT / "evaluation/experiments/experiment3/empirical/metrics.json",
    ROOT / "evaluation/experiments/experiment3/empirical/bootstrap_results.json",
    ROOT / "evaluation/experiments/experiment3/empirical/verifier_reports.jsonl",
    ROOT / "evaluation/experiments/experiment3/empirical/figures/attack_validation_loss.svg",
)
PUBLISHED = {
    "results.json": "82324e96da71095bf1f2e75a2c080a396151590671111a91d7a870a6a657f8f8",
    "metrics.json": "2c186172e5f1e9e2c2f344292d0b5a093a11e8fbb746294bde6cb54faeb08c57",
    "bootstrap_results.json": "2b56ac693740bfdbee00dcf788c0bb4a097d7f70c3ad78b3335bd6b120dce53a",
    "verifier_reports.jsonl": "877d0218dd498e8ca525e651f52f8aa1e337cd6f5123583fb277a2a28e01eca5",
    "attack_validation_loss.svg": "8be472c94d29b34caec0829065afcc21eb059b746d0d31f8b2871fc7465b1dd4",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes() -> dict[str, str]:
    return {path.name: _sha(path) for path in PROTECTED}


def assert_frozen() -> None:
    hashes = protected_hashes()
    for path in PROTECTED:
        if hashes[path.name] != PUBLISHED[path.name]:
            raise RuntimeError(f"frozen Experiment 3 artifact changed: {path.name}")


def assert_destination(destination: Path) -> None:
    text = destination.resolve().as_posix().lower()
    if "experiment3/empirical" in text or "final_test" in text:
        raise RuntimeError("refusing to write Experiment 1 output into Experiment 3 or Final Test")


def _attack_label(row: dict) -> str:
    target = row.get("attack_target") or []
    if target:
        return row["attack_condition"] + " [" + ",".join(target) + "]"
    return row["attack_condition"]


def _selector() -> VerifierSelector:
    stubs = [_NamedVerifier(name) for name in DEFAULT_VERIFIER_ORDER]
    return VerifierSelector(verifiers=stubs, capabilities=BUILTIN_CAPABILITIES)


def greedy_plan(example: dict, selector: VerifierSelector) -> dict:
    """Coverage-greedy team from the heuristic analyzer. No verifier call."""
    analysis = heuristic_analysis(example["question"])
    analysis.research_context = build_research_context(analysis)
    plan = selector.plan(analysis, context=example.get("context"))
    return {
        "team": tuple(sorted(plan.initial_selected)),
        "difficulty": plan.difficulty,
        "minimum_count": plan.minimum_count,
        "target_count": plan.target_count,
        "requirements": list(plan.requirements.requirements),
    }


def pure_probabilities(strategy_ids: tuple[str, ...], chosen: str) -> dict[str, float]:
    if chosen not in strategy_ids:
        raise ValueError("chosen strategy is outside the feasible set")
    return {strategy_id: float(strategy_id == chosen) for strategy_id in strategy_ids}


def uniform_probabilities(strategy_ids: tuple[str, ...]) -> dict[str, float]:
    weight = 1.0 / len(strategy_ids)
    return {strategy_id: weight for strategy_id in strategy_ids}


def fixed_strategy_id(matrix) -> str:
    """Predeclared rule: minimum worst-column loss, then smaller strategy id."""
    return matrix.strategy_ids[deterministic_id(matrix, clean=False)]


def _index(cells: list[dict]) -> dict:
    return {(row["strategy_id"], row["candidate_id"], row["attack_id"]): row for row in cells}


def _weighted(cell_index, probabilities, candidate_id, attack_id) -> dict | None:
    losses = []
    penalties = []
    coverage = []
    failures = 0
    decisions = Counter()
    expected = Counter()
    verifiers = None
    base = None
    for strategy_id, weight in probabilities.items():
        if weight == 0:
            continue
        cell = cell_index[(strategy_id, candidate_id, attack_id)]
        base = cell
        if cell["execution_status"] != "complete" or cell["validation_loss"] is None:
            failures += 1
            continue
        losses.append(weight * cell["validation_loss"])
        penalties.append(weight * cell["resource_penalty"])
        coverage.append(weight * (1.0 if cell["decision"] in {"passed", "failed"} else 0.0))
        decisions[cell["decision"]] += weight
        label = binary_correctness(cell)
        if label:
            expected[label] += weight
        if weight == 1.0:
            verifiers = list(cell["verifiers"])
    if base is None or failures:
        return None
    positive = [strategy_id for strategy_id, weight in probabilities.items() if weight > 0]
    decision = next(iter(decisions)) if len(decisions) == 1 and len(positive) == 1 else "mixture"
    return {
        "candidate_id": candidate_id,
        "related_group_id": base["related_group_id"],
        "benchmark": base["benchmark"],
        "attack_id": attack_id,
        "attack_condition": _attack_label(base),
        "decision": decision,
        "gold_label": base["gold_label"],
        "validation_loss": sum(losses),
        "resource_penalty": sum(penalties),
        "coverage": sum(coverage),
        "execution_status": "complete",
        "selected_verifiers": verifiers,
        "human_verified": base["human_verified"],
        "expected_correctness": dict(expected),
    }


def method_rows(scored: dict, plans: dict[str, dict]) -> tuple[dict, list[dict]]:
    matrix = _matrix(scored["strategies"], scored["attacks"], scored["cells"])
    solved = _policies(matrix)
    strategy_ids = matrix.strategy_ids
    by_id = {strategy.strategy_id: strategy for strategy in matrix.strategy_definitions}
    fixed = fixed_strategy_id(matrix)
    greedy_feasible = 0
    greedy_infeasible = Counter()
    team_counts = Counter()
    probabilities = {
        "full_minimax": pure_probabilities(strategy_ids, solved["full_minimax"]["modal_strategy_id"]),
        "uniform": uniform_probabilities(strategy_ids),
        "deterministic_minimax": pure_probabilities(strategy_ids, fixed),
    }
    cell_index = _index(scored["cells"])
    rows = []
    attacks = [(attack.attack_id, attack) for attack in scored["attacks"]]
    candidates = []
    seen = set()
    for cell in scored["cells"]:
        if cell["candidate_id"] not in seen:
            seen.add(cell["candidate_id"])
            candidates.append(cell["candidate_id"])
    for candidate_id in candidates:
        plan = plans[candidate_id]
        team = tuple(plan["team"])
        team_counts[str(team)] += 1
        match = [strategy for strategy in matrix.strategy_definitions
                 if strategy.verifiers == team and strategy.aggregation == GREEDY_AGGREGATION]
        if len(match) != 1:
            greedy_infeasible[str(team)] += 1
            greedy_probability = None
        else:
            greedy_feasible += 1
            greedy_probability = pure_probabilities(strategy_ids, match[0].strategy_id)
        for attack_id, _attack in attacks:
            for method in ("full_minimax", "uniform", "deterministic_minimax"):
                item = _weighted(cell_index, probabilities[method], candidate_id, attack_id)
                if item is None:
                    continue
                item["aggregation_method"] = method
                rows.append(item)
            if greedy_probability is None:
                rows.append({
                    "candidate_id": candidate_id,
                    "related_group_id": plans[candidate_id]["related_group_id"],
                    "benchmark": plans[candidate_id]["benchmark"],
                    "attack_id": attack_id,
                    "attack_condition": _attack_label(cell_index[(fixed, candidate_id, attack_id)]),
                    "decision": "infeasible",
                    "gold_label": plans[candidate_id]["gold_label"],
                    "validation_loss": None,
                    "resource_penalty": None,
                    "coverage": None,
                    "execution_status": "infeasible",
                    "selected_verifiers": list(team),
                    "aggregation_method": "coverage_aware_greedy",
                    "human_verified": plans[candidate_id]["human_verified"],
                    "infeasible_reason": "selector team is outside the matched budget and participant floor",
                })
            else:
                item = _weighted(cell_index, greedy_probability, candidate_id, attack_id)
                item["aggregation_method"] = "coverage_aware_greedy"
                rows.append(item)
    policies = {
        "full_minimax": {
            "rule": "solve_minimax modal strategy on the joint matrix",
            "strategy_id": solved["full_minimax"]["modal_strategy_id"],
            "verifiers": list(by_id[solved["full_minimax"]["modal_strategy_id"]].verifiers),
            "aggregation": by_id[solved["full_minimax"]["modal_strategy_id"]].aggregation,
            "game_value": solved["full_minimax"]["game_value"],
        },
        "deterministic_minimax": {
            "rule": "minimum worst-column augmented loss, then smaller strategy id",
            "strategy_id": fixed,
            "verifiers": list(by_id[fixed].verifiers),
            "aggregation": by_id[fixed].aggregation,
            "same_verifiers_as_full_minimax": list(by_id[fixed].verifiers) == list(by_id[solved["full_minimax"]["modal_strategy_id"]].verifiers),
        },
        "uniform": {
            "rule": "equal probability on every feasible strategy",
            "strategy_count": len(strategy_ids),
            "weight": 1.0 / len(strategy_ids),
        },
        "coverage_aware_greedy": {
            "rule": "heuristic QuestionAnalysis plus VerifierSelector coverage greedy, aggregation reputation_weighted",
            "aggregation": GREEDY_AGGREGATION,
            "feasible_candidates": greedy_feasible,
            "infeasible_candidates": sum(greedy_infeasible.values()),
            "infeasible_teams": dict(greedy_infeasible),
            "selected_team_counts": dict(team_counts),
            "source": "predeclared selector code; teams were not chosen from observed losses",
        },
    }
    return policies, rows


def _rate(numerator: float, denominator: float):
    if denominator == 0:
        return None
    return numerator / denominator


def summarize_method(rows: list[dict], method: str) -> dict:
    chosen = [row for row in rows if row["aggregation_method"] == method]
    complete = [row for row in chosen if row["execution_status"] == "complete"]
    buckets = defaultdict(list)
    for row in complete:
        buckets[row["attack_condition"]].append(row)
    attacks = []
    for label, group in sorted(buckets.items()):
        attacks.append({"attack": label, **_block(group)})
    return {
        "method": method,
        "rows": len(chosen),
        "complete_rows": len(complete),
        "infeasible_rows": sum(row["execution_status"] == "infeasible" for row in chosen),
        "overall": _block(complete) if complete else None,
        "by_attack": attacks,
    }


def _block(rows: list[dict]) -> dict:
    expected = Counter()
    for row in rows:
        expected.update(row.get("expected_correctness") or {})
    false_accept = expected["false_acceptance"]
    false_reject = expected["false_rejection"]
    correct_accept = expected["correct_acceptance"]
    correct_reject = expected["correct_rejection"]
    classified = false_accept + false_reject + correct_accept + correct_reject
    mixture = any(row["decision"] == "mixture" for row in rows)
    return {
        "candidates": len(rows),
        "mean_decision_loss": sum(row["validation_loss"] for row in rows) / len(rows),
        "mean_resource_penalty": sum(row["resource_penalty"] for row in rows) / len(rows),
        "correct_acceptance": correct_accept,
        "correct_rejection": correct_reject,
        "false_acceptance": false_accept,
        "false_rejection": false_reject,
        "uncertain": len(rows) - classified,
        "coverage": _rate(classified, len(rows)),
        "selective_risk": _rate(false_accept + false_reject, classified),
        "false_acceptance_rate": _rate(false_accept, false_accept + correct_reject),
        "false_rejection_rate": _rate(false_reject, false_reject + correct_accept),
        "false_acceptance_denominator": false_accept + correct_reject,
        "false_rejection_denominator": false_reject + correct_accept,
        "decision": "mixture" if mixture else "pure",
        "execution_failures": 0,
    }


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def paired_bootstrap(rows: list[dict], method: str, *, resamples: int = 2000, seed: int = SEED) -> dict:
    full = defaultdict(list)
    other = defaultdict(list)
    for row in rows:
        if row["execution_status"] != "complete" or row["validation_loss"] is None:
            continue
        if row["aggregation_method"] not in {"full_minimax", method}:
            continue
        key = (row["related_group_id"], row["attack_condition"], row["benchmark"])
        target = full if row["aggregation_method"] == "full_minimax" else other
        target[key].append(row["validation_loss"])
    shared = set(full) & set(other)
    by_group = defaultdict(list)
    for key in shared:
        by_group[key[0]].append(sum(other[key]) / len(other[key]) - sum(full[key]) / len(full[key]))
    groups = sorted(by_group)
    values = [value for group in by_group.values() for value in group]
    rng = random.Random(seed)
    means = []
    for _ in range(resamples):
        draw = [rng.choice(groups) for _ in groups]
        sample = [value for name in draw for value in by_group[name]]
        means.append(sum(sample) / len(sample))
    return {
        "method": method,
        "reference": "full_minimax",
        "related_group_count": len(groups),
        "sample_size": len(values),
        "mean_loss_difference": sum(values) / len(values) if values else None,
        "zero_difference_count": sum(value == 0 for value in values),
        "resamples": resamples,
        "seed": seed,
        "confidence_level": 0.95,
        "confidence_interval": {"lower": _quantile(means, 0.025), "upper": _quantile(means, 0.975)},
        "evidence_label": "EMPIRICAL",
    }


def load_attached(root: Path) -> list[dict]:
    examples = load_examples(root)
    stored = {}
    path = root / "evaluation/experiments/experiment3/empirical/verifier_reports.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                stored[row["candidate_id"]] = row["reports"]
    for example in examples:
        example["reports"] = stored[example["candidate_id"]]
    return examples


def run(root: Path | None = None, destination: Path | None = None) -> dict:
    root = Path(root) if root is not None else ROOT
    destination = Path(destination) if destination is not None else DESTINATION
    assert_destination(destination)
    before = protected_hashes()
    assert_frozen()
    examples = load_attached(root)
    selector = _selector()
    plans = {}
    for example in examples:
        plan = greedy_plan(example, selector)
        plan.update({
            "related_group_id": example["related_group_id"],
            "benchmark": example["benchmark"],
            "gold_label": example["gold_label"],
            "human_verified": example["human_verified"],
            "candidate_id": example["candidate_id"],
        })
        plans[example["candidate_id"]] = plan
    scored = score(examples)
    policies, rows = method_rows(scored, plans)
    summaries = [summarize_method(rows, method) for method in METHODS]
    bootstrap = [paired_bootstrap(rows, method) for method in METHODS if method != "full_minimax"]
    payload = {
        "record_type": "experiment1_offline_replay_v1",
        "evidence_label": "EMPIRICAL",
        "experiment_id": EXPERIMENT_ID,
        "source": "frozen Experiment 3 verifier_reports.jsonl",
        "verifiers_called": False,
        "final_test_accessed": False,
        "candidates": len(examples),
        "groups": len({example["related_group_id"] for example in examples}),
        "methods": list(METHODS),
        "policies": policies,
        "summaries": summaries,
        "bootstrap": bootstrap,
        "rows": rows,
        "deviations": [
            "Suppression remains unavailable, matching Experiment 3.",
            "Greedy aggregation is reputation_weighted, the pilot proposal value. experiment1_proposal.json does not name it.",
            "Question types come from the keyword heuristic, not the optional Ollama analyzer.",
            "Selector resource weights are the selector's dimensionless profiles. Feasibility then uses the Experiment 3 frozen-millisecond budget.",
            "deterministic_minimax is the preexisting worst-column rule, not a team named after seeing Experiment 3.",
        ],
    }
    destination.mkdir(parents=True, exist_ok=True)
    _write_figure(destination / "figures" / "method_decision_loss.svg", summaries)
    _write(destination / "results.json", {key: value for key, value in payload.items() if key != "summaries"})
    _write(destination / "metrics.json", {"evidence_label": "EMPIRICAL", "summaries": summaries})
    _write(destination / "bootstrap_results.json", {"evidence_label": "EMPIRICAL", "seed": SEED, "resamples": 2000, "bootstrap": bootstrap})
    _write(destination / "policy_manifest.json", {"evidence_label": "EMPIRICAL", "policies": policies, "deviations": payload["deviations"]})
    after = protected_hashes()
    if before != after:
        raise RuntimeError("Experiment 1 replay changed a frozen Experiment 3 artifact")
    return payload


def _write_figure(path: Path, summaries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if "synthetic" in path.as_posix().lower() or "experiment3" in path.as_posix().lower():
        raise RuntimeError("refusing to write an Experiment 1 figure into Experiment 3 or a synthetic path")
    attacks = summaries[0]["by_attack"]
    labels = [item["attack"] for item in attacks]
    width, height = 980, 420
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<desc>EMPIRICAL Experiment 1 offline replay. Mean decision loss by method and attack.</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="20" y="28" font-family="sans-serif" font-size="16">EMPIRICAL mean decision loss</text>',
    ]
    colors = ("#1f4e79", "#c47b2b", "#2f6f4e", "#6b3f69")
    slot = 120
    for index, summary in enumerate(summaries):
        color = colors[index]
        for attack_index, attack in enumerate(summary["by_attack"]):
            loss = attack["mean_decision_loss"]
            bar = max(1, int(loss * 220))
            x = 180 + attack_index * slot + index * 22
            y = 340 - bar
            lines.append(f'<rect x="{x}" y="{y}" width="18" height="{bar}" fill="{color}"/>')
        lines.append(f'<rect x="20" y="{48 + index * 18}" width="12" height="12" fill="{color}"/>')
        lines.append(f'<text x="38" y="{59 + index * 18}" font-family="sans-serif" font-size="12">{summary["method"]}</text>')
    for attack_index, label in enumerate(labels):
        lines.append(f'<text x="{180 + attack_index * slot}" y="360" font-family="sans-serif" font-size="9" transform="rotate(25 {180 + attack_index * slot} 360)">{label}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    payload = run()
    print(json.dumps({
        "candidates": payload["candidates"],
        "methods": payload["methods"],
        "greedy_infeasible": payload["policies"]["coverage_aware_greedy"]["infeasible_candidates"],
        "final_test_accessed": False,
    }))


if __name__ == "__main__":
    main()
