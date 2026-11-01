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
            resource_observer=None,
            allow_synthetic_for_tests=False,
        )

def create_game_runtime() -> GameRuntime:
    """Build a game runtime from a configured policy artifact or prototype bundle."""
    if settings.EXECUTION_MODE != "game":
        raise ValueError(
            "Game runtime can only be created when EXECUTION_MODE=game"
        )

    # Prefer the validated prototype bundle when configured.
    bundle_path = settings.GAME_POLICY_BUNDLE_PATH
    if bundle_path:
        path = Path(bundle_path).expanduser()

        if not path.is_dir():
            raise FileNotFoundError(
                f"Configured game policy bundle does not exist: {path}"
            )

        prototype = load_prototype(path)

        return PrototypeGameRuntime(prototype) 

    # Otherwise use the existing single-artifact deployment path.
    artifact_path = settings.GAME_POLICY_ARTIFACT_PATH
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
