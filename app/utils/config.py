"""Application configuration."""

import os


class Settings:
    """Application settings loaded from environment variables."""

    APP_NAME: str = os.getenv("APP_NAME", "multi-agent-validation")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Server-controlled validation execution mode.
    EXECUTION_MODE: str = os.getenv("EXECUTION_MODE", "baseline").strip().lower()

    # Required when EXECUTION_MODE=game.
    GAME_POLICY_ARTIFACT_PATH: str = os.getenv(
        "GAME_POLICY_ARTIFACT_PATH", ""
    ).strip()

    GAME_EPISODE_ID: str = os.getenv("GAME_EPISODE_ID", "production-episode").strip()


settings = Settings()