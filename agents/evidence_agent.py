"""
TruthLens Evidence Agent

Responsible for retrieving fact-check evidence
from external sources via the service layer.
"""

import logging
from typing import Any

from services.factcheck_service import FactCheckService

logger = logging.getLogger(__name__)


class EvidenceAgent:
    """
    Agent responsible for evidence retrieval.

    Delegates to the FactCheckService to gather evidence
    related to a given claim. Never calls external APIs directly.
    """

    def __init__(self, factcheck_service: FactCheckService) -> None:
        """
        Initialize the Evidence Agent.

        Args:
            factcheck_service: An instance of FactCheckService (injected).
        """
        self._factcheck_service = factcheck_service

    def gather(self, claim: str) -> list[dict[str, Any]]:
        """
        Gather fact-check evidence for the given claim.

        Args:
            claim: The normalized claim text.

        Returns:
            A list of evidence dictionaries from fact-checking sources.
            Returns an empty list if no evidence is found.
        """
        logger.info("EvidenceAgent gathering evidence for: '%s'", claim)

        evidence = self._factcheck_service.search(claim)

        if evidence:
            logger.info(
                "EvidenceAgent collected %d piece(s) of evidence.", len(evidence)
            )
        else:
            logger.warning("EvidenceAgent found no evidence for: '%s'", claim)

        return evidence
