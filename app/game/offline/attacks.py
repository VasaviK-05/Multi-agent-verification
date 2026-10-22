"""Single-group report corruption, not upstream evidence compromise."""

from typing import Literal
from pydantic import model_validator

from app.decision.coverage import factual_capabilities
from app.decision.vote_normalization import is_abstention, signed_mass, vote_confidence
from app.game.dependencies import FrozenModel, DependencyRegistry
from app.game.models import canonical_json, content_id
from app.game.offline.records import Attempt


class AttackSpecification(FrozenModel):
    version: Literal["report_corruption_v1"]
    suppression: Literal["unavailable", "abstention"]

    @property
    def specification_id(self):
        return content_id(self.model_dump(mode="json"))


class Attack(FrozenModel):
    specification_id: str
    kind: Literal["clean", "forced_support", "forced_rejection", "confidence_inflation", "suppression"]
    group_id: str | None
    members: tuple[str, ...]

    @model_validator(mode="after")
    def check(self):
        if (self.kind == "clean") != (self.group_id is None and not self.members):
            raise ValueError("clean has no group; corruption requires one full failure group")
        if self.kind != "clean" and (not self.members or self.group_id != content_id(tuple(sorted(self.members)))):
            raise ValueError("attack group must bind full component membership")
        object.__setattr__(self, "members", tuple(sorted(self.members)))
        return self

    @property
    def attack_id(self):
        return content_id(self.model_dump(mode="json"))


class AttackAudit(FrozenModel):
    attack_id: str
    version: str
    experiment: Literal["report_level_corruption"] = "report_level_corruption"
    validation_id: str
    verifier_name: str
    before_state: str
    after_state: str
    before_mass: float | None
    after_mass: float | None
    before_passed: bool | None
    after_passed: bool | None
    before_coverage: tuple[str, ...]
    after_coverage: tuple[str, ...]
    effective: bool
    reason: str


def enumerate_attacks(registry, specification):
    registry = DependencyRegistry.model_validate(registry)
    specification = AttackSpecification.model_validate(specification)
    names = set(registry.unresolved)
    for dependency in registry.dependencies:
        names.update(dependency.verifiers)
    groups = registry.groups(names)
    actions = [Attack(specification_id=specification.specification_id, kind="clean", group_id=None, members=())]
    for group in groups:
        for kind in ("forced_support", "forced_rejection", "confidence_inflation", "suppression"):
            actions.append(Attack(specification_id=specification.specification_id, kind=kind,
                                  group_id=group.group_id, members=group.verifiers))
    return tuple(actions)


def transform(attempt, attack, specification):
    """No label or sampled-team parameter: target/action was committed beforehand."""
    attempt = Attempt.model_validate(attempt)
    attack = Attack.model_validate(attack)
    specification = AttackSpecification.model_validate(specification)
    if attack.specification_id != specification.specification_id:
        raise ValueError("attack specification mismatch")
    row = attempt.report
    before = None if row is None else signed_mass(row)
    before_passed = None if row is None else row.passed
    before_coverage = () if row is None else tuple(sorted(factual_capabilities(row)))
    reason = "outside_target"
    result = attempt
    if attack.kind == "clean":
        reason = "clean"
    elif attempt.verifier_name in attack.members:
        if row is None:
            reason = "no_returned_report"
        elif attack.kind == "suppression":
            reason = "suppressed"
            data = attempt.model_dump()
            if specification.suppression == "unavailable":
                data.update(state="unavailable", report_json=None)
            else:
                row.metadata = {**(row.metadata or {}), "decision": "UNSURE"}
                data.update(state="abstention", report_json=canonical_json(row.model_dump(mode="python")))
            result = Attempt(**data)
        elif is_abstention(row):
            reason = "preserved_abstention"
        else:
            expected_adapter = {"rule": "rule_v1", "evidence": "evidence_v1", "confidence": "confidence_v1",
                                "semantic": "semantic_v1"}.get(row.verifier_name, "generic_v1")
            if attempt.adapter != expected_adapter:
                raise ValueError("unsupported verifier-aware transformation adapter")
            direction = row.passed if attack.kind == "confidence_inflation" else attack.kind == "forced_support"
            metadata = dict(row.metadata or {})
            decision = "SUPPORT" if direction else "REJECT"
            metadata["decision"] = decision
            if attempt.adapter == "rule_v1":
                # Correctness bit; rule identity/kind and original result provenance remain.
                row.score = 1. if direction else 0.
            else:
                row.score = 1.
            if attempt.adapter == "confidence_v1" and attack.kind != "confidence_inflation":
                judgments = metadata.get("judgments")
                if judgments is not None and not isinstance(judgments, list):
                    raise ValueError("unsupported confidence judgments payload")
                metadata["judgments"] = [decision.lower()] * max(1, len(judgments or []))
                metadata["majority_label"] = decision.lower()
            if attempt.adapter == "evidence_v1" and attack.kind != "confidence_inflation":
                label = "entailment" if direction else "contradiction"
                old_rows = metadata.get("supporting" if row.passed else "contradicting")
                claims = metadata.get("claim_decisions")
                # Never invent a coverage certificate when the recording has none.
                if old_rows is not None:
                    if not isinstance(old_rows, list) or any(not isinstance(r, dict) for r in old_rows):
                        raise ValueError("unsupported evidence rows")
                    metadata["supporting" if direction else "contradicting"] = [dict(r, nli_label=label) for r in old_rows]
                    metadata["contradicting" if direction else "supporting"] = []
                if claims is not None:
                    if not isinstance(claims, list) or any(not isinstance(c, dict) for c in claims):
                        raise ValueError("unsupported claim decisions")
                    metadata["claim_decisions"] = [dict(c, decision=decision) for c in claims]
                metadata.update(nli_label=label, unsure_reason=None)
            row.passed, row.metadata = direction, metadata
            data = attempt.model_dump()
            data["report_json"] = canonical_json(row.model_dump(mode="python"))
            result = Attempt(**data)
            if is_abstention(result.report) or vote_confidence(result.report) != 1. or result.report.passed != direction:
                raise ValueError("attack normalization postcondition failed")
            reason = "transformed_directional_report"
    after = None if result.report is None else signed_mass(result.report)
    after_passed = None if result.report is None else result.report.passed
    after_coverage = () if result.report is None else tuple(sorted(factual_capabilities(result.report)))
    audit = AttackAudit(attack_id=attack.attack_id, version=specification.version,
        validation_id=attempt.execution_id, verifier_name=attempt.verifier_name,
        before_state=attempt.state, after_state=result.state, before_mass=before, after_mass=after,
        before_passed=before_passed, after_passed=after_passed,
        before_coverage=before_coverage, after_coverage=after_coverage,
        effective=(attempt.state != result.state or before != after or before_passed != after_passed
                   or before_coverage != after_coverage), reason=reason)
    return result, audit
