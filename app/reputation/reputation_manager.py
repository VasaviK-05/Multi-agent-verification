"""Domain-aware verifier reputation.

Each verifier × domain pair has its own Beta–Bernoulli counts. The reported
reputation is the posterior mean

    alpha = prior_alpha + successes
    beta = prior_beta + failures
    R = alpha / (alpha + beta)

With the default prior alpha = beta = 1 this is Laplace's rule of succession:
R = (successes + 1) / (successes + failures + 2). Successes and failures are
stored as integers. The observation count is their sum. It is not recovered
by subtracting the prior from alpha and beta.

A verifier succeeds when its own pass/reject vote matches an external boolean
label. Rejecting an incorrect answer is a success. Abstentions and verifiers
that did not run add no observation. ``validate`` does not call this module.
The decision status, a consensus, a confidence score, and a reference-answer
string are not labels.

The posterior variance is

    alpha * beta / ((alpha + beta)^2 * (alpha + beta + 1))

Variance and R are not calibrated answer confidence.

``update_reputation`` and ``update_from_ground_truth`` have no validation
identity. A repeated call is another observation. ``record_feedback`` binds
one external label to a validation id. Delivering that same feedback again
does nothing. A different label or vote list for an id that is already
recorded is rejected and does not change state. Replacing a stored label
needs a future correction workflow; this module does not provide one.

``source`` is caller-supplied metadata. It is not authentication and it is
not proof that the boolean is true. The legacy methods still reject a source
other than ``ground_truth`` so a prediction tag is not stored as evidence.
That check does not establish that a ``ground_truth`` tag came from a
trusted party.

The prior and the +1 step are UNCALIBRATED. This is not an EWMA, a decay,
or a confidence-weighted pseudo-count. See docs/decision_formulas.md and
docs/reputation_integration.md.
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass
from typing import Mapping, Sequence

from app.models.schemas import VerificationResult

_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ReputationStatistics:
    """Detached counts for one verifier and domain.

    ``posterior_mean`` and ``posterior_variance`` describe the Beta–Bernoulli
    belief about that verifier in that domain. They are not the probability
    that an answer is correct.
    """

    verifier_name: str
    domain: str
    alpha: float
    beta: float
    successes: int
    failures: int
    observation_count: int
    posterior_mean: float
    posterior_variance: float
    cold_start: bool


@dataclass(frozen=True)
class FeedbackReceipt:
    """Result of one feedback delivery. A replay has ``applied`` false."""

    validation_id: str
    applied: bool
    observations_applied: int


@dataclass(frozen=True)
class FeedbackEvent:
    """One external label for one validation run.

    ``results`` are the verifiers that actually ran. ``source`` is metadata.
    """

    validation_id: str
    domain: str
    answer_is_correct: bool
    results: tuple[VerificationResult, ...]
    source: str = "ground_truth"


@dataclass(frozen=True)
class _Vote:
    verifier_name: str
    passed: bool
    abstained: bool


@dataclass(frozen=True)
class _FeedbackRecord:
    validation_id: str
    domain: str
    answer_is_correct: bool
    source: str
    votes: tuple[_Vote, ...]


@dataclass
class _Counts:
    successes: int = 0
    failures: int = 0


class ReputationManager:
    """Maintains a separate Beta reputation for each verifier and domain."""

    # UNCALIBRATED uniform prior. R = 1 / (1 + 1) = 0.5 until a label arrives.
    DEFAULT_ALPHA = 1.0
    DEFAULT_BETA = 1.0
    GROUND_TRUTH_SOURCE = "ground_truth"

    def __init__(
        self,
        prior_alpha: float = DEFAULT_ALPHA,
        prior_beta: float = DEFAULT_BETA,
    ) -> None:
        self._prior_alpha = _require_prior("prior_alpha", prior_alpha)
        self._prior_beta = _require_prior("prior_beta", prior_beta)
        _belief(self._prior_alpha, self._prior_beta)
        self._counts: dict[tuple[str, str], _Counts] = {}
        self._feedback: dict[str, _FeedbackRecord] = {}
        self._lock = threading.RLock()

    @property
    def prior_alpha(self) -> float:
        return self._prior_alpha

    @property
    def prior_beta(self) -> float:
        return self._prior_beta

    def observation_count(self, verifier_name: str, domain: str) -> int:
        """How many ground-truth votes have been applied to this pair.

        The prior itself is not an observation. Cold start is a count of 0.
        """
        _require_identifier("verifier_name", verifier_name)
        _require_identifier("domain", domain)
        with self._lock:
            counts = self._counts.get((verifier_name, domain))
            if counts is None:
                return 0
            return counts.successes + counts.failures

    def is_cold_start(self, verifier_name: str, domain: str) -> bool:
        """True when this pair still has only the prior, in this domain alone."""
        return self.observation_count(verifier_name, domain) == 0

    def get_reputation(self, verifier_name: str, domain: str) -> float:
        """Return R = alpha / (alpha + beta), rounded to 6 decimals.

        The default prior yields exactly 0.5. That value means "no labels
        yet" (or an even split of labels), not a measured accuracy and not
        the probability that an answer is correct. Selector and decision
        code read this rounded mean.
        """
        with self._lock:
            stats = self._statistics_unlocked(verifier_name, domain)
        return round(stats.posterior_mean, 6)

    def statistics(self, verifier_name: str, domain: str) -> ReputationStatistics:
        """Return a detached view. The manager's tables are not exposed.

        The read is atomic with updates in this process. It is not a
        multi-process or database transaction.
        """
        with self._lock:
            return self._statistics_unlocked(verifier_name, domain)

    def statistics_batch(
        self,
        pairs: Sequence[tuple[str, str]],
    ) -> tuple[ReputationStatistics, ...]:
        """Return detached statistics for each pair under one lock acquisition.

        The result follows ``pairs`` in order. This read does not change
        counts or feedback. It is atomic in this process, not a
        multi-process or database transaction.
        """
        if isinstance(pairs, (str, bytes)) or not isinstance(pairs, Sequence):
            raise TypeError("pairs must be a sequence of (verifier_name, domain) pairs")
        requested: list[tuple[str, str]] = []
        for item in pairs:
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError(
                    "each statistics request must be a (verifier_name, domain) pair"
                )
            requested.append(item)
        with self._lock:
            return tuple(
                self._statistics_unlocked(verifier_name, domain)
                for verifier_name, domain in requested
            )

    def _statistics_unlocked(self, verifier_name: str, domain: str) -> ReputationStatistics:
        _require_identifier("verifier_name", verifier_name)
        _require_identifier("domain", domain)
        counts = self._counts.get((verifier_name, domain), _Counts())
        alpha, beta, mean, variance = _components(
            self._prior_alpha,
            self._prior_beta,
            counts.successes,
            counts.failures,
        )
        observations = counts.successes + counts.failures
        return ReputationStatistics(
            verifier_name=verifier_name,
            domain=domain,
            alpha=alpha,
            beta=beta,
            successes=counts.successes,
            failures=counts.failures,
            observation_count=observations,
            posterior_mean=mean,
            posterior_variance=variance,
            cold_start=observations == 0,
        )

    def update_reputation(
        self,
        verifier_name: str,
        domain: str,
        agreed_with_ground_truth: bool,
        *,
        source: str = GROUND_TRUTH_SOURCE,
    ) -> None:
        """Apply one Bernoulli observation with no validation identity.

        A second call for the same vote is a second observation. This method
        cannot reject a duplicate delivery. ``source`` must be the string
        ``ground_truth``; any other tag is refused. That refusal is not
        authentication of the label.
        """
        _require_identifier("verifier_name", verifier_name)
        _require_identifier("domain", domain)
        if not isinstance(source, str) or source != self.GROUND_TRUTH_SOURCE:
            raise ValueError(
                "Reputation updates require source='ground_truth'. "
                "The source string is caller metadata, not authentication, "
                "and a prediction tag is not evidence."
            )
        if not isinstance(agreed_with_ground_truth, bool):
            raise TypeError(
                "agreed_with_ground_truth must be a boolean. "
                "Pass the comparison with an external label, not a status string."
            )
        with self._lock:
            staged = _with_observation(
                self._counts,
                verifier_name,
                domain,
                agreed_with_ground_truth,
            )
            _require_readable_counts(self._prior_alpha, self._prior_beta, staged)
            self._counts = staged

    def update_from_ground_truth(
        self,
        verifier_name: str,
        domain: str,
        verifier_passed: bool,
        answer_is_correct: bool,
    ) -> None:
        """Score one verifier vote against a label, with no event identity.

        Repeated calls each add an observation. The verifier was correct
        when its pass/reject vote matches the label.
        """
        _require_identifier("verifier_name", verifier_name)
        _require_identifier("domain", domain)
        if not isinstance(verifier_passed, bool) or not isinstance(answer_is_correct, bool):
            raise TypeError(
                "verifier_passed and answer_is_correct must be booleans. "
                "A status string such as 'passed' is not a ground-truth label."
            )
        self.update_reputation(
            verifier_name,
            domain,
            verifier_passed == answer_is_correct,
            source=self.GROUND_TRUTH_SOURCE,
        )

    def record_unscoped_ground_truth(
        self,
        domain: str,
        results: Sequence[VerificationResult],
        answer_is_correct: bool,
    ) -> int:
        """Learn from executed results that have no validation identity.

        Abstentions are skipped. The whole list is checked before any count
        changes. If a later pair cannot be represented, no count from this
        call is stored. A later call with the same results is new evidence,
        because this path has nothing to recognize a replay. Returns the
        number of observations applied.
        """
        record = _normalize_feedback(
            validation_id="unscoped",
            domain=domain,
            results=results,
            answer_is_correct=answer_is_correct,
            source=self.GROUND_TRUTH_SOURCE,
        )
        with self._lock:
            staged = {
                key: _Counts(value.successes, value.failures)
                for key, value in self._counts.items()
            }
            applied = 0
            for vote in record.votes:
                if vote.abstained:
                    continue
                staged = _with_observation(
                    staged,
                    vote.verifier_name,
                    record.domain,
                    vote.passed == record.answer_is_correct,
                )
                applied += 1
            _require_readable_counts(self._prior_alpha, self._prior_beta, staged)
            self._counts = staged
            return applied

    def record_feedback(self, event: FeedbackEvent) -> FeedbackReceipt:
        """Learn from one labeled validation, or do nothing if it was already stored."""
        receipts = self.record_feedback_batch((event,))
        return receipts[0]

    def record_feedback_batch(
        self,
        events: Sequence[FeedbackEvent],
    ) -> tuple[FeedbackReceipt, ...]:
        """Validate every event, then apply the new ones.

        An invalid or conflicting later event leaves every count and every
        stored feedback record unchanged. A count that cannot be represented
        does the same, and does not store that batch's validation ids. An
        event that matches a stored record, or an earlier event in this
        batch, is a no-op. A different payload for an id that is already
        present is an error. This method does not replace a stored label.
        """
        if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
            raise TypeError("events must be a sequence of FeedbackEvent")
        with self._lock:
            normalized = tuple(_event_record(event) for event in events)
            receipts, counts, feedback = _plan_feedback(
                self._counts,
                self._feedback,
                normalized,
            )
            _require_readable_counts(self._prior_alpha, self._prior_beta, counts)
            self._counts = counts
            self._feedback = feedback
            return receipts

    def export_state(self) -> dict:
        """Return a JSON-ready copy of priors, counts, and feedback records.

        This is not a database write. The returned dict does not share
        objects with the manager. The copy is taken under the process lock.
        """
        with self._lock:
            return self._export_unlocked()

    def _export_unlocked(self) -> dict:
        pairs = [
            {
                "verifier_name": verifier_name,
                "domain": domain,
                "successes": counts.successes,
                "failures": counts.failures,
            }
            for (verifier_name, domain), counts in sorted(self._counts.items())
            if counts.successes or counts.failures
        ]
        feedback = [
            {
                "validation_id": record.validation_id,
                "domain": record.domain,
                "answer_is_correct": record.answer_is_correct,
                "source": record.source,
                "votes": [
                    {
                        "verifier_name": vote.verifier_name,
                        "passed": vote.passed,
                        "abstained": vote.abstained,
                    }
                    for vote in record.votes
                ],
            }
            for record in sorted(self._feedback.values(), key=lambda item: item.validation_id)
        ]
        return {
            "schema_version": _SCHEMA_VERSION,
            "prior_alpha": self._prior_alpha,
            "prior_beta": self._prior_beta,
            "pairs": pairs,
            "feedback": feedback,
        }

    def restore_state(self, payload: object) -> None:
        """Replace live state only after the whole payload is valid.

        A malformed, non-finite, or inconsistent payload raises and leaves
        the current priors, counts, and feedback records in place.
        """
        with self._lock:
            counts, feedback, prior_alpha, prior_beta = _parse_state(payload)
            self._prior_alpha = prior_alpha
            self._prior_beta = prior_beta
            self._counts = counts
            self._feedback = feedback


def _event_record(event: FeedbackEvent) -> _FeedbackRecord:
    if not isinstance(event, FeedbackEvent):
        raise TypeError("feedback event must be a FeedbackEvent")
    return _normalize_feedback(
        validation_id=event.validation_id,
        domain=event.domain,
        results=event.results,
        answer_is_correct=event.answer_is_correct,
        source=event.source,
    )


def _normalize_feedback(
    *,
    validation_id: str,
    domain: str,
    results: Sequence[VerificationResult],
    answer_is_correct: bool,
    source: str,
) -> _FeedbackRecord:
    _require_identifier("validation_id", validation_id)
    _require_identifier("domain", domain)
    if not isinstance(answer_is_correct, bool):
        raise TypeError(
            "answer_is_correct must be a boolean. "
            "A status string or a reference answer is not a label."
        )
    if not isinstance(source, str) or source.strip() == "":
        raise ValueError(
            "source must be a non-blank string. "
            "It records caller metadata and does not prove the label is true."
        )
    if not isinstance(results, Sequence) or isinstance(results, (str, bytes)):
        raise TypeError("results must be a sequence of verifier results")
    votes: list[_Vote] = []
    seen: dict[str, _Vote] = {}
    for result in results:
        if not isinstance(result, VerificationResult):
            raise TypeError("results must contain VerificationResult values")
        _require_identifier("verifier_name", result.verifier_name)
        if not isinstance(result.passed, bool):
            raise TypeError("verifier passed must be a boolean")
        # Imported here so loading ReputationManager does not load DecisionEngine.
        from app.decision.vote_normalization import is_abstention

        vote = _Vote(
            verifier_name=result.verifier_name,
            passed=result.passed,
            abstained=is_abstention(result),
        )
        previous = seen.get(vote.verifier_name)
        if previous is None:
            seen[vote.verifier_name] = vote
            votes.append(vote)
            continue
        if previous != vote:
            raise ValueError(
                f"conflicting duplicate verifier result for {vote.verifier_name!r}"
            )
    return _FeedbackRecord(
        validation_id=validation_id,
        domain=domain,
        answer_is_correct=answer_is_correct,
        source=source,
        votes=tuple(votes),
    )


def _plan_feedback(
    counts: Mapping[tuple[str, str], _Counts],
    feedback: Mapping[str, _FeedbackRecord],
    events: Sequence[_FeedbackRecord],
) -> tuple[tuple[FeedbackReceipt, ...], dict[tuple[str, str], _Counts], dict[str, _FeedbackRecord]]:
    """Build the next tables. The caller swaps them in only after this returns."""
    staged_feedback = dict(feedback)
    incoming: list[_FeedbackRecord] = []
    receipts: list[FeedbackReceipt] = []
    for record in events:
        stored = staged_feedback.get(record.validation_id)
        if stored is None:
            staged_feedback[record.validation_id] = record
            incoming.append(record)
            receipts.append(
                FeedbackReceipt(
                    validation_id=record.validation_id,
                    applied=True,
                    observations_applied=_informative_count(record),
                )
            )
            continue
        if stored != record:
            raise ValueError(
                f"conflicting feedback for validation {record.validation_id!r}. "
                "Label corrections require a future correction workflow."
            )
        receipts.append(
            FeedbackReceipt(
                validation_id=record.validation_id,
                applied=False,
                observations_applied=0,
            )
        )
    staged_counts = {
        key: _Counts(value.successes, value.failures) for key, value in counts.items()
    }
    for record in incoming:
        for vote in record.votes:
            if vote.abstained:
                continue
            pair = staged_counts.setdefault((vote.verifier_name, record.domain), _Counts())
            if vote.passed == record.answer_is_correct:
                pair.successes += 1
            else:
                pair.failures += 1
    return tuple(receipts), staged_counts, staged_feedback


def _informative_count(record: _FeedbackRecord) -> int:
    return sum(1 for vote in record.votes if not vote.abstained)


def _parse_state(
    payload: object,
) -> tuple[dict[tuple[str, str], _Counts], dict[str, _FeedbackRecord], float, float]:
    if not isinstance(payload, dict):
        raise ValueError("reputation state must be an object")
    expected = {"schema_version", "prior_alpha", "prior_beta", "pairs", "feedback"}
    if set(payload) != expected:
        raise ValueError("reputation state keys are incomplete or unrecognized")
    version = payload["schema_version"]
    if isinstance(version, bool) or type(version) is not int or version != _SCHEMA_VERSION:
        raise ValueError("schema_version must be the integer 1")
    prior_alpha = _require_prior("prior_alpha", payload["prior_alpha"])
    prior_beta = _require_prior("prior_beta", payload["prior_beta"])
    _belief(prior_alpha, prior_beta)
    counts = _parse_pairs(payload["pairs"])
    feedback = _parse_feedback(payload["feedback"])
    _require_feedback_within_counts(counts, feedback)
    for counts_row in counts.values():
        _components(prior_alpha, prior_beta, counts_row.successes, counts_row.failures)
    return counts, feedback, prior_alpha, prior_beta


def _parse_pairs(value: object) -> dict[tuple[str, str], _Counts]:
    if not isinstance(value, list):
        raise ValueError("reputation pairs must be a list")
    counts: dict[tuple[str, str], _Counts] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {
            "verifier_name",
            "domain",
            "successes",
            "failures",
        }:
            raise ValueError("reputation pair fields are incomplete or unrecognized")
        verifier_name = item["verifier_name"]
        domain = item["domain"]
        _require_identifier("verifier_name", verifier_name)
        _require_identifier("domain", domain)
        key = (verifier_name, domain)
        if key in counts:
            raise ValueError("reputation state repeats a verifier and domain")
        counts[key] = _Counts(
            successes=_require_count("successes", item["successes"]),
            failures=_require_count("failures", item["failures"]),
        )
    return counts


def _parse_feedback(value: object) -> dict[str, _FeedbackRecord]:
    if not isinstance(value, list):
        raise ValueError("reputation feedback must be a list")
    feedback: dict[str, _FeedbackRecord] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {
            "validation_id",
            "domain",
            "answer_is_correct",
            "source",
            "votes",
        }:
            raise ValueError("feedback record fields are incomplete or unrecognized")
        votes = _parse_votes(item["votes"])
        validation_id = item["validation_id"]
        domain = item["domain"]
        _require_identifier("validation_id", validation_id)
        _require_identifier("domain", domain)
        if not isinstance(item["answer_is_correct"], bool):
            raise TypeError("answer_is_correct must be a boolean")
        source = item["source"]
        if not isinstance(source, str) or source.strip() == "":
            raise ValueError("source must be a non-blank string")
        record = _FeedbackRecord(
            validation_id=validation_id,
            domain=domain,
            answer_is_correct=item["answer_is_correct"],
            source=source,
            votes=votes,
        )
        if record.validation_id in feedback:
            raise ValueError("reputation state repeats a validation id")
        feedback[record.validation_id] = record
    return feedback


def _parse_votes(value: object) -> tuple[_Vote, ...]:
    if not isinstance(value, list):
        raise ValueError("feedback votes must be a list")
    votes: list[_Vote] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {
            "verifier_name",
            "passed",
            "abstained",
        }:
            raise ValueError("feedback vote fields are incomplete or unrecognized")
        verifier_name = item["verifier_name"]
        _require_identifier("verifier_name", verifier_name)
        if not isinstance(item["passed"], bool) or not isinstance(item["abstained"], bool):
            raise TypeError("feedback vote flags must be booleans")
        if verifier_name in seen:
            raise ValueError("feedback record repeats a verifier")
        seen.add(verifier_name)
        votes.append(
            _Vote(
                verifier_name=verifier_name,
                passed=item["passed"],
                abstained=item["abstained"],
            )
        )
    return tuple(votes)


def _require_feedback_within_counts(
    counts: Mapping[tuple[str, str], _Counts],
    feedback: Mapping[str, _FeedbackRecord],
) -> None:
    implied: dict[tuple[str, str], _Counts] = {}
    for record in feedback.values():
        for vote in record.votes:
            if vote.abstained:
                continue
            pair = implied.setdefault((vote.verifier_name, record.domain), _Counts())
            if vote.passed == record.answer_is_correct:
                pair.successes += 1
            else:
                pair.failures += 1
    for key, required in implied.items():
        actual = counts.get(key, _Counts())
        if actual.successes < required.successes or actual.failures < required.failures:
            raise ValueError(
                "reputation counts are smaller than the stored feedback observations"
            )


def _with_observation(
    counts: Mapping[tuple[str, str], _Counts],
    verifier_name: str,
    domain: str,
    succeeded: bool,
) -> dict[tuple[str, str], _Counts]:
    """Return a copy of ``counts`` with one integer observation added."""
    staged = {
        key: _Counts(value.successes, value.failures) for key, value in counts.items()
    }
    current = staged.get((verifier_name, domain), _Counts())
    if succeeded:
        staged[(verifier_name, domain)] = _Counts(current.successes + 1, current.failures)
    else:
        staged[(verifier_name, domain)] = _Counts(current.successes, current.failures + 1)
    return staged


def _require_readable_counts(
    prior_alpha: float,
    prior_beta: float,
    counts: Mapping[tuple[str, str], _Counts],
) -> None:
    """Reject a proposal whose pairs statistics and restore could not read."""
    for row in counts.values():
        _components(prior_alpha, prior_beta, row.successes, row.failures)


def _components(
    prior_alpha: float,
    prior_beta: float,
    successes: int,
    failures: int,
) -> tuple[float, float, float, float]:
    """Return alpha, beta, posterior mean, and posterior variance.

    The mean is alpha / (alpha + beta), computed with a ratio so large or
    tiny finite priors do not overflow the sum. The variance is the same
    Beta formula, rewritten as mean * (1 - mean) / (alpha + beta + 1).
    """
    alpha = _shift_prior(prior_alpha, successes)
    beta = _shift_prior(prior_beta, failures)
    mean, variance = _belief(alpha, beta)
    return alpha, beta, mean, variance


def _shift_prior(prior: float, count: int) -> float:
    count_value = _exact_count_float(count)
    try:
        shifted = prior + count_value
    except OverflowError as exc:
        raise ValueError("reputation parameters cannot be represented safely") from exc
    if not math.isfinite(shifted) or shifted <= 0.0:
        raise ValueError("reputation parameters cannot be represented safely")
    return shifted


def _exact_count_float(count: int) -> float:
    try:
        value = float(count)
    except OverflowError as exc:
        raise ValueError("reputation counts cannot be represented safely") from exc
    if not math.isfinite(value) or value != count:
        raise ValueError("reputation counts cannot be represented safely")
    return value


def _belief(alpha: float, beta: float) -> tuple[float, float]:
    if (
        not math.isfinite(alpha)
        or not math.isfinite(beta)
        or alpha <= 0.0
        or beta <= 0.0
    ):
        raise ValueError("reputation parameters cannot be represented safely")
    if alpha >= beta:
        ratio = beta / alpha
        mean = 1.0 / (1.0 + ratio)
        scale = alpha
    else:
        ratio = alpha / beta
        mean = ratio / (1.0 + ratio)
        scale = beta
    if scale <= 1.0:
        # alpha + beta + 1 is safe here; reciprocal scaling can overflow.
        variance = mean * (1.0 - mean) / (1.0 + scale * (1.0 + ratio))
    else:
        # Keep the scaled form so very large alpha + beta cannot overflow.
        inside = 1.0 + ratio + (1.0 / scale)
        variance = mean * (1.0 - mean) / scale / inside
    if not math.isfinite(mean) or not math.isfinite(variance):
        raise ValueError("reputation parameters cannot be represented safely")
    return mean, variance


def _require_prior(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite positive number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be a finite positive number") from exc
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be a finite positive number")
    return number


def _require_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{name} must be a non-blank string")


def _require_count(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value
