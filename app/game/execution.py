"""Explicit complete-team game execution. Never imports offline data or optimizers."""

from copy import deepcopy
from dataclasses import asdict, dataclass
import math

from pydantic import ValidationError

from app.decision.decision_engine import DecisionDetail
from app.decision.report_identity import canonical_reports
from app.decision.vote_normalization import is_abstention
from app.game.artifacts import DeploymentEpisode, PolicyArtifact
from app.game.finalization import finalize_decision
from app.game.frozen_planning import PlanningMismatch, frozen_selector
from app.game.models import capture_context, content_id
from app.game.policy import sample_policy
from app.game.strategies import enumerate_strategies
from app.selection.models import VerifierUnavailable


class VerifierExecutionFailure(RuntimeError):
    """Deliberately identified recoverable execution failure, never a programming error.

    Adapters may explicitly raise this after classifying an upstream failure.
    RuntimeError, ValueError, unexpected imports/model errors, etc. propagate.
    """


@dataclass(frozen=True)
class GameRun:
    results: tuple
    detail: object
    public_status: str
    summary: dict


@dataclass(frozen=True)
class GameRuntime:
    provider: object
    episode: DeploymentEpisode
    rng: object
    allow_synthetic_for_tests: bool = False
    # Adapter-owned observations; no automatic model/service probing in the engine.
    resource_observer: object = None
    domain_routes: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, "episode", DeploymentEpisode.model_validate(self.episode))
        if type(self.allow_synthetic_for_tests) is not bool:
            raise TypeError("test-only artifact permission must be an explicit boolean")
        from app.game.domain_routing import DomainRoute
        routes = tuple(DomainRoute.model_validate(r) for r in self.domain_routes)
        if len({r.domain for r in routes}) != len(routes):
            raise ValueError("domain routes must be unique")
        object.__setattr__(self, "domain_routes", routes)

    def run(self, selector, analysis, request, validation_id):
        if self.domain_routes:
            route = next((r for r in self.domain_routes if r.domain == analysis.domain), None)
            if route is None:
                # Empty provider guarantees no accidental execution via an anchor episode.
                from app.game.artifacts import InMemoryPolicyProvider
                run = GameRuntime(InMemoryPolicyProvider(), self.episode, self.rng,
                    self.allow_synthetic_for_tests, self.resource_observer).run(selector, analysis, request, validation_id)
                run.summary.update(selection_status="unmapped_domain", selection_reasons=["no explicit domain route"])
                return run
            episode = route.pooled_episode if route.is_sparse else route.direct_episode
            run = GameRuntime(self.provider, episode, self.rng, self.allow_synthetic_for_tests,
                              self.resource_observer).run(selector, analysis, request, validation_id)
            run.summary.update(policy_route="pooled" if route.is_sparse else "direct",
                routing_domain=route.domain, routing_rule="minimum_eligible_candidate_history_v1",
                routing_history_observations=route.history_observations,
                routing_minimum_history_observations=route.minimum_history_observations)
            return run
        # Capture all externally replaceable references once, before planning or dispatch.
        episode = DeploymentEpisode.model_validate(self.episode)
        registered = tuple(self.provider.snapshot())
        context, contract = episode.context, episode.contract
        artifact_ids = sorted(
            str(getattr(artifact, "artifact_id", ""))
            for artifact in registered
        )
        effective_configuration_fingerprint = content_id({
            "episode_id": episode.episode_id,
            "execution_configuration_id": episode.execution_configuration_id,
            "execution_contract": contract.model_dump(mode="json"),
            "registered_artifact_ids": artifact_ids,
        })
        summary = dict(audit_version="game_execution_audit_v1", execution_mode="game",
            episode_id=episode.episode_id,
            effective_configuration_fingerprint=effective_configuration_fingerprint,
            artifact_id=None, policy_id=None, matrix_id=None,
            reputation_snapshot_id=context.reputation_snapshot_id,
            offline_evaluation_id=context.offline_evaluation_id, selected_strategy_id=None,
            team=[], aggregation=None, threshold=contract.threshold,
            execution_contract=contract.model_dump(mode="json"),
            execution_configuration_id=episode.execution_configuration_id,
            dependency_assumptions=list(context.dependencies.assumptions),
            budget=context.budget, cost_units=context.cost_units,
            estimated_selected_cost=0., estimated_attempted_cost=0.,
            attempted_verifiers=[], attempts=[], selection_status="pending", selection_reasons=[],
            numerical_decision=None, public_status="uncertain", override_reasons=[],
            contributors=0, minimum_contributors=context.minimum_participant_count,
            pooling_contract_json=context.pooling_contract_json,
            expected_resource_manifest_id=None if contract.resource_manifest is None else contract.resource_manifest.manifest_id,
            observed_resource_manifest_id=None,
            required=sorted(set(context.plan.requirements.requirements + context.plan.requirements.unsupported)),
            achieved=[], unresolved=sorted(set(context.plan.requirements.requirements + context.plan.requirements.unsupported)))

        def failed(code, explanation):
            summary.update(selection_status=code, selection_reasons=[explanation], override_reasons=["selection_failure"])
            detail = DecisionDetail(analysis.domain, "unknown", 0., 0., contract.threshold, "unknown", ())
            summary["numerical_decision"] = asdict(detail)
            return GameRun((), detail, "uncertain", deepcopy(summary))

        try:
            planned_selector = frozen_selector(selector, context)
            configuration = context.model_dump(exclude={"selection_json", "analyzer_provenance"})
            current = capture_context(planned_selector, analysis, context=request.context, **configuration)
        except (PlanningMismatch, ValidationError, ValueError) as exc:
            return failed("incompatible", str(exc))
        feasible = enumerate_strategies(current)
        if not feasible.strategies:
            return failed("no_feasible_strategy", "; ".join(reason for row in feasible.rejected for reason in row.reasons))
        if current.compatibility_id != context.compatibility_id:
            return failed("incompatible", "current analyzer/requirements/candidates/prerequisites/configuration differ from episode")
        matching, rejected = [], []
        for supplied in registered:
            try:
                artifact = PolicyArtifact.model_validate(supplied)
            except (ValidationError, ValueError) as exc:
                rejected.append("invalid artifact: " + str(exc))
                continue
            if artifact.applicable_domain != analysis.domain or artifact.context.compatibility_id != current.compatibility_id:
                rejected.append("incompatible artifact")
                continue
            if artifact.policy.provenance.evidence_kind != "empirical" and not self.allow_synthetic_for_tests:
                rejected.append("synthetic artifacts require explicit test-only permission")
                continue
            matching.append(artifact)
        if not matching:
            return failed("incompatible" if registered else "missing_policy", "; ".join(rejected) or "no registered policy")
        if len(matching) != 1:
            return failed("ambiguous_policy", "multiple exactly compatible registered artifacts")
        artifact = matching[0]
        if contract.resource_manifest is not None:
            from app.game.resource_provenance import ResourceManifest
            if self.resource_observer is None:
                return failed("provenance_incompatible", "resource-bound execution requires an observation adapter")
            try:
                observed = ResourceManifest.model_validate(self.resource_observer.snapshot())
                observed.require_candidates(c.verifier_name for c in current.plan.candidates)
                summary["observed_resource_manifest_id"] = observed.manifest_id
                if observed != contract.resource_manifest:
                    return failed("provenance_incompatible", "observed resources differ from evaluated resources")
            except (ValidationError, ValueError) as exc:
                return failed("provenance_incompatible", str(exc))
        # Validation already certifies definitions/costs/budget. Recheck before RNG and dispatch.
        if any(s.estimated_cost > current.budget or s.estimated_cost != math.fsum(
                dict(current.attempt_costs)[name] for name in s.verifiers) for s in artifact.policy.strategies):
            return failed("budget_rejected", "policy cost differs from estimated attempt budget")
        selection = sample_policy(artifact.policy, current, rng=self.rng)
        strategy = next(s for s in artifact.policy.strategies if s.strategy_id == selection.strategy_id)
        summary.update(artifact_id=artifact.artifact_id, policy_id=artifact.policy.policy_id,
            matrix_id=artifact.policy.matrix.matrix_id, selected_strategy_id=strategy.strategy_id,
            team=list(strategy.verifiers), aggregation=strategy.aggregation,
            estimated_selected_cost=strategy.estimated_cost, selection_status="selected")
        results, states, attempts = [], [], []
        for name in strategy.verifiers:
            cost = dict(current.attempt_costs)[name]
            record = dict(verifier_name=name, estimated_attempt_cost=cost)
            try:
                verifier = planned_selector.resolve(name)
                raw = verifier.verify(request.question, request.answer, request.context)
            except VerifierUnavailable as exc:
                state = "unavailable"
                record["reason"] = str(exc)
            except VerifierExecutionFailure as exc:
                state = "failed"
                record["reason"] = str(exc)
            else:
                checked, _, _ = canonical_reports([raw], team=(name,), validation_id=validation_id, deduplicate=False)
                raw = checked[0]
                state = "abstention" if is_abstention(raw) else "directional"
                results.append(raw)
            record["state"] = state
            states.append((name, state))
            attempts.append(record)
        finalized = finalize_decision(current, strategy, contract, results, states, validation_id)
        resource_drift = False
        if contract.resource_manifest is not None:
            try:
                after = ResourceManifest.model_validate(self.resource_observer.snapshot())
                summary["after_resource_manifest_id"] = after.manifest_id
                resource_drift = after != observed
            except (ValidationError, ValueError) as exc:
                summary["resource_observation_error"] = str(exc)
                resource_drift = True
        summary.update(attempted_verifiers=list(strategy.verifiers), attempts=attempts,
            estimated_attempted_cost=math.fsum(a["estimated_attempt_cost"] for a in attempts),
            contributors=finalized.contributors, minimum_contributors=current.minimum_participant_count,
            required=list(finalized.required), achieved=list(finalized.achieved), unresolved=list(finalized.unresolved),
            override_reasons=list(finalized.reasons), numerical_decision=finalized.detail.to_dict(),
            public_status=finalized.public_status, selection_plan=current.plan.to_dict(),
            termination="complete_selected_team", early_stopping_enabled=False, fallback_enabled=False)
        if resource_drift:
            summary["override_reasons"].append("resource_provenance_changed_during_execution")
            summary["public_status"] = "uncertain"
        return GameRun(tuple(results), finalized.detail, summary["public_status"], deepcopy(summary))
