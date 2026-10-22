"""Empirical development matrices and separately evaluated frozen policies."""

import math

from app.game.dependencies import FrozenModel
from app.game.models import PlanningContext, PayoffMatrix, content_id
from app.game.policy import build_policy, validate_policy
from app.game.strategies import enumerate_strategies
from app.game.offline.attacks import AttackSpecification, enumerate_attacks
from app.game.offline.records import DatasetManifest, history_reputation
from app.game.offline.replay import ReplayContract, ReplayOutcome, replay


class Metrics(FrozenModel):
    examples: int
    correct_accept: float
    correct_reject: float
    false_accept: float
    false_reject: float
    uncertain: float
    unresolved: float
    decision_coverage: float
    selective_risk: float | None
    estimated_resource_cost: float
    mean_loss: float


class Evaluation(FrozenModel):
    role: str
    manifest_id: str
    compatibility_id: str
    contract: ReplayContract
    attacks: AttackSpecification
    matrix: PayoffMatrix
    outcomes: tuple[ReplayOutcome, ...]
    metrics: tuple[tuple[str, str, Metrics], ...]


def evaluation_binding(manifest, contract, specification):
    return content_id({"version": "offline_evaluation_binding_v1", "manifest": manifest.manifest_id,
                       "contract": contract.model_dump(mode="json"),
                       "attacks": specification.model_dump(mode="json")})


def bind_evaluation(context, manifest, contract, specification):
    """Check history-derived statistics, then bind all replay-affecting settings."""
    context = PlanningContext.model_validate(context)
    manifest = DatasetManifest.model_validate(manifest)
    contract = ReplayContract.model_validate(contract)
    specification = AttackSpecification.model_validate(specification)
    provenance = context.provenance
    for role, dataset in (("history", provenance.history_dataset), ("development", provenance.development_dataset),
                          ("final_test", provenance.final_test_dataset)):
        if manifest.partition(role).dataset_id != dataset:
            raise ValueError("partition provenance differs from planning context")
    if (provenance.evidence_kind != manifest.evidence_kind
        or provenance.attack_specification != specification.specification_id):
        raise ValueError("attack/evidence provenance differs from planning context")
    statistics = context.plan.reputation_statistics
    if not statistics:
        raise ValueError("complete reputation snapshot required")
    manager = history_reputation(manifest, prior_alpha=contract.history_prior_alpha, prior_beta=contract.history_prior_beta)
    actual = manager.statistics_batch(tuple((s.verifier_name, context.plan.domain) for s in statistics))
    if {s.verifier_name: s for s in actual} != {s.verifier_name: s for s in statistics}:
        raise ValueError("snapshot is not established by the declared independent history")
    binding = evaluation_binding(manifest, contract, specification)
    if context.offline_evaluation_id not in {None, binding}:
        raise ValueError("offline settings changed; rebuild a compatible context and policy")
    data = context.model_dump()
    data["offline_evaluation_id"] = binding
    return PlanningContext(**data)


def _inputs(context, manifest, contract, specification):
    context = PlanningContext.model_validate(context)
    manifest = DatasetManifest.model_validate(manifest)
    contract = ReplayContract.model_validate(contract)
    specification = AttackSpecification.model_validate(specification)
    bound = bind_evaluation(context, manifest, contract, specification)
    if context.compatibility_id != bound.compatibility_id:
        raise ValueError("explicitly bind evaluation settings before fitting/evaluating")
    return context, manifest, contract, specification


def outcome_loss(outcome, loss):
    if outcome.public_status == "passed":
        return 0. if outcome.answer_is_correct else loss.false_accept
    if outcome.public_status == "failed":
        return 0. if not outcome.answer_is_correct else loss.false_reject
    return loss.uncertain


def summarize(weighted_outcomes, loss):
    """Weights are strategy probabilities per example, never best-strategy selection."""
    if not weighted_outcomes:
        raise ValueError("empty evaluation")
    counts = dict(correct_accept=0., correct_reject=0., false_accept=0., false_reject=0., uncertain=0., unresolved=0.)
    examples = {o.example_id for o, _ in weighted_outcomes}
    by_example = {name: [] for name in examples}
    for outcome, weight in weighted_outcomes:
        if not math.isfinite(weight) or weight < 0:
            raise ValueError("invalid policy weight")
        by_example[outcome.example_id].append(weight)
        if outcome.public_status not in {"passed", "failed"}:
            key = "uncertain"
        else:
            correct = (outcome.public_status == "passed") == outcome.answer_is_correct
            key = ("correct_" if correct else "false_") + ("accept" if outcome.public_status == "passed" else "reject")
        counts[key] += weight
        if outcome.unresolved:
            counts["unresolved"] += weight
    if any(not math.isclose(math.fsum(weights), 1., rel_tol=0., abs_tol=1e-12) for weights in by_example.values()):
        raise ValueError("policy weights must sum to one for each declared example")
    n = len(examples)
    decisive = math.fsum(counts[k] for k in ("correct_accept", "correct_reject", "false_accept", "false_reject"))
    cost = math.fsum(o.estimated_attempt_cost * w for o, w in weighted_outcomes) / n
    mean = math.fsum(outcome_loss(o, loss) * w for o, w in weighted_outcomes) / n
    total = mean + loss.resource_weight * cost
    if not math.isfinite(total):
        raise ValueError("nonfinite payoff")
    return Metrics(examples=n, **counts, decision_coverage=decisive / n,
        selective_risk=(counts["false_accept"] + counts["false_reject"]) / decisive if decisive else None,
        estimated_resource_cost=cost, mean_loss=total)


def construct_payoffs(context, manifest, contract, specification):
    """Fit only on development, including every declared example in each cell."""
    context, manifest, contract, specification = _inputs(context, manifest, contract, specification)
    strategies = enumerate_strategies(context).strategies
    if not strategies:
        raise ValueError("no_feasible_strategy")
    actions = enumerate_attacks(context.dependencies, specification)
    outcomes, metrics, values = [], [], []
    for strategy in strategies:
        row = []
        for attack in actions:
            cell = tuple(replay(context, strategy, attack, specification, contract, example)
                         for example in manifest.partition("development").examples)
            summary = summarize(tuple((o, 1.) for o in cell), context.loss_configuration)
            outcomes.extend(cell)
            metrics.append((strategy.strategy_id, attack.attack_id, summary))
            row.append(summary.mean_loss)
        values.append(tuple(row))
    matrix = PayoffMatrix(strategy_ids=tuple(s.strategy_id for s in strategies), strategy_definitions=strategies,
        attack_ids=tuple(a.attack_id for a in actions), values=tuple(values), compatibility_id=context.compatibility_id)
    return Evaluation(role="development", manifest_id=manifest.manifest_id, compatibility_id=context.compatibility_id,
        contract=contract, attacks=specification, matrix=matrix, outcomes=tuple(outcomes), metrics=tuple(metrics))


def fit_policy(context, manifest, contract, specification):
    evaluation = construct_payoffs(context, manifest, contract, specification)
    return build_policy(context, evaluation.matrix), evaluation


class PolicyEvaluation(FrozenModel):
    role: str
    policy_id: str
    manifest_id: str
    outcomes: tuple[ReplayOutcome, ...]
    probabilities: tuple[tuple[str, float], ...]
    attack_metrics: tuple[tuple[str, Metrics], ...]


def evaluate_final_test(policy, context, manifest, contract, specification):
    """No fitting or optimization: integrate each attack's outcomes over frozen x."""
    context, manifest, contract, specification = _inputs(context, manifest, contract, specification)
    policy = validate_policy(policy, context)
    actions = enumerate_attacks(context.dependencies, specification)
    if policy.matrix.attack_ids != tuple(a.attack_id for a in actions):
        raise ValueError("policy attack columns differ from the frozen specification")
    probabilities = dict(policy.solution.probabilities)
    outcomes, metrics = [], []
    for attack in actions:
        weighted = []
        for strategy in policy.strategies:
            for example in manifest.partition("final_test").examples:
                outcome = replay(context, strategy, attack, specification, contract, example)
                outcomes.append(outcome)
                weighted.append((outcome, probabilities[strategy.strategy_id]))
        metrics.append((attack.attack_id, summarize(tuple(weighted), context.loss_configuration)))
    return PolicyEvaluation(role="final_test", policy_id=policy.policy_id, manifest_id=manifest.manifest_id,
        outcomes=tuple(outcomes), probabilities=policy.solution.probabilities, attack_metrics=tuple(metrics))
