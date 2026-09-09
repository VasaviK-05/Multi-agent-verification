"""Application configuration (placeholder)."""

import os


class Settings:
    """Minimal settings loaded from environment variables."""

    APP_NAME: str = os.getenv("APP_NAME", "multi-agent-validation")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"


settings = Settings()
