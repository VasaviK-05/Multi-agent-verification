"""Fit shared strategy distributions from explicit source-domain development games.

Every source replays its own domain and history snapshot. Exported policies retain
exact target-domain snapshots and applicability; no domain is relabelled.
"""

import math

from app.game.dependencies import FrozenModel
from app.game.models import PlanningContext, PayoffMatrix, canonical_json
from app.game.offline.attacks import AttackSpecification
from app.game.offline.evaluation import _inputs, construct_payoffs, evaluate_final_test
from app.game.offline.records import DatasetManifest
from app.game.offline.replay import ReplayContract
from app.game.pooling_contract import PoolSource, PoolingContract, pooled_payoff_digest
from app.game.policy import Policy, build_policy, validate_policy
from app.game.strategies import enumerate_strategies


class PoolMember(FrozenModel):
    context: PlanningContext
    manifest: DatasetManifest
    contract: ReplayContract
    attacks: AttackSpecification


def _validate_members(members):
    members = tuple(PoolMember.model_validate(m) for m in members)
    if not members or len({m.context.plan.domain for m in members}) != len(members):
        raise ValueError("pool members require unique nonempty domains")
    seen = {}
    groups = {}
    datasets = {}
    for member in members:
        if member.context.pooling_contract_json is not None:
            raise ValueError("nested or previously pooled inputs are not accepted")
        _inputs(member.context, member.manifest, member.contract, member.attacks)
        for part in member.manifest.partitions:
            if part.dataset_id in datasets and datasets[part.dataset_id] != part.role:
                raise ValueError("pool dataset identifier crosses partition roles")
            datasets[part.dataset_id] = part.role
            for example in part.examples:
                for kind, value in (("question", example.question_id), ("content", example.content_identity)):
                    key = part.role, kind, value
                    if key in groups and groups[key] != example.split_identity:
                        raise ValueError("related pool observations must share a split identity")
                    groups[key] = example.split_identity
                # IDs are global across the pool; custody must assign shared group IDs.
                for kind, value in (("example", example.example_id), ("question", example.question_id),
                                    ("group", example.split_identity), ("run", example.validation_id),
                                    ("content", example.content_identity)):
                    key = kind, value
                    if key in seen:
                        role, domain = seen[key]
                        if role != part.role or (kind != "group" and domain != member.context.plan.domain):
                            raise ValueError("pool split leakage or duplicate observation: " + kind)
                    seen[key] = part.role, member.context.plan.domain
    return members


def _semantics(member):
    context = member.context
    # Domain labels, analyzer routing versions and reputation snapshots remain
    # separately bound. Pool only games with identical decision/task semantics.
    plan = context.plan
    candidate_fields = ("verifier_name", "registered", "eligible", "capability_source", "cost", "latency",
                        "requires_reference", "configured_readiness", "prerequisite_status", "exclusion_reason")
    candidates = [dict(**{field: getattr(c, field) for field in candidate_fields},
        expected_capabilities=sorted(set(c.expected_capabilities)), limitations=sorted(set(c.limitations)))
        for c in plan.candidates]
    return canonical_json({"requirements": context.requirement_signature,
        "candidates": sorted(candidates, key=lambda c: c["verifier_name"]),
        "reference": plan.reference_available, "minimum": context.minimum_participant_count,
        "costs": context.attempt_costs, "budget": context.budget, "units": context.cost_units,
        "loss": context.loss_configuration.model_dump(mode="json"),
        "dependencies": context.dependencies.model_dump(mode="json"),
        "aggregations": context.aggregation_versions,
        "execution": member.contract.model_dump(mode="json"),
        "attacks": member.attacks.model_dump(mode="json"), "evidence": member.manifest.evidence_kind,
        "strategies": [s.model_dump(mode="json") for s in enumerate_strategies(context).strategies]})


def fit_pooled_policies(members, *, pool_id, source_weights):
    """Return (pool contract, ((domain, context, policy), ...), source evaluations).

    source_weights explicitly names contributing domains and positive weights.
    Other members are applicability targets only; their development labels never
    enter this fit. Targets still require independent history and held-out data.
    """
    members = _validate_members(members)
    lookup = {m.context.plan.domain: m for m in members}
    pairs = tuple(source_weights)
    weights = dict(pairs)
    if len(weights) != len(pairs) or len(weights) < 2 or not set(weights) <= set(lookup):
        raise ValueError("pool requires at least two unique explicit source domains")
    if any(isinstance(w, bool) or not isinstance(w, (float, int)) or not math.isfinite(w) or w <= 0 for w in weights.values()):
        raise ValueError("source weights must be finite and positive")
    if not math.isclose(math.fsum(weights.values()), 1., rel_tol=0., abs_tol=1e-12):
        raise ValueError("source weights must sum to one")
    if len({_semantics(m) for m in members}) != 1:
        raise ValueError("pool members have incompatible task, execution, cost, loss or strategy semantics")
    evaluations = tuple((domain, construct_payoffs(lookup[domain].context, lookup[domain].manifest,
        lookup[domain].contract, lookup[domain].attacks)) for domain in sorted(weights))
    first = evaluations[0][1].matrix
    if any(e.matrix.strategy_definitions != first.strategy_definitions or e.matrix.attack_ids != first.attack_ids
           for _, e in evaluations):
        raise ValueError("pool requires identical complete matrix row and attack definitions")
    values = tuple(tuple(math.fsum(weights[d] * e.matrix.values[i][j] for d, e in evaluations)
                         for j in range(len(first.attack_ids))) for i in range(len(first.strategy_ids)))
    pooling = PoolingContract(pool_id=pool_id,
        sources=tuple(PoolSource(domain=d, compatibility_id=lookup[d].context.compatibility_id,
            manifest_id=e.manifest_id, matrix_id=e.matrix.matrix_id, weight=float(weights[d])) for d, e in evaluations),
        applicability=tuple((d, m.context.compatibility_id) for d, m in lookup.items()),
        payoff_digest=pooled_payoff_digest(first.strategy_definitions, first.attack_ids, values))
    fitted = []
    shared_policy = None
    for domain in sorted(lookup):
        data = lookup[domain].context.model_dump()
        data["pooling_contract_json"] = canonical_json(pooling.model_dump(mode="json"))
        context = PlanningContext(**data)
        matrix = PayoffMatrix(strategy_ids=first.strategy_ids, strategy_definitions=first.strategy_definitions,
            attack_ids=first.attack_ids, values=values, compatibility_id=context.compatibility_id)
        if shared_policy is None:
            shared_policy = build_policy(context, matrix)
            policy = shared_policy
        else:
            # Solve the pooled game once. Degenerate optimal games must not pick
            # different mixtures merely because another target is being bound.
            policy = validate_policy(Policy(version=shared_policy.version,
                compatibility_id=context.compatibility_id, provenance=context.provenance,
                matrix=matrix, strategies=matrix.strategy_definitions,
                solution=shared_policy.solution.model_copy(update={"matrix_id": matrix.matrix_id})), context)
        fitted.append((domain, context, policy))
    return pooling, tuple(fitted), evaluations


def evaluate_pooled_final_test(policy, context, member):
    """Score one frozen target policy without rebuilding the pool or fitting."""
    from app.game.pooling_contract import unpooled_context
    member = PoolMember.model_validate(member)
    context = PlanningContext.model_validate(context)
    if context.pooling_contract_json is None or unpooled_context(context) != member.context:
        raise ValueError("pooled policy does not bind this exact target member")
    return evaluate_final_test(policy, context, member.manifest, member.contract, member.attacks)
