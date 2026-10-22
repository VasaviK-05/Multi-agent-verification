"""Configured compromise pathways, separate from expected capabilities."""

from pydantic import BaseModel, ConfigDict, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False,
                              revalidate_instances="always")


def identifier(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError("identifiers must be nonblank strings without surrounding whitespace")
    return value


class Dependency(FrozenModel):
    resource_id: str
    compromise_pathway: str
    verifiers: tuple[str, ...]

    @model_validator(mode="after")
    def validate_resource(self):
        identifier(self.resource_id)
        identifier(self.compromise_pathway)
        if not self.verifiers or len(set(self.verifiers)) != len(self.verifiers):
            raise ValueError("dependency requires unique affected verifiers")
        for name in self.verifiers:
            identifier(name)
        object.__setattr__(self, "verifiers", tuple(sorted(self.verifiers)))
        return self


class FailureGroup(FrozenModel):
    group_id: str
    verifiers: tuple[str, ...]


class DependencyRegistry(FrozenModel):
    version: str
    dependencies: tuple[Dependency, ...] = ()
    unresolved: tuple[str, ...] = ()
    unknown_treatment: str = "shared_unknown"

    @model_validator(mode="after")
    def validate_registry(self):
        identifier(self.version)
        if self.unknown_treatment != "shared_unknown":
            raise ValueError("Stage 1 supports the declared shared_unknown treatment only")
        ids = [row.resource_id for row in self.dependencies]
        if len(ids) != len(set(ids)) or len(self.unresolved) != len(set(self.unresolved)):
            raise ValueError("duplicate dependency or unresolved identifier")
        for name in self.unresolved:
            identifier(name)
        object.__setattr__(self, "dependencies", tuple(sorted(self.dependencies, key=lambda d: d.resource_id)))
        object.__setattr__(self, "unresolved", tuple(sorted(self.unresolved)))
        return self

    def groups(self, verifier_names) -> tuple[FailureGroup, ...]:
        # Build components over the entire registry before projecting a team:
        # an absent bridge verifier must not split a configured failure group.
        from app.game.models import content_id
        names = tuple(sorted(verifier_names))
        if len(names) != len(set(names)):
            raise ValueError("duplicate verifier names")
        configured = set(self.unresolved)
        for dependency in self.dependencies:
            configured.update(dependency.verifiers)
        if not set(names) <= configured:
            raise ValueError("each candidate must have explicit dependencies or be unresolved")
        components = {name: {name} for name in configured}
        relationships = [d.verifiers for d in self.dependencies]
        if self.unresolved:
            relationships.append(self.unresolved)
        for relationship in relationships:
            merged = set().union(*(components[name] for name in relationship))
            for name in merged:
                components[name] = merged
        unique = {tuple(sorted(components[name])) for name in names}
        return tuple(FailureGroup(group_id=content_id(component),
                                  verifiers=tuple(n for n in component if n in names))
                     for component in sorted(unique))

    @property
    def assumptions(self) -> tuple[str, ...]:
        return ("configured compromise pathways; conservative connected components",
                "unresolved verifiers share one unknown compromise pathway",
                "observed provenance is audit-only and never rewrites this registry")
