from __future__ import annotations

import urllib.parse

import httpx

from app.config.settings import settings


class WebSearchClient:
    def search(self, query: str, max_results: int = 5) -> list[dict]:
        if settings.tavily_api_key:
            return self._search_tavily(query, max_results)
        if settings.serpapi_api_key:
            return self._search_serpapi(query, max_results)
        return [
            {
                "title": "Web search not configured",
                "url": None,
                "snippet": "Set TAVILY_API_KEY or SERPAPI_API_KEY to enable live web search.",
                "source": "local_fallback",
            }
        ]

    def _search_tavily(self, query: str, max_results: int) -> list[dict]:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={"api_key": settings.tavily_api_key, "query": query, "max_results": max_results},
            timeout=15,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        return [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "snippet": item.get("content"),
                "source": "tavily",
            }
            for item in results
        ]

    def _search_serpapi(self, query: str, max_results: int) -> list[dict]:
        params = urllib.parse.urlencode(
            {"engine": "google", "q": query, "api_key": settings.serpapi_api_key, "num": max_results}
        )
        response = httpx.get(f"https://serpapi.com/search.json?{params}", timeout=15)
        response.raise_for_status()
        results = response.json().get("organic_results", [])[:max_results]
        return [
            {
                "title": item.get("title"),
                "url": item.get("link"),
                "snippet": item.get("snippet"),
                "source": "serpapi",
            }
            for item in results
        ]
