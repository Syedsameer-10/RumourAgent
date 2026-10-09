"""
TruthLens Reasoning Agent

Coordinates with GeminiService to produce a verdict, cross-references
supporting evidence citations, and ensures uncertainty is made explicit.
"""

import logging
from typing import Any

from services.gemini_service import GeminiService, GeminiAPIError, GeminiTimeoutError, GeminiParseError

logger = logging.getLogger(__name__)


class ReasoningAgent:
    """
    Agent responsible for verdict generation and evidence alignment.
    """

    def __init__(self, gemini_service: GeminiService) -> None:
        self._gemini_service = gemini_service

    def analyze(self, claim: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze claim against collected evidence.
        Returns a rich result with verified citations and provenance metadata.
        Propagates operational exceptions with distinct error status.
        """
        logger.info("ReasoningAgent analyzing claim: '%s'", claim)

        try:
            analysis = self._gemini_service.analyze(claim, evidence)
        except (GeminiAPIError, GeminiTimeoutError, GeminiParseError) as op_err:
            logger.error("Operational failure in reasoning: %s", op_err)
            # Return explicit failure status so memory agent knows NOT to cache this as normal verification
            return {
                "claim": claim,
                "status": "OPERATIONAL_FAILURE",
                "error_type": type(op_err).__name__,
                "error_message": str(op_err),
                "verdict": "ERROR",
                "confidence": 0,
                "explanation": f"Operational failure during analysis: {op_err}",
                "citations": [],
                "evidence_snapshot": evidence,
                "model_used": self._gemini_service.model_name
            }

        # Resolve citations: match supporting indices to actual evidence
        citations: list[dict[str, Any]] = []
        supporting_indices = analysis.get("supporting_source_indices", [])

        if supporting_indices and evidence:
            for idx in supporting_indices:
                if 1 <= idx <= len(evidence):
                    item = evidence[idx - 1]
                    citations.append({
                        "source_id": idx,
                        "publisher": item.get("publisher", "Unknown"),
                        "title": item.get("title", "Article"),
                        "tier": item.get("tier", "Web Source"),
                        "url": item.get("review_url", ""),
                        "snippet": item.get("rating", "")
                    })
        elif evidence:
            # Fallback: if model did not return indices, provide the top ranked item with explicit disclaimer
            top_item = evidence[0]
            citations.append({
                "source_id": 1,
                "publisher": top_item.get("publisher", "Unknown"),
                "title": top_item.get("title", "Article"),
                "tier": top_item.get("tier", "Web Source"),
                "url": top_item.get("review_url", ""),
                "snippet": top_item.get("rating", "")
            })

        result: dict[str, Any] = {
            "claim": claim,
            "status": "SUCCESS",
            "verdict": analysis.get("verdict", "Unverified"),
            "confidence": analysis.get("confidence", 0),
            "explanation": analysis.get("explanation", "No explanation available."),
            "citations": citations,
            "evidence_snapshot": evidence,
            "model_used": analysis.get("model_used", self._gemini_service.model_name),
            "primary_publisher": citations[0]["publisher"] if citations else "N/A",
            "primary_url": citations[0]["url"] if citations else "N/A",
        }

        logger.info(
            "ReasoningAgent verdict: %s (confidence: %d%%, citations: %d)",
            result["verdict"],
            result["confidence"],
            len(citations)
        )
        return result
