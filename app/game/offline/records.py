"""Detached replay records and independently labelled, leakage-checked partitions."""

from typing import Literal

from pydantic import StrictBool, model_serializer, model_validator

from app.decision.report_identity import canonical_reports
from app.decision.vote_normalization import is_abstention
from app.game.dependencies import FrozenModel, identifier
from app.game.models import canonical_json, content_id
from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import ReputationManager


class Attempt(FrozenModel):
    verifier_name: str
    state: Literal["directional", "abstention", "unavailable", "failed", "missing"]
    report_json: str | None = None
    execution_id: str
    configuration_id: str
    report_provenance: str
    adapter: Literal["generic_v1", "rule_v1", "evidence_v1", "confidence_v1", "semantic_v1"]
    observed_resources_json: str | None = None

    @model_serializer(mode="wrap")
    def serialize_attempt(self, handler):
        data = handler(self)
        if self.observed_resources_json is None:
            data.pop("observed_resources_json", None)
        return data

    @model_validator(mode="after")
    def check(self):
        if self.observed_resources_json is not None:
            from app.game.resource_provenance import VerifierResources
            observation = VerifierResources.model_validate_json(self.observed_resources_json, strict=True)
            if observation.verifier_name != self.verifier_name:
                raise ValueError("observed resource verifier identity mismatch")
            object.__setattr__(self, "observed_resources_json", canonical_json(observation.model_dump(mode="json")))
        for value in (self.verifier_name, self.execution_id, self.configuration_id, self.report_provenance):
            identifier(value)
        if (self.state in {"directional", "abstention"}) != (self.report_json is not None):
            raise ValueError("returned states require a report; other outcomes cannot contain one")
        if self.report_json is not None:
            row = VerificationResult.model_validate_json(self.report_json, strict=True)
            rows, _, _ = canonical_reports([row], team=(self.verifier_name,), validation_id=self.execution_id)
            if is_abstention(rows[0]) != (self.state == "abstention"):
                raise ValueError("recorded state differs from normalized behavior")
            object.__setattr__(self, "report_json", canonical_json(rows[0].model_dump(mode="python")))
        return self

    @property
    def report(self):
        return None if self.report_json is None else VerificationResult.model_validate_json(self.report_json)


class Example(FrozenModel):
    example_id: str
    split_identity: str
    question_id: str
    question: str
    answer: str
    reference: str | None
    domain: str
    planning_category: str
    answer_is_correct: StrictBool
    label_source: str
    label_method: Literal["independent_human", "independent_ground_truth"]
    validation_id: str
    execution_configuration_id: str
    # A caller attests no team/order/prefix/context-dependent verifier behavior.
    cache_contract: Literal["complete_team_independent_v1"]
    attempts: tuple[Attempt, ...]

    @model_validator(mode="after")
    def check(self):
        for value in (self.example_id, self.split_identity, self.question_id, self.question,
                      self.domain, self.planning_category, self.label_source,
                      self.validation_id, self.execution_configuration_id):
            identifier(value)
        names = [a.verifier_name for a in self.attempts]
        if not names or len(names) != len(set(names)):
            raise ValueError("recording requires unique verifier outcomes")
        if any(a.execution_id != self.validation_id or a.configuration_id != self.execution_configuration_id
               for a in self.attempts):
            raise ValueError("recording execution/configuration provenance mismatch")
        object.__setattr__(self, "attempts", tuple(sorted(self.attempts, key=lambda a: a.verifier_name)))
        return self

    @property
    def content_identity(self):
        return content_id([self.question, self.answer, self.reference])


class Partition(FrozenModel):
    role: Literal["history", "development", "final_test"]
    dataset_id: str
    examples: tuple[Example, ...]

    @model_validator(mode="after")
    def check(self):
        identifier(self.dataset_id)
        ids = [e.example_id for e in self.examples]
        runs = [e.validation_id for e in self.examples]
        if not ids or len(ids) != len(set(ids)) or len(runs) != len(set(runs)):
            raise ValueError("partitions must be nonempty with unique examples and runs")
        object.__setattr__(self, "examples", tuple(sorted(self.examples, key=lambda e: e.example_id)))
        return self


class DatasetManifest(FrozenModel):
    version: str
    evidence_kind: Literal["empirical", "synthetic_test_fixture"]
    partitions: tuple[Partition, ...]

    @model_validator(mode="after")
    def check(self):
        identifier(self.version)
        if sorted(p.role for p in self.partitions) != ["development", "final_test", "history"]:
            raise ValueError("exactly history, development, final_test partitions required")
        if len({p.dataset_id for p in self.partitions}) != 3:
            raise ValueError("dataset identifiers must be distinct")
        seen = {}
        for part in self.partitions:
            for example in part.examples:
                for kind, value in (("example", example.example_id), ("group", example.split_identity),
                                    ("question", example.question_id), ("content", example.content_identity),
                                    ("run", example.validation_id)):
                    key = kind, value
                    if key in seen and seen[key] != part.role:
                        raise ValueError(f"split leakage across roles: {kind}")
                    seen[key] = part.role
        object.__setattr__(self, "partitions", tuple(sorted(self.partitions, key=lambda p: p.role)))
        return self

    def partition(self, role):
        return next(p for p in self.partitions if p.role == role)

    @property
    def manifest_id(self):
        return content_id(self.model_dump(mode="json"))


def history_reputation(manifest, *, prior_alpha, prior_beta):
    """Return a new, non-persistent manager; learn only independent history labels."""
    if isinstance(manifest, Partition):
        history = Partition.model_validate(manifest)
        if history.role != "history":
            raise ValueError("only history may establish reputation")
    else:
        history = DatasetManifest.model_validate(manifest).partition("history")
    manager = ReputationManager(prior_alpha=prior_alpha, prior_beta=prior_beta)
    for example in history.examples:
        for attempt in example.attempts:
            if attempt.state == "missing":
                raise ValueError("history recording is incomplete")
            if attempt.state == "directional":
                manager.update_from_ground_truth(attempt.verifier_name, example.domain,
                                                 attempt.report.passed, example.answer_is_correct)
    return manager
