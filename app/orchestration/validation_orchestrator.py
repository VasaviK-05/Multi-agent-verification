"""Validation orchestrator — coordinates the validation pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from copy import deepcopy
import json
import threading
from uuid import UUID, uuid4

from app.analysis.question_analyzer import QuestionAnalysis, QuestionAnalyzer
from app.database.reputation_repository import (
    build_reputation_state,
    load_reputation_manager_state,
    load_reputation_state,
    save_reputation,
    save_reputation_manager_state,
    save_reputation_state_and_rows,
)
from app.decision.decision_engine import DecisionDetail, DecisionEngine
from app.evaluation.automatic_ground_truth import AutomaticGroundTruthEvaluator
from app.ground_truth.storage import save_ground_truth
from app.decision.coverage import ARITHMETIC_RULES, factual_capabilities as _factual_capabilities
from app.decision.early_termination import AdaptiveEarlyTermination
from app.decision.vote_normalization import (
    confidence_judgment_tie,
    is_abstention,
    vote_confidence,
)
from app.database.validation_repository import (
    create_validation_record,
    get_validation,
)
from app.database.execution_journal_repository import (
    begin_validation,
    mark_execution_ready,
    mark_execution_running,
    mark_execution_completed,
    mark_execution_failed,
    update_execution_plan,
    create_verifier_attempt,
    mark_verifier_attempt_started,
    mark_verifier_attempt_completed,
    mark_verifier_attempt_unavailable,
    mark_verifier_attempt_failed,
    mark_verifier_attempt_error,
)
from app.database.execution_lease import ExecutionLeaseHeartbeat
from app.database.verifier_repository import get_verifier_outputs
from app.models.schemas import ValidationRequest, ValidationResponse, VerificationResult
from app.reputation.reputation_manager import FeedbackEvent, ReputationManager
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.selection.models import VerifierUnavailable
from app.selection.baseline_budget import (
    BudgetLedger, capture_baseline_budget_configuration, plan_with_budget,
)
from database import get_connection
from time import perf_counter


class _GameExecutionObserver:
    """Conservative, monotonic dispatch boundary, also without persistence."""
    def __init__(self, journal=None):
        self.journal = journal
        self.started = False

    def set_plan(self, plan):
        if self.journal is not None:
            return self.journal.set_plan(plan)

    def start_attempt(self, **kwargs):
        # Set before journal work and before either atomic/component verify().
        self.started = True
        if self.journal is not None:
            return self.journal.start_attempt(**kwargs)
        return {"attempt_id": None}

    def complete_attempt(self, token, **kwargs):
        if self.journal is not None:
            return self.journal.complete_attempt(token, **kwargs)

    def unavailable_attempt(self, token, **kwargs):
        if self.journal is not None:
            return self.journal.unavailable_attempt(token, **kwargs)

    def failed_attempt(self, token, **kwargs):
        if self.journal is not None:
            return self.journal.failed_attempt(token, **kwargs)


@dataclass(frozen=True)
class _GameInitializationFailure:
    """Only explicitly classified service initialization failures reach here."""
    diagnostics: dict

    def run(self, selector, analysis, request, validation_id, **kwargs):
        from app.game.execution import GameRun
        return GameRun((), None, "uncertain", {
            "selection_status": self.diagnostics["status"],
            "selection_reasons": [self.diagnostics["error_message"]],
            "initialization_failure": dict(self.diagnostics),
        })


@dataclass
class _BorrowedExecution:
    lease_token: str
    heartbeat: ExecutionLeaseHeartbeat
    failure_recorded: bool = False
    terminalization_attempted: bool = False


class _GameExecutionJournal:
    """Small callback passed to game call sites; never wraps verifier objects."""
    def __init__(self, validation_id, lease_token, heartbeat):
        self.validation_id = validation_id
        self.lease_token = lease_token
        self.heartbeat = heartbeat
        self.order = 0
        self.attempts = []

    def set_plan(self, plan):
        self.heartbeat.assert_owned()
        update_execution_plan(validation_id=self.validation_id,
                              plan_payload=plan, lease_token=self.lease_token)

    def start_attempt(self, *, verifier_name, component_id=None,
                       report_validation_id=None, binding_id=None,
                       call_id=None, estimated_cost=None):
        self.heartbeat.assert_owned()
        order = self.order
        self.order += 1
        identity = {}
        if binding_id is not None:
            identity["binding_id"] = binding_id
        if call_id is not None:
            identity["call_id"] = call_id
        if component_id is not None:
            identity["component_id"] = component_id
        attempt = create_verifier_attempt(
            validation_id=self.validation_id,
            call_key=call_id or f"game:{order}:{verifier_name}",
            execution_order=order,
            verifier_name=verifier_name,
            component_id=component_id,
            report_validation_id=report_validation_id,
            identity_binding=identity,
            lease_token=self.lease_token,
        )
        self.heartbeat.assert_owned()
        mark_verifier_attempt_started(
            attempt_id=attempt["attempt_id"], lease_token=self.lease_token
        )
        token = {"attempt_id": attempt["attempt_id"],
                 "started": perf_counter(), "estimated_cost": estimated_cost,
                 "verifier_name": verifier_name, "component_id": component_id,
                 "report_validation_id": report_validation_id,
                 "binding_id": binding_id}
        self.attempts.append(token)
        return token

    def complete_attempt(self, token, *, report, outcome):
        self.heartbeat.assert_owned()
        return mark_verifier_attempt_completed(
            attempt_id=token["attempt_id"], report=report,
            outcome=outcome, duration_ms=(perf_counter()-token["started"])*1000,
            estimated_cost=token["estimated_cost"], lease_token=self.lease_token,
        )

    def unavailable_attempt(self, token, *, reason):
        self.heartbeat.assert_owned()
        return mark_verifier_attempt_unavailable(
            attempt_id=token["attempt_id"], reason=reason,
            duration_ms=(perf_counter()-token["started"])*1000,
            estimated_cost=token["estimated_cost"], lease_token=self.lease_token,
        )

    def failed_attempt(self, token, *, error):
        self.heartbeat.assert_owned()
        return mark_verifier_attempt_failed(
            attempt_id=token["attempt_id"], error_type=type(error).__name__,
            error_message=str(error) or type(error).__name__,
            duration_ms=(perf_counter()-token["started"])*1000,
            estimated_cost=token["estimated_cost"], lease_token=self.lease_token,
        )


@dataclass(frozen=True)
class ValidationContext:
    """Identity and domain captured when a validation ran.

    Feedback uses this record. It does not read a later ``_last_analysis``.
    """

    validation_id: str
    domain: str
    results: tuple[VerificationResult, ...]
    decision: DecisionDetail | None
    run_summary: dict


class ValidationOrchestrator:
    """Runs analyzer → selector → verifiers, with early stopping → decision.

    The selector and the decision engine share one ReputationManager.
    ``analyze().domain`` is the domain both of them use.

    ``validate`` does not update reputation. Call ``record_ground_truth``
    only when an external boolean label arrives later. The final status
    produced here is not that label. Each validation keeps its own domain
    for that later label. The latest analysis is not the default domain.
    """

    def __init__(
        self,
        question_analyzer: QuestionAnalyzer | None = None,
        verifier_selector: VerifierSelector | None = None,
        decision_engine: DecisionEngine | None = None,
        reputation_manager: ReputationManager | None = None,
        early_termination: AdaptiveEarlyTermination | None = None,
        *,
        execution_mode: str = "baseline",
        game_runtime=None,
        persist_execution: bool = False,
        baseline_budget_provider=None,
    ) -> None:
        
        if execution_mode not in {"baseline", "game"}:
            raise ValueError("execution_mode must be baseline or game")

        if execution_mode == "game":
            from app.game.execution import GameRuntime
            from app.game.deployment import FlexiblePolicyGameRuntime, PrototypeGameRuntime

            if not isinstance(
                game_runtime,
                (GameRuntime, PrototypeGameRuntime, FlexiblePolicyGameRuntime, _GameInitializationFailure),
            ):
                raise ValueError(
                    "game mode requires a server-configured GameRuntime"
                )

        elif game_runtime is not None:
            raise ValueError("game runtime requires explicit game mode")

        self._execution_mode = execution_mode
        self._baseline_budget_provider = baseline_budget_provider or capture_baseline_budget_configuration
        self._persist_execution = persist_execution
        self._game_runtime = game_runtime

        if question_analyzer is not None:
            self._question_analyzer = question_analyzer
        elif execution_mode == "game":
            from app.analysis.task_analyzer import TaskQuestionAnalyzer
            self._question_analyzer = TaskQuestionAnalyzer()
        else:
            self._question_analyzer = QuestionAnalyzer()

        self._early_termination = early_termination or AdaptiveEarlyTermination()
        self._automatic_ground_truth = AutomaticGroundTruthEvaluator() if execution_mode == "baseline" else None
        self._last_analysis: QuestionAnalysis | None = None
        self._contexts: dict[str, ValidationContext] = {}
        # Strong refs to the result objects validate() returned. Lookup checks
        # identity with ``is``; the id is only a slot. Snapshots stay separate.
        self._result_binding: dict[int, tuple[VerificationResult, str]] = {}
        self._attempt_binding: dict[int, tuple[VerificationResult, str]] = {}
        # Serialize this orchestrator's learning and absolute posterior writes.
        # Dirty pairs survive a failed save, not a process restart.
        self._feedback_lock = threading.RLock()
        self._pending_posterior_pairs: set[tuple[str, str]] = set()
        selector_factory = VerifierSelector
        if execution_mode == "baseline":
            from app.selection.baseline_resources import BaselineVerifierSelector, load_baseline_evidence_configuration
            selector_factory = BaselineVerifierSelector
        self._verifier_selector, self._decision_engine, self._reputation_manager = (
            self._assemble(verifier_selector, decision_engine, reputation_manager,
                           selector_factory=selector_factory)
        )
        if execution_mode == "baseline" and verifier_selector is None:
            self._verifier_selector.configure_baseline_evidence(load_baseline_evidence_configuration())

    @staticmethod
    def _assemble(
        verifier_selector: VerifierSelector | None,
        decision_engine: DecisionEngine | None,
        reputation_manager: ReputationManager | None,
        *,
        selector_factory=VerifierSelector,
    ) -> tuple[VerifierSelector, DecisionEngine, ReputationManager]:
        if verifier_selector is None and decision_engine is None:
            shared = reputation_manager or ReputationManager()

            if reputation_manager is None:
                saved_state = load_reputation_manager_state()
                if saved_state is not None:
                    shared.restore_state(saved_state)
                else:
                    shared.restore_state(build_reputation_state())

            return (
                selector_factory(reputation_manager=shared, capabilities=BUILTIN_CAPABILITIES),
                DecisionEngine(reputation_manager=shared),
                shared,
            )

        if verifier_selector is None:
            assert decision_engine is not None
            shared = reputation_manager or decision_engine.reputation_manager
            if (
                reputation_manager is not None
                and decision_engine.reputation_manager is not reputation_manager
            ):
                raise ValueError(
                    "DecisionEngine must use the orchestrator's ReputationManager."
                )
            return (
                selector_factory(reputation_manager=shared, capabilities=BUILTIN_CAPABILITIES),
                decision_engine,
                shared,
            )

        if decision_engine is None:
            shared = reputation_manager or verifier_selector.reputation_manager
            if (
                reputation_manager is not None
                and verifier_selector.reputation_manager is not reputation_manager
            ):
                raise ValueError(
                    "VerifierSelector must use the orchestrator's ReputationManager."
                )
            return (
                verifier_selector,
                DecisionEngine(reputation_manager=shared),
                shared,
            )

        if reputation_manager is None:
            if verifier_selector.reputation_manager is not decision_engine.reputation_manager:
                raise ValueError(
                    "VerifierSelector and DecisionEngine must share one ReputationManager."
                )
            return (
                verifier_selector,
                decision_engine,
                verifier_selector.reputation_manager,
            )

        if (
            verifier_selector.reputation_manager is not reputation_manager
            or decision_engine.reputation_manager is not reputation_manager
        ):
            raise ValueError(
                "Injected selector and decision engine must use the orchestrator's ReputationManager."
            )
        return verifier_selector, decision_engine, reputation_manager

    @property
    def reputation_manager(self) -> ReputationManager:
        return self._reputation_manager

    @property
    def verifier_selector(self) -> VerifierSelector:
        return self._verifier_selector

    @property
    def decision_engine(self) -> DecisionEngine:
        return self._decision_engine

    @property
    def last_analysis(self) -> QuestionAnalysis | None:
        return self._last_analysis

    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """Run ranked candidates until an approved, covered stop or exhaustion."""
        # Capture server configuration once, before analysis. Game never consults it.
        budget_snapshot = (self._baseline_budget_provider(self._verifier_selector)
                           if self._execution_mode == "baseline" else None)
        analysis = self._question_analyzer.analyze(request.question)
        self._last_analysis = analysis
        validation_id = str(uuid4())
        if self._execution_mode == "game":
            return self._validate_game(request, analysis, validation_id)

        return self._execute_baseline(request, analysis, validation_id, budget_snapshot)

    def _execute_baseline(self, request, analysis, validation_id, budget_snapshot,
                          *, prepared=None, lifecycle=None, fallback_audit=None):
        """Shared execution body; a handoff borrows the live Game lease unchanged."""
        # The fallback caller owns borrowed-lease failure/heartbeat cleanup.
        return self._execute_baseline_body(request, analysis, validation_id, budget_snapshot,
            prepared=prepared, lifecycle=lifecycle, fallback_audit=fallback_audit)

    def _execute_baseline_body(self, request, analysis, validation_id, budget_snapshot,
                               *, prepared=None, lifecycle=None, fallback_audit=None):
        def record_failure(**kwargs):
            if lifecycle is not None:
                lifecycle.terminalization_attempted = True
            mark_execution_failed(**kwargs)
            if lifecycle is not None:
                lifecycle.failure_recorded = True

        budget = BudgetLedger(budget_snapshot, validation_id)
        baseline_evidence = getattr(self._verifier_selector, "baseline_evidence_configuration", None)
        if self._persist_execution and lifecycle is None:
            connection = get_connection()
            try:
                create_validation_record(
                    validation_id=validation_id,
                    question_id=request.question_id,
                    question=request.question,
                    generated_answer=request.answer,
                    context=request.context,
                    session_id=request.session_id,
                    connection=connection,
                )

                begin_validation(
                    validation_id=validation_id,
                    execution_mode="baseline",
                    request_payload={
                        "question": request.question,
                        "answer": request.answer,
                        "context": request.context,
                        "question_id": request.question_id,
                        "session_id": request.session_id,
                    },
                    connection=connection,
                )

                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

        lease_token, heartbeat = ((lifecycle.lease_token, lifecycle.heartbeat)
                                  if lifecycle is not None else (None, None))

        try:
            plan, admission = prepared if prepared is not None else (
                self._verifier_selector.plan(analysis, request.context), None)
            if admission is None:
                admission = plan_with_budget(plan, budget_snapshot)
            budget.plan = admission

            if self._persist_execution and lifecycle is not None:
                heartbeat.assert_owned()
                update_execution_plan(validation_id=validation_id, lease_token=lease_token,
                    plan_payload={**plan.to_dict(), "baseline_budget": budget.audit(),
                                  **(fallback_audit or {})})
            elif self._persist_execution:
                mark_execution_ready(
                    validation_id=validation_id,
                    plan_payload={**plan.to_dict(), "baseline_budget": budget.audit()},
                    analysis_snapshot={
                        "domain": analysis.domain,
                        "difficulty": analysis.difficulty,
                    },
                )

                running_execution = mark_execution_running(
                    validation_id=validation_id,
                    worker_id=f"worker-{uuid4()}",
                )
                lease_token = running_execution["lease_token"]

                heartbeat = ExecutionLeaseHeartbeat(
                    validation_id=validation_id,
                    lease_token=lease_token,
                ).start()

        except Exception as exc:
            if self._persist_execution:
                record_failure(
                    validation_id=validation_id,
                    lease_token=lease_token,
                    failure_details={**(fallback_audit or {}),
                        "error_type": type(exc).__name__,
                        "error_message": str(exc) or type(exc).__name__,
                        "stage": "verifier_planning",
                    },
                )
            raise

        minimum = plan.minimum_count
        if analysis.difficulty != "hard":
            minimum = max(2, minimum)
        initial_selected = admission.initial_selected
        names = initial_selected + admission.fallback
        required = plan.requirements.requirements + plan.requirements.unsupported
        # Only these existing result contracts establish achieved coverage.
        unsupported_contracts = sorted(set(required) - {"direct_fact", "arithmetic"})
        coverage = {
            capability: {
                # Historical boolean retained, now strictly observed: a declared
                # or output-qualified candidate returned a result. Not coverage.
                "available": False,
                "planned_candidates": [name for name in names if any(
                    row.verifier_name == name and capability in row.expected_capabilities
                    for row in plan.candidates)],
                "runtime_available": [], "runtime_unavailable": [],
                "unattempted": [name for name in names if any(
                    row.verifier_name == name and capability in row.expected_capabilities
                    for row in plan.candidates)],
                "achieved_contract": capability in {"direct_fact", "arithmetic"},
                "attempts": [], "directional": [],
            }
            for capability in sorted(required)
        }
        results: list[VerificationResult] = []
        abstained: list[str] = []
        detail = None
        reason = "candidate_exhaustion" if admission.feasible else "budget_planning_infeasible"
        last_assessment = None
        attempted = []
        unavailable = []
        runtime_availability = {row.verifier_name: "unobserved" for row in plan.candidates}
        stopping_policy_vetoes = []
        attempt_records = {}

        if self._persist_execution:
            try:
                for execution_order, name in enumerate(names):
                    attempt_records[name] = create_verifier_attempt(
                        validation_id=validation_id,
                        call_key=f"{execution_order}:{name}",
                        execution_order=execution_order,
                        verifier_name=name,
                        lease_token=lease_token,
                    )
            except Exception as exc:
                record_failure(
                    validation_id=validation_id,
                    lease_token=lease_token,
                    failure_details={**(fallback_audit or {}),
                        "error_type": type(exc).__name__,
                        "error_message": str(exc) or type(exc).__name__,
                        "stage": "attempt_creation",
                    },
                )
                raise

        for name in names:
            if not budget.admit(name):
                runtime_availability[name] = "budget_not_admitted"
                continue
            attempted.append(name)
            attempt_id = (
                attempt_records[name]["attempt_id"]
                if self._persist_execution
                else None
            )

            if self._persist_execution:
                heartbeat.assert_owned()
                mark_verifier_attempt_started(
                    attempt_id=attempt_id,
                    lease_token=lease_token,
                )

            try:
                verifier = self._verifier_selector.resolve(name)
                raw = budget.verify(verifier, request.question, request.answer, request.context)
            except VerifierUnavailable as exc:
                if self._persist_execution:
                    mark_verifier_attempt_unavailable(
                        attempt_id=attempt_id,
                        reason=str(exc),
                        **budget.metrics(name),
                        lease_token=lease_token,
                    )

                unavailable.append({"verifier": name, "reason": str(exc)})
                runtime_availability[name] = "unavailable"
                for row in coverage.values():
                    if name in row["unattempted"]:
                        row["unattempted"].remove(name)
                        row["runtime_unavailable"].append(name)
                        row["attempts"].append(
                            {"verifier": name, "state": "unavailable"}
                        )
                continue

            except BaseException as exc:
                if fallback_audit is not None:
                    fallback_audit.update(
                        fallback_decision="interrupted" if not isinstance(exc, Exception) else "failed",
                        baseline_failure={"error_type": type(exc).__name__, "error_message": str(exc)})
                try:
                    if self._persist_execution:
                        mark_verifier_attempt_error(
                            attempt_id=attempt_id,
                            error_type=type(exc).__name__,
                            error_message=str(exc) or type(exc).__name__,
                            **budget.metrics(name),
                            lease_token=lease_token,
                        )
                        record_failure(
                            validation_id=validation_id,
                            lease_token=lease_token,
                            failure_details={**(fallback_audit or {}),
                                "error_type": type(exc).__name__,
                                "error_message": str(exc) or type(exc).__name__,
                                "baseline_budget": budget.audit(),
                            },
                        )
                except BaseException as recording_error:
                    if lifecycle is None or isinstance(exc, Exception):
                        raise
                    fallback_audit["attempt_failure_recording_error"] = {
                        "error_type": type(recording_error).__name__, "error_message": str(recording_error)}
                raise

            if raw.verifier_name != name:
                if self._persist_execution:
                    mark_verifier_attempt_error(
                        attempt_id=attempt_id,
                        error_type="VerifierIdentityMismatch",
                        error_message="returned verifier_name does not match planned candidate",
                        **budget.metrics(name),
                        lease_token=lease_token,
                    )
                    record_failure(
                        validation_id=validation_id,
                        lease_token=lease_token,
                        failure_details={**(fallback_audit or {}),
                            "error_type": "VerifierIdentityMismatch",
                            "error_message": "returned verifier_name does not match planned candidate",
                        },
                    )
                raise ValueError(
                    "returned verifier_name does not match planned candidate"
                )

            runtime_availability[name] = "returned_result"
            abstention = is_abstention(raw)

            if self._persist_execution:
                heartbeat.assert_owned()
                mark_verifier_attempt_completed(
                    attempt_id=attempt_id,
                    report=raw.model_dump(mode="json"),
                    outcome="abstention" if abstention else "directional",
                    **budget.metrics(name),
                    lease_token=lease_token,
                )

            annotated = _annotate(
                raw, abstained_before=list(abstained), abstention=abstention
            )
            results.append(annotated)

            if self._persist_execution and attempt_id is not None:
                self._attempt_binding[id(annotated)] = (annotated, attempt_id)

            if abstention:
                abstained.append(raw.verifier_name)

            _track_coverage(coverage, raw)
            assessment = self._early_termination.should_terminate(
                results, analysis, minimum,
                decision_engine=self._decision_engine,
            )
            last_assessment = assessment["reason"]
            vetoes = []

            if assessment["terminate"]:
                if plan.requirements.status == "invalid":
                    vetoes.append("invalid_requirement_context")
                elif not plan.requirements.requirements_known:
                    vetoes.append("requirements_unknown")
                if plan.requirements.unsupported:
                    vetoes.append("unsupported_requirements")
                if any(n not in attempted for n in initial_selected):
                    vetoes.append("initial_team_incomplete")
                if analysis.difficulty == "hard":
                    vetoes.append("hard_question")
                for capability, row in coverage.items():
                    if not row["directional"]:
                        prefix = (
                            "missing_achieved_coverage"
                            if row["achieved_contract"]
                            else "no_achieved_coverage_contract"
                        )
                        vetoes.append(f"{prefix}:{capability}")
                if vetoes:
                    stopping_policy_vetoes.append({
                        "after_verifier": name,
                        "result_count": len(results),
                        "numerical_assessment": assessment["reason"],
                        "reasons": vetoes,
                    })

            if assessment["terminate"] and not vetoes:
                detail = assessment["decision"]
                reason = "approved_early_stop"
                break

        if reason == "candidate_exhaustion" and budget.skipped:
            reason = "actual_budget_exhaustion"
        if detail is None:
            detail = self._decision_engine.decide_detailed(results, domain=analysis.domain)
        contributors = self._early_termination.contributor_count(detail, results)
        missing = [key for key, row in coverage.items() if not row["directional"]]
        final_status = detail.status
        uncertainty_reasons = []
        if reason in {"budget_planning_infeasible", "actual_budget_exhaustion"}:
            final_status = "uncertain"
            uncertainty_reasons.append(reason)

        if contributors < minimum:
            uncertainty_reasons.append("insufficient_contributors")

        if missing:
            uncertainty_reasons.extend(
                f"missing_coverage:{key}" for key in missing
            )

        if plan.requirements.status == "invalid":
            uncertainty_reasons.append("invalid_coverage_requirements")

        for verifier_result in results:
            metadata = verifier_result.metadata or {}

            unsure_reason = metadata.get("unsure_reason")
            abstain_reason = metadata.get("abstain_reason")

            if unsure_reason:
                uncertainty_reasons.append(
                    f"{verifier_result.verifier_name}:{unsure_reason}"
                )

            if abstain_reason:
                uncertainty_reasons.append(
                    f"{verifier_result.verifier_name}:{abstain_reason}"
                )

        if (
            contributors < minimum
            or missing
            or plan.requirements.status == "invalid"
        ):
            final_status = "uncertain"

        if final_status == "uncertain" and not uncertainty_reasons:
            uncertainty_reasons.append("decision_uncertain")

        uncertainty_reasons = list(dict.fromkeys(uncertainty_reasons))
        final_score = detail.score
        summary = {
           "audit_version": "execution_audit_v2",
            "baseline_budget": budget.audit(),
            "baseline_evidence_configuration_id": (baseline_evidence.configuration_id if baseline_evidence else None),
            "uncertainty_reasons": uncertainty_reasons,
            "termination": reason,
            "last_stopping_assessment": last_assessment,
            "minimum_contributors": minimum, "contributors": contributors,
            "missing_coverage": missing, "coverage": coverage,
            "numerical_decision": asdict(detail), "public_status": final_status,
            "selection_plan": plan.to_dict(),
            "attempted_verifiers": attempted,
            "returned_result_verifiers": [result.verifier_name for result in results],
            "unavailable_verifiers": unavailable,
            "runtime_availability": runtime_availability,
            "stopping_policy_vetoes": stopping_policy_vetoes,
            "coverage_unknown": not plan.requirements.requirements_known,
            "unsupported_coverage_contracts": unsupported_contracts,
        }
        # Keep response, in-memory context, and JSONB metadata identical (the
        # detailed decision contains tuple fields before JSON normalization).
        if fallback_audit is not None:
            summary.update(fallback_audit)
            # The preparation snapshot must not replace actual attempt metrics.
            summary["baseline_budget"] = budget.audit()
            summary["baseline_execution_details"] = {
                "selection_plan": plan.to_dict(), "attempted_verifiers": attempted,
                "baseline_budget": budget.audit(), "final_decision": final_status}
        summary = json.loads(json.dumps(summary, allow_nan=False))
        if results:
            metadata = dict(results[-1].metadata or {})
            if RUN_SUMMARY_KEY in metadata:
                raise ValueError(f"reserved metadata key {RUN_SUMMARY_KEY!r} already exists")
            metadata[RUN_SUMMARY_KEY] = deepcopy(summary)
            original_result = results[-1]
            updated_result = original_result.model_copy(
                update={"metadata": metadata}
            )
            results[-1] = updated_result

            attempt_binding = self._attempt_binding.pop(
                id(original_result), None
            )
            if attempt_binding is not None:
                self._attempt_binding[id(updated_result)] = (
                    updated_result,
                    attempt_binding[1],
                )

        ground_truth = self._automatic_ground_truth.evaluate(
        question=request.question,
        answer=request.answer,
        )

        signed_score = detail.raw_score

        context = ValidationContext(
            validation_id=validation_id,
            domain=analysis.domain,
            results=_detach_results(results),
            decision=detail,
            run_summary=deepcopy(summary),
        )
        self._contexts[validation_id] = context

        for result in results:
            self._result_binding[id(result)] = (result, validation_id)

        response = ValidationResponse(
            results=results,
            final_status=final_status,
            final_score=final_score,
            validation_id=validation_id,
            domain=analysis.domain,
            session_id=request.session_id,
            ground_truth=ground_truth,
            difficulty=analysis.difficulty,
            selected_verifiers=[result.verifier_name for result in results],
            early_stop_reason=reason,
            uncertainty_reasons=uncertainty_reasons,
            signed_score=signed_score,
            execution_audit=deepcopy(summary),
        )
        if self._persist_execution:
            heartbeat.assert_owned()
            final_response = response.model_dump(mode="json")
            if lifecycle is not None:
                lifecycle.terminalization_attempted = True
            mark_execution_completed(
                validation_id=validation_id,
                final_response=final_response,
                lease_token=lease_token,
            )

        return response

    def _new_fallback_baseline(self):
        return ValidationOrchestrator(reputation_manager=self._reputation_manager,
            persist_execution=self._persist_execution,
            baseline_budget_provider=self._baseline_budget_provider)

    @staticmethod
    def _fallback_decision_audit(game_summary, execution_started=False):
        """Populate rejected decisions too, without inventing Baseline results."""
        status = game_summary.get("selection_status")
        if game_summary.get("initialization_failure"):
            stage = "initialization"
        elif status in {"resource_incompatible", "provenance_incompatible"}:
            stage = "resource_preflight"
        elif (game_summary.get("policy_category") in {"missing_policy", "unsupported_category"}
              or status in {"task_reference_mismatch", "task_out_of_scope", "unsupported_category"}):
            stage = "routing"
        elif status == "missing_policy":
            stage = "policy_lookup"
        elif execution_started:
            stage = "execution"
        else:
            stage = "strategy_selection"
        return dict(requested_mode="game", executed_mode="game", fallback_triggered=False,
            game_verifier_execution_started=execution_started, game_failure_stage=stage,
            game_failure_status=status, game_failure_reason=deepcopy(game_summary.get("selection_reasons", [])),
            game_execution_details=deepcopy(game_summary), baseline_eligibility=False,
            fallback_decision="rejected", fallback_reason=None,
            baseline_preparation_status="not_started", baseline_preparation_stage=None)

    def _try_baseline_fallback(self, request, validation_id, game_summary, audit, *, lifecycle):
        """Own cleanup until execution finishes or rejection returns ownership to Game."""
        audit.update(self._fallback_decision_audit(game_summary, audit.get("game_verifier_execution_started", False)))
        borrowed = _BorrowedExecution(*lifecycle) if lifecycle is not None else None
        resume_game = False
        propagating_error = None
        try:
            status = game_summary.get("selection_status")
            reasons = game_summary.get("selection_reasons", [])
            eligible = status in {"no_feasible_strategy", "game_policy_missing", "game_policy_incompatible"}
            # Flexible missing_policy may denote unmatched/invalid routing.
            eligible |= status == "missing_policy" and "policy_category" not in game_summary
            eligible |= status == "incompatible" and bool(reasons) and all(
                reason in {"incompatible artifact"} or reason.startswith("invalid artifact:") for reason in reasons)
            if not eligible:
                audit["fallback_rejection_reason"] = "game_failure_not_eligible"
                resume_game = True
                return None
            try:
                audit["baseline_preparation_stage"] = "request_validation"
                if not request.question.strip() or not request.answer.strip():
                    raise ValueError("request_out_of_scope")
                # Registered paraphrases have an explicit reference prerequisite.
                if request.question.strip().casefold().startswith("paraphrase this reference: ") and (
                        request.context != request.question.strip().partition(": ")[2]):
                    raise ValueError("request_prerequisite_unsatisfied")
                audit["baseline_preparation_stage"] = "selector_construction"
                audit["baseline_preparation_status"] = "in_progress"
                baseline = self._new_fallback_baseline()
                audit["baseline_preparation_stage"] = "analysis"
                analysis = baseline._question_analyzer.analyze(request.question)
                audit["baseline_preparation_stage"] = "selection_planning"
                plan = baseline._verifier_selector.plan(analysis, request.context)
                audit["baseline_selection"] = plan.to_dict()
                audit["baseline_preparation_stage"] = "requirements_validation"
                if (plan.requirements.status == "invalid" or plan.requirements.unsupported
                        or not plan.requirements.requirements_known or plan.expected_uncovered):
                    raise ValueError("baseline_coverage_unproven")
                minimum = max(plan.minimum_count, 2 if analysis.difficulty != "hard" else 1)
                if len(plan.initial_selected + plan.fallback) < minimum:
                    raise ValueError("request_prerequisite_unsatisfied" if plan.exclusions
                                     else "baseline_insufficient_contributors")
                audit["baseline_preparation_stage"] = "resource_validation"
                from app.selection.baseline_resources import validate_baseline_evidence
                selected = getattr(baseline._verifier_selector, "baseline_evidence_configuration", None)
                audit["baseline_resource_validation"] = "not_required"
                if "evidence" in plan.initial_selected + plan.fallback:
                    audit["baseline_resource_validation"] = "in_progress"
                    if selected is None:
                        raise ValueError("baseline_resources_incompatible")
                    try:
                        validate_baseline_evidence(selected)
                    except (OSError, ValueError, TypeError) as exc:
                        raise ValueError("baseline_resources_incompatible") from exc
                    audit["baseline_resource_validation"] = "passed"
                audit["baseline_preparation_stage"] = "budget_capture"
                snapshot = baseline._baseline_budget_provider(baseline._verifier_selector)
                audit["baseline_budget"] = asdict(snapshot)
                from app.utils.config import settings
                if settings.BASELINE_BUDGET_CONFIG_PATH and snapshot.status != "configured":
                    raise ValueError("baseline_budget_configuration_invalid")
                audit["baseline_preparation_stage"] = "budget_admission"
                admission = plan_with_budget(plan, snapshot)
                if not admission.feasible:
                    raise ValueError("baseline_budget_feasibility_unproven")
            except Exception as exc:
                # Preparation never dispatches. Retain diagnostics alongside the
                # original Game result rather than disguising a rejection as a run.
                if audit.get("baseline_resource_validation") == "in_progress":
                    audit["baseline_resource_validation"] = "failed"
                audit.update(baseline_preparation_status=("not_started" if audit["baseline_preparation_status"] == "not_started"
                    else "rejected"), fallback_rejection_reason=str(exc),
                    baseline_failure={"error_type": type(exc).__name__, "error_message": str(exc)})
                resume_game = True
                return None
            audit.update(executed_mode="baseline", fallback_triggered=True,
                fallback_reason=status, baseline_eligibility=True, fallback_decision="accepted",
                baseline_preparation_status="completed")
            baseline._contexts = self._contexts
            baseline._result_binding = self._result_binding
            baseline._attempt_binding = self._attempt_binding
            self._last_analysis = analysis
            return baseline._execute_baseline(request, analysis, validation_id, snapshot,
                prepared=(plan, admission), lifecycle=borrowed, fallback_audit=audit)
        except BaseException as exc:
            propagating_error = exc
            interrupted = not isinstance(exc, Exception)
            if audit.get("baseline_resource_validation") == "in_progress":
                audit["baseline_resource_validation"] = "interrupted" if interrupted else "failed"
            if audit["baseline_preparation_status"] != "completed":
                audit["baseline_preparation_status"] = "interrupted" if interrupted else "failed"
            audit.update(fallback_decision="interrupted" if interrupted else "failed",
                baseline_failure={"error_type": type(exc).__name__, "error_message": str(exc)})
            if borrowed is not None and not borrowed.terminalization_attempted:
                try:
                    borrowed.heartbeat.assert_owned()
                    borrowed.terminalization_attempted = True
                    mark_execution_failed(validation_id=validation_id, lease_token=borrowed.lease_token,
                        failure_details={**audit, "stage": "baseline_execution" if audit["baseline_preparation_status"] == "completed"
                            else "baseline_preparation", "error_type": type(exc).__name__, "error_message": str(exc)})
                    borrowed.failure_recorded = True
                except BaseException as recording_error:
                    # A lost lease/persistence error must not mask the original signal.
                    audit["failure_recording_error"] = {
                        "error_type": type(recording_error).__name__, "error_message": str(recording_error)}
            raise
        finally:
            # Ordinary rejection keeps Game's live lease until Game finalizes it.
            # All other paths are owned here, with no release/reacquisition gap.
            if borrowed is not None and not resume_game:
                try:
                    borrowed.heartbeat.stop()
                except BaseException as cleanup_error:
                    if propagating_error is None:
                        raise
                    audit["heartbeat_cleanup_error"] = {
                        "error_type": type(cleanup_error).__name__, "error_message": str(cleanup_error)}

    def _validate_game(self, request, analysis, validation_id):
        # One server-configured runtime/episode per run; request metadata cannot replace it.
        runtime = self._game_runtime
        journal = None
        heartbeat = None
        lease_token = None
        if self._persist_execution:
            connection = get_connection()
            try:
                create_validation_record(
                    validation_id=validation_id,
                    question_id=request.question_id,
                    question=request.question,
                    generated_answer=request.answer,
                    context=request.context,
                    session_id=request.session_id,
                    connection=connection,
                )
                begin_validation(
                    validation_id=validation_id,
                    execution_mode="game",
                    request_payload={
                        "question": request.question,
                        "answer": request.answer,
                        "context": request.context,
                        "question_id": request.question_id,
                        "session_id": request.session_id,
                    },
                    connection=connection,
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()
            try:
                mark_execution_ready(
                    validation_id=validation_id,
                    plan_payload={"phase": "game_route_resolution"},
                    analysis_snapshot={"domain": analysis.domain,
                                       "difficulty": analysis.difficulty},
                )
                running = mark_execution_running(
                    validation_id=validation_id,
                    worker_id=f"worker-{uuid4()}",
                )
                lease_token = running["lease_token"]
                heartbeat = ExecutionLeaseHeartbeat(
                    validation_id=validation_id, lease_token=lease_token
                ).start()
                journal = _GameExecutionJournal(validation_id, lease_token, heartbeat)
            except Exception as exc:
                mark_execution_failed(
                    validation_id=validation_id, lease_token=lease_token,
                    failure_details={"error_type": type(exc).__name__,
                                     "error_message": str(exc) or type(exc).__name__,
                                     "stage": "game_journal_start"},
                )
                raise
        observer = _GameExecutionObserver(journal)
        try:
            run = runtime.run(self._verifier_selector, analysis, request,
                              validation_id, execution_journal=observer)
        except Exception as exc:
            if journal is not None:
                try:
                    failure_audit = self._fallback_decision_audit({
                        "selection_status": "exception",
                        "selection_reasons": [str(exc) or type(exc).__name__]}, observer.started)
                    failure_audit.update(
                        game_failure_stage="execution" if observer.started else "runtime_before_dispatch",
                        fallback_rejection_reason="game_execution_started" if observer.started else "game_failure_not_eligible")
                    mark_execution_failed(
                        validation_id=validation_id, lease_token=lease_token,
                        failure_details={**failure_audit, "error_type": type(exc).__name__,
                                         "error_message": str(exc) or type(exc).__name__,
                                     "stage": "game_execution",
                                     "requested_mode": "game", "executed_mode": "game",
                                     "fallback_triggered": False,
                                     "game_verifier_execution_started": observer.started},
                    )
                finally:
                    heartbeat.stop()
            raise
        summary = json.loads(json.dumps(run.summary, allow_nan=False))
        fallback_audit = self._fallback_decision_audit(summary, observer.started)
        if not observer.started:
            response = self._try_baseline_fallback(request, validation_id, summary,
                fallback_audit, lifecycle=(lease_token, heartbeat) if journal is not None else None)
            if response is not None:
                return response
        else:
            fallback_audit["fallback_rejection_reason"] = "game_execution_started"
        summary.update(fallback_audit)
        summary = json.loads(json.dumps(summary, allow_nan=False))
        run_results = getattr(run, "results", None)
        if run_results is None:
            # Component runs carry their native per-obligation reports in the
            # router audit. Preserve those reports for the API/database path;
            # do not aggregate them again as a flat baseline vote.
            run_results = tuple(
                VerificationResult.model_validate(attempt["report"])
                for attempt in summary.get("attempts", ())
                if isinstance(attempt, dict) and isinstance(attempt.get("report"), dict)
            )
        results = list(run_results)
        if results:
            metadata = dict(results[-1].metadata or {})
            if RUN_SUMMARY_KEY in metadata:
                raise ValueError(f"reserved metadata key {RUN_SUMMARY_KEY!r} already exists")
            metadata[RUN_SUMMARY_KEY] = deepcopy(summary)
            results[-1] = results[-1].model_copy(update={"metadata": metadata})
        detail = getattr(run, "detail", None)
        self._contexts[validation_id] = ValidationContext(validation_id, analysis.domain,
            _detach_results(results), detail, deepcopy(summary))
        for result in results:
            self._result_binding[id(result)] = (result, validation_id)
        response = ValidationResponse(results=results, final_status=run.public_status,
            final_score=None if detail is None else detail.score,
            signed_score=None if detail is None else detail.raw_score,
            validation_id=validation_id, domain=analysis.domain, session_id=request.session_id,
            difficulty=analysis.difficulty, selected_verifiers=summary.get("team", []),
            early_stop_reason=summary.get("termination", "game_selection_failure"),
            uncertainty_reasons=(
                ["decision_uncertain"]
                if run.public_status == "uncertain"
                else []
            ),
            execution_audit=deepcopy(summary))
        if journal is not None:
            try:
                heartbeat.assert_owned()
                # Journal completion precedes API audit/output persistence by design.
                mark_execution_completed(
                    validation_id=validation_id,
                    final_response=response.model_dump(mode="json"),
                    lease_token=lease_token,
                )
                events = summary.get("attempts", [])
                attempt_by_identity = {}
                for event in events:
                    attempt_id = event.get("journal_attempt_id")
                    if not attempt_id:
                        continue
                    key = (event.get("verifier_name"), event.get("validation_id"),
                           event.get("component_id"), event.get("binding_id"))
                    attempt_by_identity[key] = attempt_id
                attempt_ids_by_name = {}
                for event in events:
                    if event.get("journal_attempt_id"):
                        attempt_ids_by_name.setdefault(event.get("verifier_name"), []).append(
                            event["journal_attempt_id"]
                        )
                for result in response.results:
                    metadata = result.metadata or {}
                    key = (result.verifier_name, metadata.get("validation_id"),
                           metadata.get("component_id"), metadata.get("binding_id"))
                    attempt_id = attempt_by_identity.get(key)
                    if attempt_id is None:
                        candidates = attempt_ids_by_name.get(result.verifier_name, [])
                        if len(candidates) == 1:
                            attempt_id = candidates[0]
                    if attempt_id:
                        self._attempt_binding[id(result)] = (result, attempt_id)
            except Exception as exc:
                mark_execution_failed(
                    validation_id=validation_id, lease_token=lease_token,
                    failure_details={**fallback_audit, "error_type": type(exc).__name__,
                                     "error_message": str(exc) or type(exc).__name__,
                                     "stage": "game_journal_completion"},
                )
                raise
            finally:
                heartbeat.stop()
        return response

    def validation_context(self, validation_id: str) -> ValidationContext:
        """Return a detached copy of one validation's domain and results."""
        context = self._contexts.get(validation_id)
        if context is None:
            raise ValueError(f"unknown validation {validation_id!r}")
        return ValidationContext(
            validation_id=context.validation_id,
            domain=context.domain,
            results=_detach_results(context.results),
            decision=context.decision,
            run_summary=deepcopy(context.run_summary),
        )

    def record_ground_truth(
        self,
        results: list[VerificationResult],
        answer_is_correct: bool,
        domain: str | None = None,
        *,
        validation_id: str | None = None,
        source: str = "external_feedback",
    ) -> int:
        """Update reputation from a label received after validation.

        ``answer_is_correct`` has to be the external boolean label. This
        method does not read ``final_status``. ``validation_id`` selects the
        stored run and is the preferred path. Omitting the id matches a
        result only when that same object is still retained from ``validate``.
        A slot whose stored object is not this one does not match, even when
        the votes are equal. A newly built list is not that run. An explicit
        domain with no bound result objects uses the unscoped update, which
        has no replay protection. Learning always uses the stored snapshot,
        and only when the supplied votes still match it. Returns the number
        of observations applied. A replay returns 0, but retries pending saves.
        ``source`` is metadata, not authentication. Changing it for a recorded
        validation conflicts under the manager's existing identity policy.
        """
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source must be a non-blank string")
        with self._feedback_lock:
            return self._record_ground_truth_locked(
                results, answer_is_correct, domain,
                validation_id=validation_id, source=source,
            )

    def record_persisted_ground_truth(
        self,
        validation_id: str,
        answer_is_correct: bool,
        source: str = "ground_truth",
    ) -> int:
        """Apply feedback using validation and verifier results stored in PostgreSQL."""

        if not isinstance(validation_id, str) or not validation_id.strip():
            raise ValueError("validation_id must be provided.")

        with self._feedback_lock:
            validation = get_validation(validation_id)

            if validation is None:
                raise ValueError(f"Unknown validation: {validation_id}")

            domain = validation.get("domain")
            if not domain:
                raise ValueError("Persisted validation has no domain.")

            stored_results = get_verifier_outputs(validation_id)

            if not stored_results:
                raise ValueError(
                    "No persisted verifier outputs found for this validation."
                )

            results = tuple(
                VerificationResult(
                    verifier_name=row["verifier_name"],
                    score=row["score"],
                    passed=row["passed"],
                    reasoning=row["reasoning"],
                    metadata=row["metadata"] or {},
                )
                for row in stored_results
            )

            previous_state = self._reputation_manager.export_state()

            receipt = self._reputation_manager.record_feedback(
                FeedbackEvent(
                    validation_id=validation_id,
                    domain=domain,
                    answer_is_correct=answer_is_correct,
                    results=results,
                    source=source,
                )
            )

            if receipt.applied:
                state = self._reputation_manager.export_state()

                try:
                    save_reputation_state_and_rows(state)
                except Exception:
                    self._reputation_manager.restore_state(previous_state)
                    raise

                self._pending_posterior_pairs.update(
                    (result.verifier_name, domain)
                    for result in results
                    if not is_abstention(result)
                )

            self._flush_pending_posteriors()

            return receipt.observations_applied

    def _record_ground_truth_locked(
        self,
        results: list[VerificationResult],
        answer_is_correct: bool,
        domain: str | None,
        *,
        validation_id: str | None,
        source: str,
    ) -> int:
        context = self._resolve_context(results, validation_id)
        if context is None:
            if domain is None:
                raise ValueError(
                    "domain or a bound validation is required. "
                    "Identical votes are not treated as a validation identity."
                )
            return self._reputation_manager.record_unscoped_ground_truth(
                domain,
                results,
                answer_is_correct,
                source=source,
            )
        if domain is not None and domain != context.domain:
            raise ValueError(
                "domain does not match the validation that produced these results"
            )
        if _learning_votes(results) != _learning_votes(context.results):
            raise ValueError("results do not match the bound validation")
        previous_state = self._reputation_manager.export_state()

        receipt = self._reputation_manager.record_feedback(
            FeedbackEvent(
                validation_id=context.validation_id,
                domain=context.domain,
                answer_is_correct=answer_is_correct,
                results=context.results,
                source=source,
            )
        )

        if receipt.applied:
            state = self._reputation_manager.export_state()

            try:
                save_reputation_state_and_rows(state)
            except Exception:
                self._reputation_manager.restore_state(previous_state)
                raise

            self._pending_posterior_pairs.update(
                (result.verifier_name, context.domain)
                for result in context.results
                if not is_abstention(result)
            )

        # Flush pending persistence work after successfully applying feedback.
        self._flush_pending_posteriors()
        return receipt.observations_applied

    def _flush_pending_posteriors(self) -> None:
        """Called under _feedback_lock; save latest counts, never old events.

        Each repository call upserts absolute alpha/beta in its own transaction.
        Only successful calls remove their pair. Other orchestrators, direct
        manager mutations, and other processes do not share this lock.
        """
        for name, domain in sorted(self._pending_posterior_pairs):
            stats = self._reputation_manager.statistics(name, domain)
            save_reputation(
                verifier_name=name, domain=domain,
                alpha=stats.alpha, beta=stats.beta,
            )
            self._pending_posterior_pairs.remove((name, domain))

    def _resolve_context(
        self,
        results: list[VerificationResult],
        validation_id: str | None,
    ) -> ValidationContext | None:
        if validation_id is not None:
            if not isinstance(validation_id, str) or validation_id.strip() == "":
                raise ValueError("validation_id must be a non-blank string")
            context = self._contexts.get(validation_id)
            if context is None:
                raise ValueError(f"unknown validation {validation_id!r}")
            return context
        if not results:
            return None
        bound: list[str] = []
        unbound = False
        for result in results:
            found = self._bound_validation_id(result)
            if found is None:
                unbound = True
            else:
                bound.append(found)
        if unbound and bound:
            raise ValueError(
                "results mix outputs from a stored validation with unbound results"
            )
        if unbound:
            return None
        identities = set(bound)
        if len(identities) != 1:
            raise ValueError(
                "results come from more than one validation. Pass validation_id."
            )
        return self._contexts[bound[0]]

    def _bound_validation_id(self, result: VerificationResult) -> str | None:
        """Return a validation id only when ``result`` is the retained object."""
        slot = self._result_binding.get(id(result))
        if slot is None:
            return None
        stored, validation_id = slot
        if stored is not result:
            return None
        return validation_id

    def get_attempt_id_for_result(
        self,
        result: VerificationResult,
    ) -> str | None:
        slot = self._attempt_binding.get(id(result))

        if slot is None:
            return None

        stored_result, attempt_id = slot

        if stored_result is not result:
            return None

        return attempt_id


def _detach_results(
    results: list[VerificationResult] | tuple[VerificationResult, ...],
) -> tuple[VerificationResult, ...]:
    """Deep-copy verifier outputs so later mutation cannot change the snapshot."""
    return tuple(result.model_copy(deep=True) for result in results)


def _learning_votes(
    results: list[VerificationResult] | tuple[VerificationResult, ...],
) -> tuple[tuple[str, bool, bool], ...]:
    return tuple(
        (result.verifier_name, is_abstention(result), result.passed) for result in results
    )


def _annotate(
    result: VerificationResult,
    *,
    abstained_before: list[str],
    abstention: bool,
) -> VerificationResult:
    """Attach a visible note about how this result was used. Verifier fields stay."""
    metadata = dict(result.metadata or {})
    if abstention:
        metadata["pipeline_role"] = "abstention"
        metadata["pipeline_note"] = (
            f"{result.verifier_name} abstained ({_abstention_reason(result)}). "
            "This result is not a pass or a reject, and it does not trigger early stopping. "
            "Another verifier is consulted when one is still available."
        )
    else:
        metadata["pipeline_role"] = "vote"
        confidence = vote_confidence(result)
        consulted = ""
        if abstained_before:
            consulted = (
                "Consulted after "
                + ", ".join(abstained_before)
                + " abstained. "
            )
        rule = metadata.get("rule")
        if (
            result.verifier_name == "rule"
            and isinstance(rule, str)
            and rule != "unsupported"
        ):
            scale = (
                f"Supported rule '{rule}' is deterministic, so the decision uses "
                f"confidence {confidence:.0f} rather than the stored score {result.score}."
            )
        else:
            scale = (
                f"The verifier score {result.score} is used as confidence {confidence:.4f} "
                "in this pass/reject vote."
            )
        side = "pass" if result.passed else "reject"
        metadata["pipeline_note"] = f"{consulted}Counted {result.verifier_name} as a {side} vote. {scale}"
    return result.model_copy(update={"metadata": metadata})


def _abstention_reason(result: VerificationResult) -> str:
    metadata = result.metadata or {}
    if result.verifier_name == "rule" and metadata.get("rule") == "unsupported":
        return "no supported rule matched the question"
    if result.verifier_name == "semantic":
        return "no reference context"
    if result.verifier_name == "evidence":
        label = metadata.get("nli_label")
        if isinstance(label, str) and label.lower() == "neutral":
            return "retrieved evidence was neutral, not a contradiction"
        return "no evidence was retrieved"
    if result.verifier_name == "confidence":
        if confidence_judgment_tie(result):
            return "the highest judgment counts were tied"
        return "no verification judgments"
    return "the verifier did not cast a vote"


RUN_SUMMARY_KEY = "multi_agent_verification.execution"


def _track_coverage(coverage: dict, result: VerificationResult) -> None:
    """Track declared candidates and qualifying outputs, never checker names.

    Runtime availability means that this request returned a result from a
    declared or output-qualified candidate. Abstention still cannot cover a
    requirement, and unattempted candidates are never observed available.
    """
    qualified = _factual_capabilities(result)
    for capability, row in coverage.items():
        if result.verifier_name not in row["planned_candidates"] and capability not in qualified:
            continue
        row["runtime_available"].append(result.verifier_name)
        row["available"] = True
        if result.verifier_name in row["unattempted"]:
            row["unattempted"].remove(result.verifier_name)
        if not row["achieved_contract"]:
            # A directional vote is not a certificate for semantic/consistency,
            # arbitrary logic, or an unrecognized requirement.
            row["attempts"].append({"verifier": result.verifier_name, "state": "no_achieved_contract"})
            continue
        state = ("directional" if capability in qualified else
                 "abstained" if is_abstention(result) else
                 "zero_confidence" if vote_confidence(result) == 0 else "unproven")
        row["attempts"].append({"verifier": result.verifier_name, "state": state})
        if capability in qualified:
            row["directional"].append(result.verifier_name)
