"""Load and validate a server-configured game deployment."""

import json
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
    """Explicit flexible-policy runtime using the orchestrator's live selector."""

    def __init__(self, package_path) -> None:
        from scripts.policy_package import load_runtime_candidate

        self._configuration, self._provider, self._compound, self._transfer, self._bundle_id = (
            load_runtime_candidate(package_path)
        )
        self._router = QuestionPolicyRouter(self._configuration)
        self._rng = random.Random()
        self._transfer_id = self._transfer['transfer_id']

    def run(self, selector, analysis, request, validation_id):
        # The selector is injected by ValidationOrchestrator and owns the exact
        # verifier instances that ProjectObserver attests for this request.
        observer = ProjectObserver(scoped_transfer_id=self._transfer_id)
        run = self._router.run(
            selector, request, validation_id, provider=self._provider,
            rng=self._rng, resource_observer=observer,
            resource_transfer=self._transfer, allow_synthetic_for_tests=False,
        )
        run.summary.setdefault('policy_execution_mode', run.summary.get('execution_mode'))
        run.summary['execution_mode'] = 'flexible_game'
        run.summary['policy_bundle_id'] = self._bundle_id
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
