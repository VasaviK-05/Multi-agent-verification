"""Dataset-free lineage of an explicitly weighted pooled development game."""

from typing import Literal

from pydantic import Field, StrictFloat, model_validator

from app.game.dependencies import FrozenModel, identifier


class PoolSource(FrozenModel):
    domain: str
    compatibility_id: str
    manifest_id: str
    matrix_id: str
    weight: StrictFloat = Field(gt=0, le=1)

    @model_validator(mode="after")
    def check(self):
        for value in (self.domain, self.compatibility_id, self.manifest_id, self.matrix_id):
            identifier(value)
        return self


class PoolingContract(FrozenModel):
    version: Literal["weighted_domain_pool_v1"] = "weighted_domain_pool_v1"
    pool_id: str
    # Explicit weights over domain means; no implicit population weighting.
    sources: tuple[PoolSource, ...]
    # Exact pre-pooling target context digests, including target history snapshots.
    applicability: tuple[tuple[str, str], ...]
    payoff_digest: str

    @model_validator(mode="after")
    def check(self):
        import math
        identifier(self.pool_id)
        identifier(self.payoff_digest)
        domains = [s.domain for s in self.sources]
        targets = dict(self.applicability)
        if len(domains) < 2 or len(domains) != len(set(domains)):
            raise ValueError("a pool requires at least two unique source domains")
        if not math.isclose(math.fsum(s.weight for s in self.sources), 1., rel_tol=0., abs_tol=1e-12):
            raise ValueError("explicit source-domain weights must sum to one")
        if not targets or len(targets) != len(self.applicability):
            raise ValueError("pool requires unique explicit target domains")
        for domain, digest in self.applicability:
            identifier(domain)
            identifier(digest)
        if any(targets.get(source.domain) != source.compatibility_id for source in self.sources):
            raise ValueError("pool source context must match its explicit applicability")
        object.__setattr__(self, "sources", tuple(sorted(self.sources, key=lambda s: s.domain)))
        object.__setattr__(self, "applicability", tuple(sorted(self.applicability)))
        return self

    @property
    def pooling_id(self):
        from app.game.models import content_id
        return content_id(self.model_dump(mode="json"))


def unpooled_context(context):
    from app.game.models import PlanningContext
    data = context.model_dump()
    data["pooling_contract_json"] = None
    return PlanningContext(**data)


def check_pool_matrix(context, matrix):
    """Prevent a domain-only or altered matrix from claiming pooled lineage."""
    if context.pooling_contract_json is not None:
        contract = PoolingContract.model_validate_json(context.pooling_contract_json, strict=True)
        expected = pooled_payoff_digest(matrix.strategy_definitions, matrix.attack_ids, matrix.values)
        if expected != contract.payoff_digest:
            raise ValueError("matrix differs from the bound pooled development payoffs")


def pooled_payoff_digest(strategies, attacks, values):
    from app.game.models import content_id
    return content_id({"strategies": [s.model_dump(mode="json") for s in strategies],
                       "attacks": attacks, "values": values})
