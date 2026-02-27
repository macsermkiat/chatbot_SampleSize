"""Tavily search wrapper.

The ResearchGapAgentSearch node generates 3-5 search terms; this service
executes them in parallel and returns aggregated results matching the n8n
shape: {url, title, content, score}.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from tavily import AsyncTavilyClient

from app.config import settings


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    content: str
    score: float


async def search(queries: list[str], *, max_results: int = 5) -> list[SearchResult]:
    """Run *queries* against Tavily in parallel and return deduplicated results."""

    client = AsyncTavilyClient(api_key=settings.tavily_api_key)

    async def _single(query: str) -> list[dict]:
        response = await client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
        )
        return response.get("results", [])

    batches = await asyncio.gather(*[_single(q) for q in queries], return_exceptions=True)

    seen_urls: set[str] = set()
    results: list[SearchResult] = []

    for batch in batches:
        if isinstance(batch, Exception):
            continue
        for item in batch:
            url = item.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            results.append(
                SearchResult(
                    url=url,
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                )
            )

    # Sort by relevance score descending
    return sorted(results, key=lambda r: r.score, reverse=True)
