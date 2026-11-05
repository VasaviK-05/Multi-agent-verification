"""Load and validate a server-configured game deployment."""

import json
import os
import random
from pathlib import Path

from app.game.artifacts import (
    DeploymentEpisode,
    InMemoryPolicyProvider,
    PolicyArtifact,
)
from app.game.execution import GameRuntime
from app.game.prototype_bundle import load_prototype
from app.game.offline.recording_adapters import ProjectObserver
from app.game.question_routing import QuestionPolicyRouter
from app.utils.config import settings

_REFERENCE_ARTIFACT_ID = "ee32392c870fba30b08b4f7509af645019d9f8b92dc7c39bafeceb8207745c8f"

class PrototypeGameRuntime:
    """Run a validated prototype bundle through its task-aware router."""

    def __init__(self, prototype) -> None:
        self._prototype = prototype
        self._router = prototype.router()
        self._provider = prototype.provider()
        self._rng = random.Random()

    def run(self, selector, analysis, request, validation_id):
        return self._router.run(
            selector,
            analysis,
            request,
            validation_id,
            provider=self._provider,
            rng=self._rng,
            resource_observer=ProjectObserver(),
            allow_synthetic_for_tests=False,
        )


class FlexiblePolicyGameRuntime:
    """Explicit flexible-policy dispatcher with route-specific reviewed factories."""

    def __init__(self, package_path) -> None:
        from app.benchmark.project_adapter import AdapterConfiguration, ROOT, read_json
        from scripts.reconciliation import load_bundle

        published_path = (ROOT / "reconciliation/policies.json").resolve()
        configured_path = Path(package_path).expanduser().resolve()
        if configured_path != published_path:
            raise ValueError("flexible runtime accepts only the reviewed reconciliation package")
        self._configuration, self._provider, self._compound = load_bundle()
        self._router = QuestionPolicyRouter(self._configuration)
        self._rng = random.Random()
        self._bundle_id = json.loads(published_path.read_text(encoding="utf-8"))["bundle_id"]
        adapter_path = (settings.GAME_FLEXIBLE_ADAPTER_CONFIG_PATH
                        or os.environ.get("VERIFIER_COLLECTION_ADAPTER_CONFIG", "adapter.json"))
        self._adapter = AdapterConfiguration.model_validate(read_json(adapter_path))

    def _adapter_for(self, route_name):
        binding_setting = {
            "factual": settings.GAME_FLEXIBLE_FACTUAL_RELOCATION_BINDING_PATH,
            "compound": settings.GAME_FLEXIBLE_COMPOUND_RELOCATION_BINDING_PATH,
            "reference": settings.GAME_FLEXIBLE_REFERENCE_RELOCATION_BINDING_PATH,
        }.get(route_name)
        if route_name == "arithmetic":
            binding_setting = ""
        if route_name not in {"arithmetic", "factual", "compound", "reference"}:
            raise ValueError("unknown flexible route resource scope")
        # Never inherit a generic relocation binding from the collector adapter.
        # Each route scope must opt into its own reviewed binding explicitly.
        return self._adapter.model_copy(update={
            "resource_relocation_binding": binding_setting or None,
        })

    def run(self, selector, analysis, request, validation_id):
        from app.game.component_execution import unavailable
        from app.game.offline.reconciled_resources import create_scoped
        from app.game.offline.singleton_compatibility import create_singleton, transfer_for
        from scripts.reconciliation import selector_for

        kind, key, resolved = self._router.resolve(request.question, request.context)
        routing_signature = list(key) if isinstance(key, tuple) else key
        if resolved is None:
            run = self._router.run(
                selector, request, validation_id, provider=self._provider,
                rng=self._rng, resource_observer=None, allow_synthetic_for_tests=False,
            )
            run.summary.update(execution_mode="flexible_game", policy_bundle_id=self._bundle_id,
                               policy_category=kind, routing_signature=routing_signature,
                               validation_id=validation_id)
            return run

        route = resolved[0]
        observer = None
        actual_selector = selector
        artifact = None
        preflight_resource_manifest_id = None
        preflight_compatibility_proof = None
        try:
            if kind == "component":
                policy_id = self._compound.policy_id
                artifact_id = None
                pool, observer = create_scoped(self._adapter_for("compound"), self._compound)
                actual_selector = selector_for(pool)
            elif kind == "atomic":
                episode = route[3]
                matches = [candidate for candidate in self._provider.snapshot()
                           if candidate.context == episode.context
                           and candidate.contract == episode.contract
                           and candidate.execution_configuration_id == episode.execution_configuration_id]
                if len(matches) != 1:
                    raise ValueError("atomic route did not resolve to one packaged artifact")
                artifact = matches[0]
                artifact_id, policy_id = artifact.artifact_id, artifact.policy.policy_id
                if artifact.artifact_id == _REFERENCE_ARTIFACT_ID:
                    from app.game.offline.reference_compatibility import create_reference
                    pool, observer = create_reference(self._adapter_for("reference"), artifact)
                    actual_selector = selector_for(pool)
                else:
                    binding = transfer_for(artifact)[1]
                    route_name = "arithmetic" if binding["selected"] == "rule" else "factual"
                    factory_config = self._adapter_for(route_name)
                    actual_selector, observer = create_singleton(factory_config, artifact)
            else:
                raise ValueError("unsupported registered flexible route kind")
            snapshot_for = getattr(observer, "snapshot_for", None)
            if snapshot_for is None:
                raise ValueError("route factory observer cannot attest its actual selector")
            observed = snapshot_for(actual_selector)
            preflight_resource_manifest_id = observed.manifest_id
            preflight_compatibility_proof = getattr(observer, "last_proof", None)
        except (OSError, TypeError, ValueError) as exc:
            run = unavailable("resource_incompatible: " + str(exc))
            run.summary.update(execution_mode="flexible_game", policy_bundle_id=self._bundle_id,
                               policy_category=kind, routing_signature=routing_signature,
                               policy_id=policy_id if "policy_id" in locals() else None,
                               artifact_id=artifact_id if "artifact_id" in locals() else None,
                               validation_id=validation_id)
            return run

        run = self._router.run(
            actual_selector, request, validation_id, provider=self._provider,
            rng=self._rng, resource_observer=observer,
            allow_synthetic_for_tests=False,
        )
        run.summary.setdefault('policy_execution_mode', run.summary.get('execution_mode'))
        run.summary['execution_mode'] = 'flexible_game'
        run.summary['policy_bundle_id'] = self._bundle_id
        run.summary['policy_category'] = kind
        run.summary['routing_signature'] = routing_signature
        run.summary['policy_id'] = policy_id
        run.summary['artifact_id'] = artifact_id
        run.summary['validation_id'] = validation_id
        run.summary['pre_dispatch_resource_manifest_id'] = preflight_resource_manifest_id
        run.summary['pre_dispatch_compatibility_proof'] = preflight_compatibility_proof
        return run

def create_game_runtime() -> GameRuntime | PrototypeGameRuntime | FlexiblePolicyGameRuntime:
    """Build a game runtime from a configured policy artifact or prototype bundle."""
    if settings.EXECUTION_MODE != "game":
        raise ValueError(
            "Game runtime can only be created when EXECUTION_MODE=game"
        )

    flexible_path = settings.GAME_FLEXIBLE_POLICY_PACKAGE_PATH
    bundle_path = settings.GAME_POLICY_BUNDLE_PATH
    artifact_path = settings.GAME_POLICY_ARTIFACT_PATH
    configured = [bool(flexible_path), bool(bundle_path), bool(artifact_path)]
    if sum(configured) > 1:
        raise ValueError("configure exactly one game policy package, bundle, or artifact")
    if flexible_path:
        path = Path(flexible_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Configured flexible policy package does not exist: {path}")
        return FlexiblePolicyGameRuntime(path)

    # Prefer the validated prototype bundle when configured.
    if bundle_path:
        path = Path(bundle_path).expanduser()

        if not path.is_dir():
            raise FileNotFoundError(
                f"Configured game policy bundle does not exist: {path}"
            )

        prototype = load_prototype(path)

        return PrototypeGameRuntime(prototype) 

    # Otherwise use the existing single-artifact deployment path.
    if not artifact_path:
        raise RuntimeError(
            "EXECUTION_MODE=game requires either "
            "GAME_POLICY_BUNDLE_PATH or GAME_POLICY_ARTIFACT_PATH"
        )

    path = Path(artifact_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(
            f"Configured game policy artifact does not exist: {path}"
        )

    try:
        artifact_data = json.loads(path.read_text(encoding="utf-8"))
        artifact = PolicyArtifact.model_validate(artifact_data)

        episode = DeploymentEpisode(
            episode_id=settings.GAME_EPISODE_ID,
            context=artifact.context,
            contract=artifact.contract,
            execution_configuration_id=artifact.execution_configuration_id,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            f"Invalid game deployment artifact at {path}: {exc}"
        ) from exc

    provider = InMemoryPolicyProvider((artifact,))

    return GameRuntime(
        provider=provider,
        episode=episode,
        rng=random.Random(),
        allow_synthetic_for_tests=False,
    )
