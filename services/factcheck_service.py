"""
TruthLens Fact Check Service

Uses DuckDuckGo Search to find fact-check evidence
related to a given claim. No API key required.
"""

import logging
from typing import Any
from urllib.parse import urlparse

from ddgs import DDGS

logger = logging.getLogger(__name__)


class FactCheckService:
    """Service layer for web-based fact-check evidence retrieval."""

    def __init__(self, api_key: str = "") -> None:
        """
        Initialize the Fact Check Service.

        Args:
            api_key: Not used (kept for interface compatibility). DuckDuckGo requires no key.
        """
        self._ddgs = DDGS()

    def search(self, query: str) -> list[dict[str, Any]]:
        """
        Search DuckDuckGo for fact-check articles related to the claim.

        Appends 'fact check' to the query to target fact-checking sources.

        Args:
            query: The claim or rumour text to search for.

        Returns:
            A list of evidence dictionaries, each containing:
                - claim_text: The original search query
                - publisher: Source domain of the result
                - rating: Snippet from the fact-check article
                - review_url: URL to the full article
                - title: Title of the article
        """
        try:
            search_query = f"{query} fact check"
            logger.info("Searching DuckDuckGo for: '%s'", search_query)

            results = self._ddgs.text(
                query=search_query,
                max_results=5,
            )

            if not results:
                logger.info("No results found for: '%s'", query)
                return []

            evidence_list = self._parse_results(query, results)
            logger.info("Found %d result(s) for: '%s'", len(evidence_list), query)
            return evidence_list

        except Exception as e:
            logger.error("DuckDuckGo search error: %s", e)
            return []

    def _parse_results(self, query: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Parse DuckDuckGo search results into structured evidence dicts.

        Args:
            query: The original claim text.
            results: Raw results from DuckDuckGo.

        Returns:
            List of structured evidence dictionaries.
        """
        evidence_list: list[dict[str, Any]] = []

        for result in results:
            url = result.get("href", "")
            publisher = self._extract_domain(url)

            evidence = {
                "claim_text": query,
                "publisher": publisher,
                "rating": result.get("body", "No snippet available"),
                "review_url": url,
                "title": result.get("title", "No title"),
            }
            evidence_list.append(evidence)

        return evidence_list

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract a clean domain name from a URL."""
        try:
            domain = urlparse(url).netloc
            # Remove 'www.' prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain if domain else "Unknown"
        except Exception:
            return "Unknown"
