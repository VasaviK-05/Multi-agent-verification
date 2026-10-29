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
from app.utils.config import settings


def create_game_runtime() -> GameRuntime:
    """Build a game runtime from a validated deployment artifact."""
    if settings.EXECUTION_MODE != "game":
        raise ValueError(
            "Game runtime can only be created when EXECUTION_MODE=game"
        )

    artifact_path = settings.GAME_POLICY_ARTIFACT_PATH
    if not artifact_path:
        raise RuntimeError(
            "EXECUTION_MODE=game requires GAME_POLICY_ARTIFACT_PATH "
            "to point to a validated deployment artifact JSON file"
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
