"""
TruthLens Fact Check Service

Retrieves, filters, and ranks evidence from:
1. Google Fact Check Tools API (Official ClaimReviews)
2. Live Web Search via DuckDuckGo (Ranked & scored news/journalism sources)

Preserves title, URL, publisher, snippet, retrieval date, and source tier.
"""

import logging
from typing import Any
from urllib.parse import urlparse
import requests
from ddgs import DDGS

from utils.helpers import get_timestamp

logger = logging.getLogger(__name__)

# Trusted domain lists for ranking
TRUSTED_FACTCHECK_DOMAINS = {
    "snopes.com", "politifact.com", "factcheck.org", "reuters.com",
    "apnews.com", "bbc.com", "bbc.co.uk", "afp.com", "fullfact.org",
    "boomlive.in", "altnews.in", "factly.in", "vishvasnews.com"
}

REPUTABLE_NEWS_DOMAINS = {
    "thehindu.com", "indianexpress.com", "ndtv.com", "hindustantimes.com",
    "nytimes.com", "washingtonpost.com", "theguardian.com", "aljazeera.com",
    "bloomberg.com", "nature.com", "who.int", "cdc.gov", "nasa.gov"
}


class FactCheckService:
    """Service layer for evidence retrieval, ranking, and citation enrichment."""

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key.strip() if api_key else ""
        self._ddgs = DDGS()

    def search(self, query: str) -> list[dict[str, Any]]:
        """
        Gather evidence from official fact-checks and live web search.
        Returns ranked evidence items with provenance metadata.
        """
        evidence_list: list[dict[str, Any]] = []

        # 1. Google Fact Check Tools API (Official ClaimReview)
        if self._api_key:
            evidence_list.extend(self._fetch_google_factchecks(query))

        # 2. Live Web Search (Multi-query retrieval)
        web_evidence = self._fetch_web_evidence(query)
        evidence_list.extend(web_evidence)

        # 3. Deduplicate by URL
        unique_evidence: list[dict[str, Any]] = []
        seen_urls = set()
        for item in evidence_list:
            u = item.get("review_url", "").strip()
            if u and u not in seen_urls:
                seen_urls.add(u)
                unique_evidence.append(item)
            elif not u:
                unique_evidence.append(item)

        # 4. Rank evidence: Tier 1 (Official Fact Check) > Tier 2 (Reputable News) > Tier 3 (General Web)
        ranked = sorted(unique_evidence, key=self._score_evidence, reverse=True)
        logger.info("Total ranked evidence pieces collected: %d", len(ranked))
        return ranked[:6]  # Return top 6 highest quality sources

    def _fetch_google_factchecks(self, query: str) -> list[dict[str, Any]]:
        """Query Google Fact Check Tools API."""
        items = []
        try:
            factcheck_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
            params = {
                "query": query,
                "key": self._api_key,
                "languageCode": "en",
            }
            resp = requests.get(factcheck_url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for claim_item in data.get("claims", []):
                    for review in claim_item.get("claimReview", []):
                        pub = review.get("publisher", {}).get("name", "Official Fact-Checker")
                        rating = review.get("textualRating", "Fact-checked")
                        url = review.get("url", "")
                        title = review.get("title", claim_item.get("text", query))
                        items.append({
                            "source_id": len(items) + 1,
                            "claim_text": claim_item.get("text", query),
                            "publisher": pub,
                            "tier": "Tier 1: Official ClaimReview",
                            "rating": f"Verdict by {pub}: '{rating}'",
                            "review_url": url,
                            "title": title,
                            "retrieved_at": get_timestamp(),
                            "is_official_factcheck": True,
                        })
            if items:
                logger.info("Found %d official ClaimReview records via Google Fact Check", len(items))
        except Exception as e:
            logger.warning("Google Fact Check API query failed (%s). Falling back.", e)
        return items

    def _fetch_web_evidence(self, query: str) -> list[dict[str, Any]]:
        """Fetch news & web results using DuckDuckGo with query variations."""
        raw_results = []
        queries = [f"{query} fact check", query]

        for q in queries:
            try:
                results = self._ddgs.text(q, max_results=4)
                if results:
                    raw_results.extend(results)
            except Exception as e:
                logger.error("DuckDuckGo search error on '%s': %s", q, e)

        items = []
        for r in raw_results:
            url = r.get("href", "")
            domain = self._extract_domain(url)
            tier = "Tier 2: Reputable News/Org" if domain in REPUTABLE_NEWS_DOMAINS or domain in TRUSTED_FACTCHECK_DOMAINS else "Tier 3: Web Search Snippet"

            items.append({
                "source_id": len(items) + 1,
                "claim_text": query,
                "publisher": domain,
                "tier": tier,
                "rating": r.get("body", "No snippet available"),
                "review_url": url,
                "title": r.get("title", "Article"),
                "retrieved_at": get_timestamp(),
                "is_official_factcheck": domain in TRUSTED_FACTCHECK_DOMAINS,
            })
        return items

    def _score_evidence(self, item: dict[str, Any]) -> int:
        """Assign ranking score based on source credibility."""
        score = 0
        if item.get("is_official_factcheck"):
            score += 100
        domain = item.get("publisher", "").lower()
        if domain in TRUSTED_FACTCHECK_DOMAINS:
            score += 50
        elif domain in REPUTABLE_NEWS_DOMAINS:
            score += 30
        if item.get("review_url"):
            score += 10
        return score

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain if domain else "Web Source"
        except Exception:
            return "Web Source"
