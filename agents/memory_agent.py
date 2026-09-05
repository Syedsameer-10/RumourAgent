"""
TruthLens Memory Agent

Responsible for searching and storing verification results
in a local JSON file to avoid redundant API calls.
"""

import json
import logging
from pathlib import Path
from typing import Any

from utils.helpers import get_timestamp

logger = logging.getLogger(__name__)


class MemoryAgent:
    """
    Agent responsible for verification caching.

    Reads and writes verification history to a JSON file.
    Auto-creates the file and parent directories if they do not exist.
    """

    def __init__(self, history_file: Path) -> None:
        """
        Initialize the Memory Agent.

        Args:
            history_file: Path to the history.json file.
        """
        self._history_file = history_file
        self._ensure_history_file()

    def _ensure_history_file(self) -> None:
        """Create the history file and parent directories if they don't exist."""
        self._history_file.parent.mkdir(parents=True, exist_ok=True)

        if not self._history_file.exists():
            self._history_file.write_text("[]", encoding="utf-8")
            logger.info("Created history file: %s", self._history_file)

    def _load_history(self) -> list[dict[str, Any]]:
        """Load the full verification history from disk."""
        try:
            content = self._history_file.read_text(encoding="utf-8")
            history = json.loads(content)
            return history if isinstance(history, list) else []
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load history file: %s", e)
            return []

    def _save_history(self, history: list[dict[str, Any]]) -> None:
        """Write the full verification history to disk."""
        try:
            self._history_file.write_text(
                json.dumps(history, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as e:
            logger.error("Failed to save history file: %s", e)

    def search(self, claim: str) -> dict[str, Any] | None:
        """
        Search for a previously verified claim in history.

        Args:
            claim: The normalized claim text to look up.

        Returns:
            The cached verification result dict, or None if not found.
        """
        history = self._load_history()

        for entry in history:
            if entry.get("claim", "").lower() == claim.lower():
                logger.info("MemoryAgent found cached result for: '%s'", claim)
                return entry

        logger.info("MemoryAgent found no cached result for: '%s'", claim)
        return None

    def save(self, result: dict[str, Any]) -> None:
        """
        Save a new verification result to history.

        Adds a timestamp and appends to the history file.

        Args:
            result: The complete verification result dictionary.
        """
        history = self._load_history()

        # Add timestamp
        result["verified_at"] = get_timestamp()

        history.append(result)
        self._save_history(history)

        logger.info("MemoryAgent saved verification for: '%s'", result.get("claim", ""))
