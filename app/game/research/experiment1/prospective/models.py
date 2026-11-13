"""Outcome-free prospective protocol and immutable, explicitly supplied evidence.

Hashes authenticate bytes relative to a caller-trusted digest, not the truth of a
producer's claims. Authority/custody records remain an external review boundary.
No artifact locator is followed and no Final Test outcomes are representable here.
"""
import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, StrictBool, StrictFloat, StrictInt, model_validator

from app.game.dependencies import DependencyRegistry, FrozenModel, identifier
from app.game.models import content_id
from app.game.offline.attacks import AttackSpecification
from app.game.offline.collection import Candidate
from app.game.offline.records import TrainingManifest
from app.game.research.experiment1.manifest import AtomicEntry
from app.game.research.specification import PolicyBuildSpecification
from app.game.research.__main__ import _object, _nonfinite
from app.game.resource_provenance import ResourceManifest

Text = Annotated[str, AfterValidator(identifier)]


def reviewed_record(value):
    identifier(value)
    if value.upper().startswith(('PENDING', 'UNRESOLVED', 'UNAPPROVED', 'TODO', 'MISSING', 'UNKNOWN', 'NOT_AUTHORIZED')):
        raise ValueError('unresolved placeholder is not reviewed evidence or authorization')
    return value


ReviewedText = Annotated[str, AfterValidator(reviewed_record)]
Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
CohortName = Literal['arithmetic', 'factual']
Role = Literal['history', 'development', 'final_test']
HISTORICAL_POLICIES = frozenset({
    'c6a1f9c14bf2337aa3202124a2ed087616d48a46d70f56e7f37aba0a2a446e14',
    '0df33426333e0f7bbe6418fdf7900719dbda5182f68d50405b593b3341ec9d0d',
    '0192b98e50ab5dcbd40ca78a0d4a3ec3978dfe8086edcb615802c21024c83532',
    'c05a50fb5fc3651c8dc5d1bd55ec02086c3f4c26e49e7145393cb007e7149cda',
})


class LabelProvenance(FrozenModel):
    method: Literal['independent_human', 'independent_ground_truth', 'provisional_automated']
    basis: Literal['human_adjudication', 'independent_ground_truth', 'synthetic_transformation', 'provisional_automated']
    source: Text
    producer_protocol: Text
    independent_review_record: ReviewedText | None = None
    record: ReviewedText
    human_verified: StrictBool

    @model_validator(mode='after')
    def check(self):
        if self.human_verified != (self.method == 'independent_human'):
            raise ValueError('human verification must match independent human provenance')
        expected = {'independent_human': {'human_adjudication'},
                    'independent_ground_truth': {'independent_ground_truth'},
                    'provisional_automated': {'synthetic_transformation', 'provisional_automated'}}
        if self.basis not in expected[self.method]:
            raise ValueError('provisional/synthetic labels cannot be cast to independent truth')
        return self


class Member(FrozenModel):
    """Split/input/label provenance only: deliberately no answer or correctness bit."""
    example_id: Text
    group_id: Text
    question_id: Text
    content_id: Digest
    validation_id: Text
    role: Role
    reference_sha256: Digest | None
    label: LabelProvenance


class Exclusion(FrozenModel):
    example_id: Text | None
    group_id: Text
    reason: Text
    source_record: Text
    quarantine_group: StrictBool

    @model_validator(mode='after')
    def check(self):
        if self.example_id is None and not self.quarantine_group:
            raise ValueError('group-only exclusions must exclude the whole group')
        return self


class Population(FrozenModel):
    dataset_ids: tuple[tuple[Role, Text], ...]
    source_sha256: Digest
    grouping_record: Text
    members: tuple[Member, ...] = Field(min_length=1)
    excluded: tuple[Exclusion, ...] = ()

    @model_validator(mode='after')
    def check(self):
        if len(self.dataset_ids) != 3 or set(dict(self.dataset_ids)) != {'history', 'development', 'final_test'} or len(set(dict(self.dataset_ids).values())) != 3:
            raise ValueError('three distinct dataset roles and identities required')
        if {e.role for e in self.members} != {'history', 'development', 'final_test'}:
            raise ValueError('nonempty History/Development and outcome-free Final Test roster required')
        for field in ('example_id', 'validation_id'):
            values = [getattr(e, field) for e in self.members]
            if len(values) != len(set(values)):
                raise ValueError('duplicate population identity: ' + field)
        for field in ('group_id', 'question_id', 'content_id'):
            seen = {}
            for e in self.members:
                value = getattr(e, field)
                if value in seen and seen[value][0] != e.role:
                    raise ValueError('split overlap: ' + field)
                if field != 'group_id' and value in seen and seen[value][1] != e.group_id:
                    raise ValueError('related inputs must share one group')
                seen[value] = e.role, e.group_id
        ids = [e.example_id for e in self.excluded if e.example_id is not None]
        keys = [(e.example_id, e.group_id) for e in self.excluded]
        if len(ids) != len(set(ids)) or len(keys) != len(set(keys)):
            raise ValueError('duplicate exclusion identity')
        included = {e.example_id for e in self.members}
        quarantined = {e.group_id for e in self.excluded if e.quarantine_group}
        if included & {e.example_id for e in self.excluded} or quarantined & {e.group_id for e in self.members}:
            raise ValueError('excluded/quarantined examples cannot enter any split')
        return self

    @property
    def population_id(self):
        return content_id(self.model_dump(mode='json'))


class Choices(FrozenModel):
    """Nulls are unresolved, never numerical scientific defaults."""
    minimum_selected: StrictInt | None = Field(default=None, ge=1, le=4)
    minimum_informative: StrictInt | None = Field(default=None, ge=1, le=4)
    development_coverage_floor: StrictFloat | None = Field(default=None, ge=0, le=1)
    budget: StrictFloat | None = Field(default=None, ge=0)
    resource_coefficient: StrictFloat | None = Field(default=None, ge=0)
    cost_units: Text | None = None
    attempt_costs: tuple[tuple[Text, StrictFloat], ...] | None = None
    history_prior_alpha: StrictFloat | None = Field(default=None, gt=0)
    history_prior_beta: StrictFloat | None = Field(default=None, gt=0)
    failure_contract: Literal['all_selected_returned', 'allow_failed_if_covered'] | None = None
    optimizer_tolerance: StrictFloat | None = Field(default=None, gt=0, le=1e-3)
    validation_epsilon: StrictFloat | None = Field(default=None, gt=0, le=1e-3)
    cost_tolerance: StrictFloat | None = Field(default=None, gt=0, le=1e-3)
    objective: Literal['validation_then_attempt_cost_v1', 'cost_inclusive_minimax'] | None = None


    @model_validator(mode='after')
    def check(self):
        if self.attempt_costs is not None and (not self.attempt_costs or len(dict(self.attempt_costs)) != len(self.attempt_costs) or any(v < 0 for _, v in self.attempt_costs)):
            raise ValueError('nonnegative costs for unique candidates required')
        return self


class Statistics(FrozenModel):
    confidence_level: Literal[.95] = .95
    resamples: StrictInt = Field(ge=2)
    seed: StrictInt = Field(ge=0)
    grouping: Literal['paired_whole_related_groups'] = 'paired_whole_related_groups'
    undefined_risk: Literal['omit_interval_if_any_resample_undefined'] = 'omit_interval_if_any_resample_undefined'


class Evidence(FrozenModel):
    kind: Literal['labels', 'task_support', 'eligibility', 'reference', 'resources',
                  'collector', 'custody', 'calibration']
    subject_id: Digest
    artifact_sha256: Digest
    authority: ReviewedText
    record: ReviewedText


def fitting_specification(spec):
    """Recover the approved input without changing any fitted policy/comparison.

    Only the two explicitly derived matrix overlays differ after preparation.
    Keep the original input for approval; do not authorize a refit of that output.
    """
    data = spec.model_dump()
    data['context']['clean_coverage_json'] = None
    data['context']['reliability_first_json'] = None
    return PolicyBuildSpecification.model_validate(data)


class Cohort(FrozenModel):
    name: CohortName
    population_kind: Literal['bounded_arithmetic', 'grounded_direct_fact', 'unresolved'] = 'unresolved'
    source_benchmark: Text | None = None
    population: Population | None = None
    resources: ResourceManifest | None = None
    candidates: tuple[Candidate, ...] = ()
    reference_contract: Text | None = None
    final_exposure: Literal['untouched_reserved', 'independence_unverified', 'previously_exposed'] | None = None
    dependencies: DependencyRegistry | None = None
    attacks: AttackSpecification | None = None
    choices: Choices = Field(default_factory=Choices)
    evidence: tuple[Evidence, ...] = ()
    training: TrainingManifest | None = None
    specification: PolicyBuildSpecification | None = None
    frozen: AtomicEntry | None = None

    @model_validator(mode='after')
    def check(self):
        if len({c.verifier_name for c in self.candidates}) != len(self.candidates):
            raise ValueError('duplicate candidate')
        if self.specification is not None and self.specification.manifest != self.training:
            raise ValueError('fitting specification must bind the exact prospective training input')
        if self.frozen is not None:
            if self.specification is not None and self.specification != fitting_specification(self.frozen.specification):
                raise ValueError('prepared comparison changed the declared fitting specification')
            if self.frozen.cohort != self.name:
                raise ValueError('cohort differs from frozen comparison')
            if self.frozen.comparison.full_artifact.policy.policy_id in HISTORICAL_POLICIES:
                raise ValueError('historical fitted policies cannot enter a new prospective fit')
            if self.training != self.frozen.specification.manifest:
                raise ValueError('frozen comparison must embed the exact prospective training input')
        return self


class Manifest(FrozenModel):
    version: Literal['prospective_experiment1_v1'] = 'prospective_experiment1_v1'
    study_id: Text
    evidence_kind: Literal['empirical', 'synthetic_test_fixture']
    research_question: Literal['joint_team_and_aggregation_tradeoffs_without_superiority_assumption'] = 'joint_team_and_aggregation_tradeoffs_without_superiority_assumption'
    primary_outcome: Literal['worst_case_expected_validation_loss'] = 'worst_case_expected_validation_loss'
    false_accept: Literal[1.] = 1.
    false_reject: Literal[1.] = 1.
    uncertain: Literal[.2] = .2
    threshold: Literal[.55] = .55
    source_commit: Annotated[str, Field(pattern=r'^[0-9a-f]{40}$')] | None = None
    source_fingerprint: Digest | None = None
    reporting_environment: dict[str, str] | None = None
    statistics: Statistics | None = None
    cohorts: tuple[Cohort, ...]
    pooling: Literal['forbidden'] = 'forbidden'

    @model_validator(mode='after')
    def check(self):
        if len(self.cohorts) != 2 or {c.name for c in self.cohorts} != {'arithmetic', 'factual'}:
            raise ValueError('separate Arithmetic and Factual dispositions required exactly once')
        seen, datasets = {}, set()
        for c in self.cohorts:
            if c.population is None:
                continue
            current = set(dict(c.population.dataset_ids).values())
            if datasets & current:
                raise ValueError('cohorts require distinct dataset identities')
            datasets |= current
            for e in c.population.members:
                for key in ('example_id', 'group_id', 'question_id', 'content_id', 'validation_id'):
                    identity = key, getattr(e, key)
                    if identity in seen and seen[identity] != c.name:
                        raise ValueError('cross-cohort population overlap: ' + key)
                    seen[identity] = c.name
        return self

    def cohort(self, name):
        found = next((c for c in self.cohorts if c.name == name), None)
        if found is None:
            raise ValueError('unknown prospective cohort')
        return found

    @property
    def protocol_id(self):
        data = self.model_dump(mode='json')
        for c in data['cohorts']:
            for field in ('evidence', 'training', 'specification', 'frozen', 'final_exposure'):
                c.pop(field)
        return content_id(data)

    def collection_id(self, name):
        c = self.cohort(name)
        return content_id(dict(study_id=self.study_id, cohort=name,
            source_commit=self.source_commit, source_fingerprint=self.source_fingerprint,
            population=c.population.model_dump(mode='json') if c.population else None,
            population_kind=c.population_kind, source_benchmark=c.source_benchmark,
            resources=c.resources.model_dump(mode='json') if c.resources else None,
            candidates=[v.model_dump(mode='json') for v in c.candidates], reference_contract=c.reference_contract))

    def fitting_id(self, name):
        c = self.cohort(name)
        return content_id(dict(protocol_id=self.protocol_id, cohort=name,
            training_id=c.training.manifest_id if c.training else None,
            specification_id=(c.specification or fitting_specification(c.frozen.specification)).specification_id if c.specification is not None or c.frozen is not None else None,
            calibration=[e.model_dump(mode='json') for e in c.evidence if e.kind == 'calibration']))

    @property
    def manifest_id(self):
        return content_id(self.model_dump(mode='json'))


class Approval(FrozenModel):
    scope: Literal['protocol', 'collection', 'fitting']
    subject_id: Digest
    authority: ReviewedText
    decision_record: ReviewedText


class FinalRelease(FrozenModel):
    """External exact-manifest release; no outcomes or payload path allowed."""
    manifest_id: Digest
    cohort: CohortName
    reservation_id: Digest
    payload_sha256: Digest
    authority: ReviewedText
    decision_record: ReviewedText


class Authorizations(FrozenModel):
    approvals: tuple[Approval, ...] = ()
    releases: tuple[FinalRelease, ...] = ()

    @model_validator(mode='after')
    def check(self):
        keys = [(a.scope, a.subject_id) for a in self.approvals]
        if len(keys) != len(set(keys)) or len({r.cohort for r in self.releases}) != len(self.releases):
            raise ValueError('duplicate approval/release')
        return self


def load_authenticated(path, expected_sha256, schema=Manifest):
    """Read one caller-designated document; never follow embedded references."""
    path = Path(path)
    if schema not in (Manifest, Authorizations) or set(path.parts) & {'test', 'final_test', 'heldout'} or path.name in {'final-partition.json', 'reserved-request.json', 'heldout-results.json', 'replay-outcomes.json'}:
        raise ValueError('metadata loader refuses reserved payload paths or schemas')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('manifest/authorization SHA-256 mismatch')
    data = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_nonfinite)
    return schema.model_validate(data)
