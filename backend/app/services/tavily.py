"""Tavily search wrapper.

The ResearchGapAgentSearch node generates 3-5 search terms; this service
executes them in parallel and returns aggregated results matching the n8n
shape: {url, title, content, score}.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from tavily import AsyncTavilyClient

from app.config import settings

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    content: str
    score: float



# High-quality medical / academic domains to prioritize.
# Tavily's include_domains biases results toward these sources,
# filtering out predatory journals and low-quality Q3/Q4 outlets.
MEDICAL_DOMAINS: list[str] = [
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "cochranelibrary.com",
    "who.int",
    "nejm.org",
    "thelancet.com",
    "bmj.com",
    "jamanetwork.com",
    "nature.com",
    "springer.com",
    "wiley.com",
    "sciencedirect.com",
    "academic.oup.com",
    "journals.plos.org",
    "frontiersin.org",
    "mdpi.com",
]


async def search(
    queries: list[str],
    *,
    max_results: int = 5,
    include_domains: list[str] | None = None,
) -> list[SearchResult]:
    """Run *queries* against Tavily in parallel and return deduplicated results.

    By default searches are scoped to high-quality medical/academic
    domains (PubMed, Cochrane, NEJM, Lancet, BMJ, JAMA, etc.).
    Pass ``include_domains=[]`` to disable domain filtering.
    """

    domains = MEDICAL_DOMAINS if include_domains is None else include_domains
    client = AsyncTavilyClient(api_key=settings.tavily_api_key)

    async def _single(query: str) -> list[dict]:
        kwargs: dict = {
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
        }
        if domains:
            kwargs["include_domains"] = domains
        response = await client.search(**kwargs)
        return response.get("results", [])

    batches = await asyncio.gather(*[_single(q) for q in queries], return_exceptions=True)

    seen_urls: set[str] = set()
    results: list[SearchResult] = []
    failed_count = 0

    for batch in batches:
        if isinstance(batch, Exception):
            failed_count += 1
            _logger.warning("Tavily search query failed: %s", batch)
            continue
        for item in batch:
            url = (item.get("url", "") or "").rstrip("/")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            results.append(
                SearchResult(
                    url=url,
                    title=item.get("title", "") or "",
                    content=item.get("content", "") or "",
                    score=item.get("score", 0.0) or 0.0,
                )
            )

    if failed_count == len(batches):
        _logger.error("All %d Tavily search queries failed", failed_count)

    # Sort by relevance score descending
    return sorted(results, key=lambda r: r.score, reverse=True)
