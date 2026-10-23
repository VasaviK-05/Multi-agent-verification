"""Pure resource fingerprints supplied by collection/integration adapters.

These records verify consistency, not the truth of an adapter's observations.
No filesystem, model, network or database access takes place here.
"""

import re
from typing import Literal

from pydantic import model_validator

from app.game.dependencies import FrozenModel, identifier


class ResourceFingerprint(FrozenModel):
    resource_id: str
    kind: Literal["implementation", "configuration", "model", "corpus", "index", "prompt", "service"]
    sha256: str

    @model_validator(mode="after")
    def check(self):
        identifier(self.resource_id)
        if re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None:
            raise ValueError("resource fingerprint requires a lowercase SHA-256 digest")
        return self


class VerifierResources(FrozenModel):
    verifier_name: str
    resources: tuple[ResourceFingerprint, ...]

    @model_validator(mode="after")
    def check(self):
        identifier(self.verifier_name)
        keys = [(r.kind, r.resource_id) for r in self.resources]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate verifier resource")
        required = {"implementation", "configuration"} | {
            "semantic": {"model"},
            "evidence": {"model", "corpus", "index"},
            "confidence": {"model", "prompt", "service"},
        }.get(self.verifier_name, set())
        missing = required - {r.kind for r in self.resources}
        if missing:
            raise ValueError("missing required resource kinds: " + ",".join(sorted(missing)))
        object.__setattr__(self, "resources", tuple(sorted(self.resources, key=lambda r: (r.kind, r.resource_id))))
        return self


class ResourceManifest(FrozenModel):
    version: Literal["game_resource_manifest_v1"] = "game_resource_manifest_v1"
    verifiers: tuple[VerifierResources, ...]

    @model_validator(mode="after")
    def check(self):
        names = [v.verifier_name for v in self.verifiers]
        if not names or len(names) != len(set(names)):
            raise ValueError("resource manifest needs unique nonempty verifier entries")
        # One resource identity has one content throughout an execution.
        observed = {}
        for verifier in self.verifiers:
            for resource in verifier.resources:
                key = resource.kind, resource.resource_id
                if key in observed and observed[key] != resource.sha256:
                    raise ValueError("shared resource identity has conflicting fingerprints")
                observed[key] = resource.sha256
        object.__setattr__(self, "verifiers", tuple(sorted(self.verifiers, key=lambda v: v.verifier_name)))
        return self

    @property
    def manifest_id(self):
        from app.game.models import content_id
        return content_id(self.model_dump(mode="json"))

    def require_candidates(self, names):
        if {v.verifier_name for v in self.verifiers} != set(names):
            raise ValueError("resource manifest must cover exactly the captured candidates")

    def require_observation(self, observation):
        observation = VerifierResources.model_validate(observation)
        expected = next((v for v in self.verifiers if v.verifier_name == observation.verifier_name), None)
        if expected != observation:
            raise ValueError("observed verifier resources differ from the evaluated manifest")


def validate_recorded_resources(contract, example):
    """Require pre-attempt observations even for abstaining/failed/unavailable checks."""
    if contract.resource_manifest is None:
        return
    expected = contract.resource_manifest
    expected.require_candidates(a.verifier_name for a in example.attempts)
    for attempt in example.attempts:
        if attempt.observed_resources_json is None:
            raise ValueError("missing observed resources for " + attempt.verifier_name)
        observation = VerifierResources.model_validate_json(attempt.observed_resources_json, strict=True)
        expected.require_observation(observation)
