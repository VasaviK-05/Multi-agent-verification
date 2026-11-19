"""Opt-in, versioned category scope over unchanged frozen game artifacts.

A declaration is an auditable scope assertion, not statistical certification.
Only independently reviewed declarations should be installed by the operator.
No historical artifact is promoted implicitly.
"""
from typing import Literal
from pydantic import Field, model_validator
from app.game.dependencies import FrozenModel


VERIFIERS = frozenset(('rule', 'evidence', 'semantic', 'confidence'))
SCENARIOS = frozenset(('correct', 'incorrect', 'uncertain', 'unsupported', 'resource_unavailable'))


class CategoryApplicability(FrozenModel):
    version: Literal['category_applicability_v1'] = 'category_applicability_v1'
    artifact_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    task_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    supported_distribution: str = Field(min_length=1)
    exclusions: tuple[str, ...]
    reviewed_by: str = Field(min_length=1)
    # Hashes of retained reports, never a flag claiming automatic certification.
    development_report: str = Field(pattern=r'^[0-9a-f]{64}$')
    held_out_report: str = Field(pattern=r'^[0-9a-f]{64}$')
    baseline_report: str = Field(pattern=r'^[0-9a-f]{64}$')
    evaluated_scenarios: tuple[str, ...]
    evaluated_teams: tuple[tuple[str, ...], ...]
    semantic_contradictions: tuple[str, ...] = ()

    @model_validator(mode='after')
    def check(self):
        if self.development_report == self.held_out_report:
            raise ValueError('development and untouched held-out reports must be distinct')
        if not SCENARIOS <= set(self.evaluated_scenarios):
            raise ValueError('incomplete scenario evaluation')
        if not self.evaluated_teams or len(set(self.evaluated_teams)) != len(self.evaluated_teams):
            raise ValueError('evaluation must list unique teams')
        for team in self.evaluated_teams:
            if not team or tuple(sorted(set(team))) != team or not set(team) <= VERIFIERS:
                raise ValueError('teams must contain sorted unique existing verifier names')
        if any('semantic' in team for team in self.evaluated_teams):
            if not {'numbers', 'negation', 'entities', 'relationships'} <= set(self.semantic_contradictions):
                raise ValueError('semantic contradiction evaluation incomplete')
        return self

    def validate_artifact(self, artifact):
        from app.game.artifacts import PolicyArtifact
        from app.game.task_conditioning import TaskSnapshotBinding
        artifact = PolicyArtifact.model_validate(artifact)
        if artifact.artifact_id != self.artifact_id:
            raise ValueError('category declaration differs from exact frozen artifact')
        binding = TaskSnapshotBinding.model_validate_json(artifact.context.task_conditioning_json or '{}')
        if binding.identity.task_id != self.task_id:
            raise ValueError('category declaration differs from task capability/prerequisite identity')
        # Require evaluation of every enumerated strategy, not just positive mass.
        teams = {tuple(s.verifiers) for s in artifact.policy.strategies}
        if not teams <= set(self.evaluated_teams):
            raise ValueError('policy contains teams outside reviewed category evaluation')
        return artifact


def configuration_from_category_artifacts(artifacts, declarations):
    """Explicit operator installation; existing execution guards remain authoritative.

    No inference, fitting, artifact mutation, or category-to-team selection occurs.
    The caller is responsible for independent report review and custody checks.
    """
    captured = tuple(artifacts)
    declarations = tuple(CategoryApplicability.model_validate(d) for d in declarations)
    by_id = {d.artifact_id: d for d in declarations}
    if len(by_id) != len(declarations) or len(captured) != len(declarations):
        raise ValueError('require one category declaration per artifact')
    validated = []
    for artifact in captured:
        from app.game.artifacts import PolicyArtifact
        artifact = PolicyArtifact.model_validate(artifact)
        if artifact.artifact_id not in by_id:
            raise ValueError('missing category applicability review')
        validated.append(by_id[artifact.artifact_id].validate_artifact(artifact))
    if {a.artifact_id for a in validated} != set(by_id):
        raise ValueError("duplicate artifact or unused category declaration")
    from app.game.question_routing import configuration_from_atomic_artifacts
    return configuration_from_atomic_artifacts(validated)
