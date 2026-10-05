"""Offline benchmark runner.

Compares three procedures on labeled examples the caller supplies:

- adaptive: question analyzer, reputation selector, early stopping, and the
  reputation-weighted decision score (the orchestrator)
- majority: every supplied verifier, unweighted pass/reject majority
- all_verifiers: every supplied verifier, no early stop, same decision score

Accuracy is correct non-abstentions over non-abstentions. Coverage is
non-abstentions over examples. Abstentions are "uncertain" and "unknown".
Verifier calls are ``verify`` invocations. Latency is wall time measured
around those calls. Cost-table estimates are not reported as latency.

Reputation, when updates are on, changes only after that example's
prediction and only from that example's boolean label. Abstentions are
not observations. Adaptive and all-verifiers keep separate reputation
tables. Majority ignores reputation. The all-verifiers path has no
validation id, so a repeated example is another observation.

This module does not ship a dataset and does not store a result. It does
not rank a winner. See docs/decision_formulas.md.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from app.analysis.question_analyzer import QuestionAnalyzer
from app.decision.decision_engine import DecisionEngine
from app.decision.early_termination import AdaptiveEarlyTermination
from app.models.schemas import ValidationRequest, VerificationResult
from app.orchestration.validation_orchestrator import ValidationOrchestrator
from app.reputation.reputation_manager import ReputationManager
from app.selection.verifier_selector import (
    DEFAULT_LAMBDA_COST,
    DEFAULT_LAMBDA_LATENCY,
    VerifierSelector,
)
from app.verifiers.base_verifier import BaseVerifier

DEFINITIONS = {
    "accuracy": (
        "n_correct / n_covered. None when nothing was covered. "
        "Abstentions are not counted as correct or incorrect."
    ),
    "coverage": "n_covered / n_examples. None when there are no examples.",
    "abstention": "A decision whose status is uncertain or unknown.",
    "verifier_calls": "Number of verify() calls.",
    "latency_ms": (
        "Wall time measured around verify() in this run, in milliseconds. "
        "Selector cost and latency estimates are not included."
    ),
}

_LABEL_KEYS = ("answer_is_correct", "label", "is_correct")


@dataclass(frozen=True)
class LabeledExample:
    """One question, one answer, and an external correctness label."""

    question: str
    answer: str
    answer_is_correct: bool
    context: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.question, str) or not isinstance(self.answer, str):
            raise TypeError("question and answer must be strings")
        if not isinstance(self.answer_is_correct, bool):
            raise TypeError(
                "answer_is_correct must be a boolean ground-truth label, not a status string"
            )


@dataclass
class MethodReport:
    """Counts from one method on one run. Rates are None when undefined."""

    method: str
    n_examples: int
    n_covered: int
    n_abstentions: int
    n_correct: int
    n_incorrect: int
    accuracy: float | None
    coverage: float | None
    verifier_calls: int
    mean_verifier_calls: float | None
    latency_ms_total: float
    mean_latency_ms: float | None
    reputation_updates: int
    uses_reputation: bool
    updates_reputation: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "n_examples": self.n_examples,
            "n_covered": self.n_covered,
            "n_abstentions": self.n_abstentions,
            "n_correct": self.n_correct,
            "n_incorrect": self.n_incorrect,
            "accuracy": self.accuracy,
            "coverage": self.coverage,
            "verifier_calls": self.verifier_calls,
            "mean_verifier_calls": self.mean_verifier_calls,
            "latency_ms_total": self.latency_ms_total,
            "mean_latency_ms": self.mean_latency_ms,
            "reputation_updates": self.reputation_updates,
            "uses_reputation": self.uses_reputation,
            "updates_reputation": self.updates_reputation,
        }


@dataclass
class BenchmarkReport:
    """Result of one comparison. Reputation objects are live state, not a score."""

    methods: tuple[MethodReport, ...]
    protocol: str
    adaptive_reputation: ReputationManager
    all_verifiers_reputation: ReputationManager

    def method(self, name: str) -> MethodReport:
        for item in self.methods:
            if item.method == name:
                return item
        raise KeyError(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "disclaimer": (
                "Computed only from the examples supplied to this run. "
                "No method is ranked as better, and no result is stored in the repository."
            ),
            "protocol": self.protocol,
            "definitions": dict(DEFINITIONS),
            "methods": [item.to_dict() for item in self.methods],
        }


class _TimedVerifier(BaseVerifier):
    """Records wall time around an existing verifier without changing its vote."""

    def __init__(self, inner: BaseVerifier, durations_ms: list[float]) -> None:
        self._inner = inner
        self._durations_ms = durations_ms

    @property
    def name(self) -> str:
        return self._inner.name

    def verify(
        self,
        question: str,
        answer: str,
        context: str | None = None,
    ) -> VerificationResult:
        started = time.perf_counter()
        try:
            return self._inner.verify(question, answer, context)
        finally:
            self._durations_ms.append((time.perf_counter() - started) * 1000.0)


def examples_from_records(records: Sequence[dict[str, Any]]) -> list[LabeledExample]:
    """Build examples from dictionaries. Exactly one boolean label key is required."""
    examples: list[LabeledExample] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise TypeError(f"record {index} must be an object")
        if "question" not in record or "answer" not in record:
            raise ValueError(f"record {index} needs question and answer")
        present = [key for key in _LABEL_KEYS if key in record and record[key] is not None]
        if len(present) != 1:
            raise ValueError(
                f"record {index} needs exactly one ground-truth label "
                f"among {', '.join(_LABEL_KEYS)}"
            )
        examples.append(
            LabeledExample(
                question=record["question"],
                answer=record["answer"],
                answer_is_correct=record[present[0]],
                context=record.get("context"),
            )
        )
    return examples


def load_labeled_jsonl(path: str | Path) -> list[LabeledExample]:
    """Load a JSONL file of labeled examples. Blank lines are skipped."""
    source = Path(path)
    records: list[dict[str, Any]] = []
    with source.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{source}:{line_number} is not valid JSON") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"{source}:{line_number} must be a JSON object")
            records.append(payload)
    return examples_from_records(records)


def _prediction(status: str) -> bool | None:
    if status == "passed":
        return True
    if status == "failed":
        return False
    return None


def _majority_status(results: Sequence[VerificationResult]) -> str:
    if not results:
        return "unknown"
    passes = sum(1 for result in results if result.passed)
    rejects = len(results) - passes
    if passes > rejects:
        return "passed"
    if rejects > passes:
        return "failed"
    return "uncertain"


def _empty_report(
    method: str,
    *,
    uses_reputation: bool,
    updates_reputation: bool,
) -> MethodReport:
    return MethodReport(
        method=method,
        n_examples=0,
        n_covered=0,
        n_abstentions=0,
        n_correct=0,
        n_incorrect=0,
        accuracy=None,
        coverage=None,
        verifier_calls=0,
        mean_verifier_calls=None,
        latency_ms_total=0.0,
        mean_latency_ms=None,
        reputation_updates=0,
        uses_reputation=uses_reputation,
        updates_reputation=updates_reputation,
    )


def _finish(
    method: str,
    *,
    n_examples: int,
    n_correct: int,
    n_incorrect: int,
    n_abstentions: int,
    verifier_calls: int,
    durations_ms: Sequence[float],
    reputation_updates: int,
    uses_reputation: bool,
    updates_reputation: bool,
) -> MethodReport:
    n_covered = n_correct + n_incorrect
    if n_covered + n_abstentions != n_examples:
        raise RuntimeError(f"{method} coverage accounting failed")
    if n_examples == 0:
        coverage = None
        accuracy = None
        mean_calls = None
    else:
        coverage = n_covered / n_examples
        accuracy = (n_correct / n_covered) if n_covered else None
        mean_calls = verifier_calls / n_examples
    total_latency = round(sum(durations_ms), 6)
    mean_latency = round(total_latency / verifier_calls, 6) if verifier_calls else None
    return MethodReport(
        method=method,
        n_examples=n_examples,
        n_covered=n_covered,
        n_abstentions=n_abstentions,
        n_correct=n_correct,
        n_incorrect=n_incorrect,
        accuracy=accuracy,
        coverage=coverage,
        verifier_calls=verifier_calls,
        mean_verifier_calls=mean_calls,
        latency_ms_total=total_latency,
        mean_latency_ms=mean_latency,
        reputation_updates=reputation_updates,
        uses_reputation=uses_reputation,
        updates_reputation=updates_reputation,
    )


def _check_examples(examples: Sequence[LabeledExample]) -> list[LabeledExample]:
    if isinstance(examples, (str, bytes)):
        raise TypeError("examples must be a sequence of LabeledExample")
    checked: list[LabeledExample] = []
    for index, example in enumerate(examples):
        if not isinstance(example, LabeledExample):
            raise TypeError(f"example {index} must be a LabeledExample")
        checked.append(example)
    return checked


def _tally(status: str, label: bool, buckets: dict[str, int]) -> None:
    prediction = _prediction(status)
    if prediction is None:
        buckets["abstentions"] += 1
    elif prediction == label:
        buckets["correct"] += 1
    else:
        buckets["incorrect"] += 1


def run_benchmark(
    examples: Sequence[LabeledExample],
    *,
    verifiers: Sequence[BaseVerifier] | None = None,
    analyzer: QuestionAnalyzer | None = None,
    update_reputation: bool = True,
    lambda_cost: float = DEFAULT_LAMBDA_COST,
    lambda_latency: float = DEFAULT_LAMBDA_LATENCY,
    verifier_profiles: dict[str, dict[str, float]] | None = None,
    difficulty_range: dict[str, tuple[int, int]] | None = None,
    prior_alpha: float = ReputationManager.DEFAULT_ALPHA,
    prior_beta: float = ReputationManager.DEFAULT_BETA,
    early_termination: AdaptiveEarlyTermination | None = None,
) -> BenchmarkReport:
    """Run adaptive, majority, and all-verifiers on ``examples``.

    ``verifiers`` defaults to the four project verifiers. Pass instances to
    reuse a test double or a caller-supplied set. ``update_reputation``
    applies each example's label after that example's prediction.
    """
    checked = _check_examples(examples)
    pool = list(verifiers) if verifiers is not None else _default_verifiers()
    question_analyzer = analyzer or QuestionAnalyzer()
    stopper = early_termination or AdaptiveEarlyTermination()
    protocol = "sequential_ground_truth_feedback" if update_reputation else "frozen_prior"

    adaptive_report, adaptive_reputation = _run_adaptive(
        checked,
        pool,
        question_analyzer,
        stopper,
        update_reputation=update_reputation,
        lambda_cost=lambda_cost,
        lambda_latency=lambda_latency,
        verifier_profiles=verifier_profiles,
        difficulty_range=difficulty_range,
        prior_alpha=prior_alpha,
        prior_beta=prior_beta,
    )
    majority_report = _run_majority(checked, pool)
    all_report, all_reputation = _run_all_verifiers(
        checked,
        pool,
        question_analyzer,
        update_reputation=update_reputation,
        prior_alpha=prior_alpha,
        prior_beta=prior_beta,
    )
    return BenchmarkReport(
        methods=(adaptive_report, majority_report, all_report),
        protocol=protocol,
        adaptive_reputation=adaptive_reputation,
        all_verifiers_reputation=all_reputation,
    )


def _default_verifiers() -> list[BaseVerifier]:
    from app.verifiers.confidence_verifier import ConfidenceVerifier
    from app.verifiers.evidence_verifier import EvidenceVerifier
    from app.verifiers.rule_verifier import RuleVerifier
    from app.verifiers.semantic_verifier import SemanticVerifier

    return [
        SemanticVerifier(),
        EvidenceVerifier(
           corpus_path="data/test_evidence_corpus.json",
           index_path="data/test_evidence_index/faiss.index",
           chunks_path="data/test_evidence_index/chunks.json",
        ),
        RuleVerifier(),
        ConfidenceVerifier(),
    ]


def _run_adaptive(
    examples: Sequence[LabeledExample],
    verifiers: Sequence[BaseVerifier],
    analyzer: QuestionAnalyzer,
    stopper: AdaptiveEarlyTermination,
    *,
    update_reputation: bool,
    lambda_cost: float,
    lambda_latency: float,
    verifier_profiles: dict[str, dict[str, float]] | None,
    difficulty_range: dict[str, tuple[int, int]] | None,
    prior_alpha: float,
    prior_beta: float,
) -> tuple[MethodReport, ReputationManager]:
    if not examples:
        return (
            _empty_report("adaptive", uses_reputation=True, updates_reputation=update_reputation),
            ReputationManager(prior_alpha, prior_beta),
        )

    durations: list[float] = []
    wrapped = [_TimedVerifier(verifier, durations) for verifier in verifiers]
    reputation = ReputationManager(prior_alpha, prior_beta)
    selector = VerifierSelector(
        reputation_manager=reputation,
        lambda_cost=lambda_cost,
        lambda_latency=lambda_latency,
        verifier_profiles=verifier_profiles,
        difficulty_range=difficulty_range,
        verifiers=wrapped,
    )
    engine = DecisionEngine(reputation_manager=reputation)
    orchestrator = ValidationOrchestrator(
        question_analyzer=analyzer,
        verifier_selector=selector,
        decision_engine=engine,
        reputation_manager=reputation,
        early_termination=stopper,
    )
    buckets = {"correct": 0, "incorrect": 0, "abstentions": 0}
    updates = 0
    for example in examples:
        response = orchestrator.validate(
            ValidationRequest(
                question=example.question,
                answer=example.answer,
                context=example.context,
            )
        )
        _tally(response.final_status, example.answer_is_correct, buckets)
        if update_reputation:
            updates += orchestrator.record_ground_truth(
                response.results,
                example.answer_is_correct,
                validation_id=response.validation_id,
            )
    return (
        _finish(
            "adaptive",
            n_examples=len(examples),
            n_correct=buckets["correct"],
            n_incorrect=buckets["incorrect"],
            n_abstentions=buckets["abstentions"],
            verifier_calls=len(durations),
            durations_ms=durations,
            reputation_updates=updates,
            uses_reputation=True,
            updates_reputation=update_reputation,
        ),
        reputation,
    )


def _run_majority(
    examples: Sequence[LabeledExample],
    verifiers: Sequence[BaseVerifier],
) -> MethodReport:
    if not examples:
        return _empty_report("majority", uses_reputation=False, updates_reputation=False)
    durations: list[float] = []
    wrapped = [_TimedVerifier(verifier, durations) for verifier in verifiers]
    buckets = {"correct": 0, "incorrect": 0, "abstentions": 0}
    for example in examples:
        results = [
            verifier.verify(example.question, example.answer, example.context)
            for verifier in wrapped
        ]
        _tally(_majority_status(results), example.answer_is_correct, buckets)
    return _finish(
        "majority",
        n_examples=len(examples),
        n_correct=buckets["correct"],
        n_incorrect=buckets["incorrect"],
        n_abstentions=buckets["abstentions"],
        verifier_calls=len(durations),
        durations_ms=durations,
        reputation_updates=0,
        uses_reputation=False,
        updates_reputation=False,
    )


def _run_all_verifiers(
    examples: Sequence[LabeledExample],
    verifiers: Sequence[BaseVerifier],
    analyzer: QuestionAnalyzer,
    *,
    update_reputation: bool,
    prior_alpha: float,
    prior_beta: float,
) -> tuple[MethodReport, ReputationManager]:
    reputation = ReputationManager(prior_alpha, prior_beta)
    if not examples:
        return (
            _empty_report(
                "all_verifiers",
                uses_reputation=True,
                updates_reputation=update_reputation,
            ),
            reputation,
        )
    durations: list[float] = []
    wrapped = [_TimedVerifier(verifier, durations) for verifier in verifiers]
    engine = DecisionEngine(reputation_manager=reputation)
    buckets = {"correct": 0, "incorrect": 0, "abstentions": 0}
    updates = 0
    for example in examples:
        analysis = analyzer.analyze(example.question)
        results = [
            verifier.verify(example.question, example.answer, example.context)
            for verifier in wrapped
        ]
        status, _score = engine.decide(results, domain=analysis.domain)
        _tally(status, example.answer_is_correct, buckets)
        if update_reputation:
            updates += reputation.record_unscoped_ground_truth(
                analysis.domain,
                results,
                example.answer_is_correct,
            )
    return (
        _finish(
            "all_verifiers",
            n_examples=len(examples),
            n_correct=buckets["correct"],
            n_incorrect=buckets["incorrect"],
            n_abstentions=buckets["abstentions"],
            verifier_calls=len(durations),
            durations_ms=durations,
            reputation_updates=updates,
            uses_reputation=True,
            updates_reputation=update_reputation,
        ),
        reputation,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry. Requires a labeled JSONL file; it does not invent one."""
    parser = argparse.ArgumentParser(
        description=(
            "Compare adaptive selection, unweighted majority, and all verifiers "
            "on a labeled JSONL file. Prints measured counts only."
        )
    )
    parser.add_argument("--data", required=True, help="JSONL file of labeled examples")
    parser.add_argument(
        "--no-reputation-updates",
        action="store_true",
        help="Keep the cold-start prior for the whole run",
    )
    args = parser.parse_args(argv)
    report = run_benchmark(
        load_labeled_jsonl(args.data),
        update_reputation=not args.no_reputation_updates,
    )
    json.dump(report.to_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
