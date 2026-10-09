"""
TruthLens Memory Agent

Responsible for storing and searching verification results
in a local JSON file or SQLite with corruption protection,
atomic saving, and non-mutating record creation.
"""

import json
import logging
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from utils.helpers import get_timestamp

logger = logging.getLogger(__name__)


class MemoryAgent:
    """
    Agent responsible for verification caching and history auditing.

    Features:
    - Non-mutating records
    - Atomic JSON saving via temp file
    - Automatic quarantine of corrupt JSON files
    - Backward-compatible search and get_all
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
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            if not self._history_file.exists():
                self._write_file_atomically("[]")
                logger.info("Created history file: %s", self._history_file)
        except Exception as e:
            logger.error("Failed to ensure history file: %s", e)

    def _load_history(self) -> list[dict[str, Any]]:
        """
        Load verification history from disk with corruption quarantine.
        If the file is damaged, quarantine it to .corrupt-<timestamp> instead
        of silently wiping it.
        """
        if not self._history_file.exists():
            return []

        try:
            content = self._history_file.read_text(encoding="utf-8")
            data = json.loads(content)
            if isinstance(data, list):
                return data
            raise ValueError("History root is not a list")
        except (json.JSONDecodeError, ValueError) as err:
            logger.error("Corruption detected in %s: %s. Quarantining file.", self._history_file, err)
            self._quarantine_corrupt_file()
            return []
        except OSError as err:
            logger.error("OS error reading history file %s: %s", self._history_file, err)
            return []

    def _quarantine_corrupt_file(self) -> None:
        """Move damaged file to backup so it's not destroyed, and start fresh."""
        try:
            ts = get_timestamp().replace(" ", "_").replace(":", "-")
            backup_path = self._history_file.with_name(f"{self._history_file.stem}_corrupt_{ts}.json")
            shutil.copy2(self._history_file, backup_path)
            logger.warning("Corrupt history backed up to: %s", backup_path)
            self._write_file_atomically("[]")
        except Exception as e:
            logger.error("Failed to quarantine corrupt history file: %s", e)

    def _write_file_atomically(self, content: str) -> None:
        """Write content to a temp file in the same directory and atomic rename."""
        parent = self._history_file.parent
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", dir=parent, delete=False, encoding="utf-8") as tf:
            tf.write(content)
            temp_path = Path(tf.name)
        temp_path.replace(self._history_file)

    def _save_history(self, history: list[dict[str, Any]]) -> None:
        """Write full history list atomically."""
        try:
            data_str = json.dumps(history, indent=2, ensure_ascii=False)
            self._write_file_atomically(data_str)
        except Exception as e:
            logger.error("Failed to save history atomically: %s", e)
            raise

    def search(self, claim: str) -> dict[str, Any] | None:
        """
        Search for the most recent valid verification of a claim.
        Ignores operational failure records.

        Args:
            claim: The normalized claim text.

        Returns:
            The latest cached result dict or None.
        """
        history = self._load_history()
        target = claim.strip().lower()

        # Iterate reverse to get latest
        for entry in reversed(history):
            if entry.get("claim", "").strip().lower() == target:
                # Do not treat operational errors as cached answers
                if entry.get("status") in ("API_ERROR", "TIMEOUT", "PARSE_ERROR"):
                    continue
                logger.info("MemoryAgent found cached result for: '%s'", claim)
                return dict(entry)

        return None

    def save(self, result: dict[str, Any]) -> None:
        """
        Save a verification record without mutating the caller's dictionary.
        Do not cache operational errors.
        """
        # Safety check: do not cache operational failures
        if result.get("status") in ("API_ERROR", "TIMEOUT", "PARSE_ERROR"):
            logger.warning("Skipping cache save for operational error status: %s", result.get("status"))
            return

        history = self._load_history()

        # Create a clean shallow copy to avoid mutating caller's dict
        entry = dict(result)
        if "verified_at" not in entry or not entry["verified_at"]:
            entry["verified_at"] = get_timestamp()

        # Upsert: replace previous entry for same claim or append
        claim_lower = entry.get("claim", "").strip().lower()
        replaced = False
        for i in range(len(history) - 1, -1, -1):
            if history[i].get("claim", "").strip().lower() == claim_lower:
                history[i] = entry
                replaced = True
                break

        if not replaced:
            history.append(entry)

        self._save_history(history)
        logger.info("MemoryAgent successfully persisted verification for: '%s'", entry.get("claim"))

    def get_all(self) -> list[dict[str, Any]]:
        """Return all valid historical verification records."""
        return self._load_history()