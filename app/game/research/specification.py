"""Explicit per-category study inputs. No empirical/scientific defaults."""

from typing import Annotated, Literal
import re

from pydantic import AfterValidator, Field, StrictFloat, StrictInt, model_validator

from app.game.dependencies import FrozenModel, identifier
from app.game.models import PlanningContext, content_id
from app.game.offline.attacks import AttackSpecification
from app.game.offline.records import DatasetManifest, FinalTestReservation, TrainingManifest
from app.game.execution_contract import ExecutionContract

Text = Annotated[str, AfterValidator(identifier)]
Role = Literal["history", "development", "final_test"]


class DatasetDescription(FrozenModel):
    role: Role
    dataset_id: Text
    version: Text
    source: Text
    independent_label_provenance: Text
    declared_label_sources: tuple[Text, ...] = Field(min_length=1)
    grouping_protocol: Text

    @model_validator(mode="after")
    def canonicalize(self):
        if len(set(self.declared_label_sources)) != len(self.declared_label_sources):
            raise ValueError("duplicate label sources")
        object.__setattr__(self, "declared_label_sources", tuple(sorted(self.declared_label_sources)))
        return self


class RecordingConfiguration(FrozenModel):
    execution_configuration_id: Text
    model_fingerprints: tuple[tuple[Text, Text], ...] = Field(min_length=1)
    corpus_fingerprints: tuple[tuple[Text, Text], ...] = Field(min_length=1)
    prompt_and_adapter_fingerprints: tuple[tuple[Text, Text], ...] = Field(min_length=1)
    collection_protocol: Literal["complete_team_independent_v1"]

    @model_validator(mode="after")
    def canonicalize(self):
        for field in ("model_fingerprints", "corpus_fingerprints", "prompt_and_adapter_fingerprints"):
            pairs = getattr(self, field)
            if len({k for k, _ in pairs}) != len(pairs):
                raise ValueError("duplicate fingerprint identity")
            object.__setattr__(self, field, tuple(sorted(pairs)))
        return self


class UncertaintyDesign(FrozenModel):
    method: Literal["paired_split_identity_cluster_percentile_v1"]
    resamples: StrictInt = Field(ge=2)
    confidence_level: StrictFloat = Field(gt=0, lt=1)
    seed: StrictInt = Field(ge=0)


class ExperimentSpecification(FrozenModel):
    version: Literal["game_research_v1"]
    study_id: Text
    configuration_version: Text
    code_revision: Text
    setting_role: Literal["primary", "sensitivity"]
    primary_specification_id: Text | None
    scientific_scope: Text
    primary_outcomes: tuple[Literal["mean_loss", "worst_case_expected_loss", "decision_coverage", "selective_risk"], ...] = Field(min_length=1)
    sensitivity_plan: tuple[Text, ...] = Field(min_length=1)
    matched_coverage_plan: Text
    final_test_custody_and_freeze_protocol: Text
    datasets: tuple[DatasetDescription, ...]
    recording: RecordingConfiguration
    context: PlanningContext
    manifest: DatasetManifest
    contract: ExecutionContract
    attacks: AttackSpecification
    unknown_dependency_treatment: Literal["shared_unknown"]
    greedy_aggregation: Literal["reputation_weighted", "dependency_group"]
    policy_sampling_seeds: tuple[StrictInt, ...] = Field(min_length=1)
    policy_sampling_repetitions: StrictInt = Field(ge=1)
    uncertainty: UncertaintyDesign
    optimizer_tolerance: StrictFloat = Field(gt=0, le=1e-3)

    @model_validator(mode="after")
    def validate_metadata(self):
        if not re.fullmatch(r"[0-9a-f]{40}", self.code_revision):
            raise ValueError("code_revision must be an exact Git SHA-1")
        if (self.setting_role == "primary") != (self.primary_specification_id is None):
            raise ValueError("sensitivity settings require the frozen primary specification ID")
        if len(self.datasets) != 3 or {d.role for d in self.datasets} != {"history", "development", "final_test"}:
            raise ValueError("describe each dataset role exactly once")
        for description in self.datasets:
            part = self.manifest.partition(description.role)
            if part.dataset_id != description.dataset_id:
                raise ValueError("dataset description differs from manifest")
            if isinstance(part, FinalTestReservation):
                # Labels/reports are released only in the separate final evaluator.
                continue
            if not {e.label_source for e in part.examples} <= set(description.declared_label_sources):
                raise ValueError("undeclared independent label source")
            known_groups = {}
            for example in part.examples:
                for key in (("question", example.question_id), ("content", example.content_identity)):
                    if key in known_groups and known_groups[key] != example.split_identity:
                        raise ValueError("related question/content must share one split identity within a role")
                    known_groups[key] = example.split_identity
        if self.unknown_dependency_treatment != self.context.dependencies.unknown_treatment:
            raise ValueError("unknown-dependency declaration differs from context")
        if self.recording.execution_configuration_id != self.contract.execution_configuration_id:
            raise ValueError("recording configuration differs from execution contract")
        if (len(set(self.policy_sampling_seeds)) != len(self.policy_sampling_seeds)
                or any(s < 0 for s in self.policy_sampling_seeds)):
            raise ValueError("sampling seeds must be unique and nonnegative")
        if len(set(self.primary_outcomes)) != len(self.primary_outcomes):
            raise ValueError("duplicate primary outcomes")
        object.__setattr__(self, "datasets", tuple(sorted(self.datasets, key=lambda d: d.role)))
        object.__setattr__(self, "policy_sampling_seeds", tuple(sorted(self.policy_sampling_seeds)))
        object.__setattr__(self, "primary_outcomes", tuple(sorted(self.primary_outcomes)))
        object.__setattr__(self, "sensitivity_plan", tuple(sorted(set(self.sensitivity_plan))))
        return self

    @property
    def specification_id(self):
        return content_id(self.model_dump(mode="json"))


class PolicyBuildSpecification(ExperimentSpecification):
    """Dedicated fitting schema; research readiness CLI retains its full schema."""
    version: Literal["offline_policy_build_v1"]
    manifest: TrainingManifest
