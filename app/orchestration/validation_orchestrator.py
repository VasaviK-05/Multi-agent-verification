"""Validation orchestrator — coordinates the validation pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from copy import deepcopy
from uuid import uuid4

from app.analysis.question_analyzer import QuestionAnalysis, QuestionAnalyzer
from app.decision.decision_engine import DecisionDetail, DecisionEngine
from app.evaluation.automatic_ground_truth import AutomaticGroundTruthEvaluator
from app.decision.early_termination import AdaptiveEarlyTermination
from app.decision.vote_normalization import (
    confidence_judgment_tie,
    is_abstention,
    vote_confidence,
)
from app.models.schemas import ValidationRequest, ValidationResponse, VerificationResult
from app.reputation.reputation_manager import FeedbackEvent, ReputationManager
from app.selection.verifier_selector import VerifierSelector


@dataclass(frozen=True)
class ValidationContext:
    """Identity and domain captured when a validation ran.

    Feedback uses this record. It does not read a later ``_last_analysis``.
    """

    validation_id: str
    domain: str
    results: tuple[VerificationResult, ...]
    decision: DecisionDetail
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
    ) -> None:
        self._question_analyzer = question_analyzer or QuestionAnalyzer()
        self._early_termination = early_termination or AdaptiveEarlyTermination()
        self._automatic_ground_truth = AutomaticGroundTruthEvaluator()
        self._last_analysis: QuestionAnalysis | None = None
        self._contexts: dict[str, ValidationContext] = {}
        # Strong refs to the result objects validate() returned. Lookup checks
        # identity with ``is``; the id is only a slot. Snapshots stay separate.
        self._result_binding: dict[int, tuple[VerificationResult, str]] = {}
        self._verifier_selector, self._decision_engine, self._reputation_manager = (
            self._assemble(verifier_selector, decision_engine, reputation_manager)
        )

    @staticmethod
    def _assemble(
        verifier_selector: VerifierSelector | None,
        decision_engine: DecisionEngine | None,
        reputation_manager: ReputationManager | None,
    ) -> tuple[VerifierSelector, DecisionEngine, ReputationManager]:
        if verifier_selector is None and decision_engine is None:
            shared = reputation_manager or ReputationManager()
            return (
                VerifierSelector(reputation_manager=shared),
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
                VerifierSelector(reputation_manager=shared),
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
        analysis = self._question_analyzer.analyze(request.question)
        self._last_analysis = analysis
        validation_id = str(uuid4())
        minimum = self._verifier_selector.minimum_count(analysis)
        if analysis.difficulty != "hard":
            minimum = max(2, minimum)
        names = [row.verifier_name for row in self._verifier_selector.explain_ranking(analysis)]
        required = set(analysis.verification_types or ()) & {"direct_fact", "arithmetic"}
        coverage = {
            capability: {
                "available": any(name in names for name in {
                    "evidence" if capability == "direct_fact" else "rule",
                    self._verifier_selector.type_mapping.get(capability),
                }),
                "unattempted": [name for name in names if name in {
                    "evidence" if capability == "direct_fact" else "rule",
                    self._verifier_selector.type_mapping.get(capability),
                }],
                "attempts": [], "directional": [],
            }
            for capability in sorted(required)
        }
        results: list[VerificationResult] = []
        abstained: list[str] = []
        detail = None
        reason = "candidate_exhaustion"
        last_assessment = None
        for verifier in self._verifier_selector.iter_ranked(analysis):
            raw = verifier.verify(request.question, request.answer, request.context)
            abstention = is_abstention(raw)
            annotated = _annotate(raw, abstained_before=list(abstained), abstention=abstention)
            results.append(annotated)
            if abstention:
                abstained.append(raw.verifier_name)
            _track_coverage(coverage, raw, self._verifier_selector.type_mapping)
            assessment = self._early_termination.should_terminate(
                results, analysis, minimum, decision_engine=self._decision_engine,
            )
            last_assessment = assessment["reason"]
            if (analysis.difficulty != "hard" and assessment["terminate"]
                    and all(row["directional"] for row in coverage.values())):
                detail = assessment["decision"]
                reason = "approved_early_stop"
                break
        if detail is None:
            detail = self._decision_engine.decide_detailed(results, domain=analysis.domain)
        contributors = self._early_termination.contributor_count(detail, results)
        missing = [key for key, row in coverage.items() if not row["directional"]]
        final_status = detail.status
        if contributors < minimum or missing:
            final_status = "uncertain"
        final_score = detail.score
        summary = {
            "termination": reason, "last_stopping_assessment": last_assessment,
            "minimum_contributors": minimum, "contributors": contributors,
            "missing_coverage": missing, "coverage": coverage,
            "numerical_decision": asdict(detail), "public_status": final_status,
        }
        if results:
            metadata = dict(results[-1].metadata or {})
            if RUN_SUMMARY_KEY in metadata:
                raise ValueError(f"reserved metadata key {RUN_SUMMARY_KEY!r} already exists")
            metadata[RUN_SUMMARY_KEY] = deepcopy(summary)
            results[-1] = results[-1].model_copy(update={"metadata": metadata})

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

        return ValidationResponse(
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
            signed_score=signed_score,
        )

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
        of observations applied. A replay returns 0.
        """
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
            )
        if domain is not None and domain != context.domain:
            raise ValueError(
                "domain does not match the validation that produced these results"
            )
        if _learning_votes(results) != _learning_votes(context.results):
            raise ValueError("results do not match the bound validation")
        receipt = self._reputation_manager.record_feedback(
            FeedbackEvent(
                validation_id=context.validation_id,
                domain=context.domain,
                answer_is_correct=answer_is_correct,
                results=context.results,
            )
        )
        return receipt.observations_applied

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
ARITHMETIC_RULES = frozenset({
    "arithmetic_addition", "arithmetic_subtraction",
    "arithmetic_multiplication", "arithmetic_division",
})


def _factual_capabilities(result: VerificationResult) -> set[str]:
    """Recognize current factual output contracts, regardless of checker name.

    Rule expected/actual fields are optional on legitimate invalid-answer
    rejections. Evidence requires assessed claims and matching evidence rows;
    an identity or bare decision is never a coverage certificate.
    """
    metadata = result.metadata or {}
    if is_abstention(result) or vote_confidence(result) == 0:
        return set()
    decision = metadata.get("decision")
    if decision not in {"SUPPORT", "REJECT"}:
        return set()
    capabilities = set()
    rule = metadata.get("rule")
    if (metadata.get("rule_kind") == "factual"
            and isinstance(rule, str) and rule in ARITHMETIC_RULES):
        capabilities.add("arithmetic")
    label = "entailment" if decision == "SUPPORT" else "contradiction"
    rows = metadata.get("supporting" if result.passed else "contradicting")
    opposite = metadata.get("contradicting" if result.passed else "supporting")
    claims = metadata.get("claim_decisions")
    if (metadata.get("nli_label") == label and metadata.get("unsure_reason") is None
            and isinstance(rows, list) and rows
            and any(isinstance(row, dict) and row.get("nli_label") == label for row in rows)
            and isinstance(claims, list) and claims):
        # Support requires every claim; rejection needs one decisive claim.
        directions = [c.get("decision") for c in claims if isinstance(c, dict)]
        if ((decision == "SUPPORT" and len(directions) == len(claims)
                and all(d == "SUPPORT" for d in directions) and not opposite)
                or (decision == "REJECT" and "REJECT" in directions)):
            capabilities.add("direct_fact")
    return capabilities


def _track_coverage(coverage: dict, result: VerificationResult, mapping: dict) -> None:
    qualified = _factual_capabilities(result)
    metadata = result.metadata or {}
    rule = metadata.get("rule")
    for capability, row in coverage.items():
        candidate = (result.verifier_name in {
            "evidence" if capability == "direct_fact" else "rule", mapping.get(capability),
        } or capability in qualified
            or (capability == "direct_fact" and "claim_decisions" in metadata)
            or (capability == "arithmetic" and isinstance(rule, str)
                and rule in ARITHMETIC_RULES))
        if not candidate:
            continue
        row["available"] = True
        if result.verifier_name in row["unattempted"]:
            row["unattempted"].remove(result.verifier_name)
        state = ("directional" if capability in qualified else
                 "abstained" if is_abstention(result) else
                 "zero_confidence" if vote_confidence(result) == 0 else "unproven")
        row["attempts"].append({"verifier": result.verifier_name, "state": state})
        if capability in qualified:
            row["directional"].append(result.verifier_name)
