"""
TruthLens Claim Agent

Responsible for cleaning and normalizing user input
before it enters the verification pipeline.
"""

import re
import logging

logger = logging.getLogger(__name__)


class ClaimAgent:
    """
    Agent responsible for input normalization.

    Takes raw user input and produces a clean, normalized
    claim string suitable for searching and caching.
    """

    def process(self, raw_input: str) -> str:
        """
        Clean and normalize the raw user input.

        Steps:
            1. Strip leading/trailing whitespace
            2. Collapse multiple spaces into one
            3. Remove excessive punctuation noise
            4. Normalize to lowercase for consistent matching

        Args:
            raw_input: The raw rumour text entered by the user.

        Returns:
            A cleaned, normalized claim string.
        """
        if not raw_input or not raw_input.strip():
            logger.warning("ClaimAgent received empty input.")
            return ""

        # Strip whitespace
        claim = raw_input.strip()

        # Collapse multiple spaces into single space
        claim = re.sub(r"\s+", " ", claim)

        # Remove repeated punctuation (e.g., "!!!" -> "!", "???" -> "?")
        claim = re.sub(r"([!?.])\1+", r"\1", claim)

        # Normalize to lowercase for consistent matching/caching
        claim = claim.lower()

        logger.info("ClaimAgent normalized input: '%s'", claim)
        return claim
