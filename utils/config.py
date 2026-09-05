"""
TruthLens Configuration Module

Loads environment variables from .env and provides
validated access to API keys and project settings.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Centralized configuration loaded from environment variables."""

    def __init__(self) -> None:
        # Load .env from project root
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)

        self.google_factcheck_api_key: str = os.getenv("GOOGLE_FACTCHECK_API_KEY", "")
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

        # Project paths
        self.project_root: Path = Path(__file__).resolve().parent.parent
        self.data_dir: Path = self.project_root / "data"
        self.history_file: Path = self.data_dir / "history.json"

        logger.info("Configuration loaded from %s", env_path)

    def validate(self) -> None:
        """Validate that all required configuration values are present."""
        missing: list[str] = []

        if not self.gemini_api_key or self.gemini_api_key == "your_gemini_api_key_here":
            missing.append("GEMINI_API_KEY")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please set them in the .env file."
            )

        logger.info("Configuration validated successfully.")
