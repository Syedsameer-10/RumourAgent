"""
TruthLens Reasoning Agent

Responsible for analyzing collected evidence and producing
a final verdict with confidence score and explanation.
"""

import logging
from typing import Any

from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class ReasoningAgent:
    """
    Agent responsible for verdict generation.

    Takes a claim and its evidence, delegates analysis to the
    GeminiService, and assembles the final verification result.
    """

    def __init__(self, gemini_service: GeminiService) -> None:
        """
        Initialize the Reasoning Agent.

        Args:
            gemini_service: An instance of GeminiService (injected).
        """
        self._gemini_service = gemini_service

    def analyze(self, claim: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze the claim against the collected evidence and produce a verdict.

        Args:
            claim: The normalized claim text.
            evidence: List of evidence dicts from the EvidenceAgent.

        Returns:
            A complete verification result dictionary containing:
                - claim: The original claim text
                - verdict: Final verdict string
                - confidence: Confidence score (0-100)
                - explanation: Reasoning behind the verdict
                - publisher: Primary publisher name (from evidence)
                - source_url: Primary source URL (from evidence)
        """
        logger.info("ReasoningAgent analyzing claim: '%s'", claim)

        # Get AI analysis from Gemini
        analysis = self._gemini_service.analyze(claim, evidence)

        # Extract primary publisher and source URL from evidence
        publisher = "N/A"
        source_url = "N/A"
        if evidence:
            publisher = evidence[0].get("publisher", "N/A")
            source_url = evidence[0].get("review_url", "N/A")

        # Assemble the final result
        result: dict[str, Any] = {
            "claim": claim,
            "verdict": analysis.get("verdict", "Unverified"),
            "confidence": analysis.get("confidence", 0),
            "explanation": analysis.get("explanation", "No explanation available."),
            "publisher": publisher,
            "source_url": source_url,
        }

        logger.info(
            "ReasoningAgent verdict: %s (confidence: %d%%)",
            result["verdict"],
            result["confidence"],
        )
        return result
