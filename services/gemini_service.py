"""
TruthLens Gemini Service

Wraps the Google Gemini API to analyze fact-check evidence
and produce a structured verdict with reasoning.
"""

import json
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Gemini API endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


class GeminiService:
    """Service layer for the Google Gemini API."""

    def __init__(self, api_key: str) -> None:
        """
        Initialize the Gemini Service.

        Args:
            api_key: Gemini API key from Google AI Studio.
        """
        self._api_key = api_key

    def analyze(self, claim: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Send claim and evidence to Gemini for analysis and verdict generation.

        Args:
            claim: The normalized claim text.
            evidence: List of evidence dicts from the Fact Check Service.

        Returns:
            A dictionary containing:
                - verdict: The final verdict (e.g., "True", "False", "Partially True", "Unverified")
                - confidence: Confidence score as an integer (0-100)
                - explanation: Detailed reasoning behind the verdict
        """
        prompt = self._build_prompt(claim, evidence)

        try:
            logger.info("Sending claim to Gemini for analysis: '%s'", claim)

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "application/json",
                }
            }

            response = requests.post(
                f"{GEMINI_API_URL}?key={self._api_key}",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            generated_text = self._extract_text(data)
            result = self._parse_response(generated_text)

            logger.info("Gemini analysis complete. Verdict: %s", result.get("verdict"))
            return result

        except requests.exceptions.HTTPError as e:
            logger.error("Gemini API HTTP error: %s", e)
            return self._default_result("API error occurred during analysis.")
        except requests.exceptions.ConnectionError as e:
            logger.error("Gemini API connection error: %s", e)
            return self._default_result("Could not connect to Gemini API.")
        except requests.exceptions.Timeout:
            logger.error("Gemini API request timed out.")
            return self._default_result("Gemini API request timed out.")
        except Exception as e:
            logger.error("Unexpected error in Gemini Service: %s", e)
            return self._default_result(f"Unexpected error: {e}")

    def _build_prompt(self, claim: str, evidence: list[dict[str, Any]]) -> str:
        """Build the analysis prompt for Gemini."""
        evidence_text = ""
        if evidence:
            for i, item in enumerate(evidence, 1):
                evidence_text += (
                    f"\nEvidence {i}:\n"
                    f"  Claim: {item.get('claim_text', 'N/A')}\n"
                    f"  Publisher: {item.get('publisher', 'N/A')}\n"
                    f"  Rating: {item.get('rating', 'N/A')}\n"
                    f"  Title: {item.get('title', 'N/A')}\n"
                    f"  URL: {item.get('review_url', 'N/A')}\n"
                )
        else:
            evidence_text = "\nNo fact-check evidence was found for this claim.\n"

        prompt = f"""You are a strict fact-checking analyst. Your job is to determine whether the following claim is TRUE or FALSE based on present-day, commonly accepted facts.

Claim: "{claim}"

Web search results for context:
{evidence_text}

IMPORTANT RULES:
- Evaluate the claim as a statement about CURRENT, commonly accepted facts.
- Do NOT use obscure historical, technical, or edge-case exceptions to justify a claim that is clearly wrong by common understanding.
- If a claim contradicts well-established facts (e.g., "the earth is flat", "a week has 8 days"), mark it as FALSE with high confidence.
- Use the web search results as supporting context, but also use your own knowledge of established facts.
- Be DECISIVE. Avoid "Partially True" unless the claim genuinely contains both true and false elements.

Provide your analysis in the following JSON format only. Do not include any other text outside the JSON:

{{
    "verdict": "<True | False | Partially True | Misleading | Unverified>",
    "confidence": <integer from 0 to 100>,
    "explanation": "<A clear, concise explanation of your reasoning in 2-4 sentences>"
}}

Verdict guidelines:
- TRUE: The claim is factually correct based on current knowledge.
- FALSE: The claim contradicts established facts.
- PARTIALLY TRUE: The claim contains a mix of accurate and inaccurate elements (use sparingly).
- MISLEADING: The claim is technically true but presented in a deceptive way.
- UNVERIFIED: There is genuinely insufficient information to determine truth or falsehood.
"""
        return prompt

    def _extract_text(self, data: dict[str, Any]) -> str:
        """Extract generated text from the Gemini API response."""
        try:
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        except (IndexError, KeyError) as e:
            logger.error("Failed to extract text from Gemini response: %s", e)

        return ""

    def _parse_response(self, text: str) -> dict[str, Any]:
        """
        Parse Gemini's response text into a structured result dict.

        Handles markdown code fences and falls back to regex extraction
        if strict JSON parsing fails.
        """
        import re

        # Strip markdown code fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Remove opening fence (e.g., ```json or ```)
            first_newline = cleaned.index("\n")
            cleaned = cleaned[first_newline + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Attempt strict JSON parsing
        try:
            result = json.loads(cleaned)
            return {
                "verdict": result.get("verdict", "Unverified"),
                "confidence": int(result.get("confidence", 0)),
                "explanation": result.get("explanation", "No explanation provided."),
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Strict JSON parse failed: %s. Trying regex fallback.", e)

        # Fallback: extract fields with regex
        try:
            verdict_match = re.search(r'"verdict"\s*:\s*"([^"]+)"', cleaned)
            confidence_match = re.search(r'"confidence"\s*:\s*(\d+)', cleaned)
            explanation_match = re.search(r'"explanation"\s*:\s*"((?:[^"\\]|\\.)*)', cleaned)

            if verdict_match:
                return {
                    "verdict": verdict_match.group(1),
                    "confidence": int(confidence_match.group(1)) if confidence_match else 50,
                    "explanation": explanation_match.group(1) if explanation_match else "Analysis completed but explanation was truncated.",
                }
        except Exception as fallback_err:
            logger.warning("Regex fallback also failed: %s", fallback_err)

        logger.debug("Raw response: %s", text)
        return self._default_result("Could not parse AI analysis response.")

    @staticmethod
    def _default_result(explanation: str) -> dict[str, Any]:
        """Return a safe default result when analysis fails."""
        return {
            "verdict": "Unverified",
            "confidence": 0,
            "explanation": explanation,
        }
