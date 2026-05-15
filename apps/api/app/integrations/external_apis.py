from __future__ import annotations

import httpx

from app.config.settings import settings
from app.integrations.financial_filings import SECFilingsClient
from app.integrations.web_search import WebSearchClient


class SanctionsProvider:
    def screen(self, supplier: dict) -> dict:
        if settings.sanctions_provider_base_url and settings.sanctions_provider_api_key:
            response = httpx.post(
                settings.sanctions_provider_base_url.rstrip("/") + "/screen",
                headers={"Authorization": f"Bearer {settings.sanctions_provider_api_key}"},
                json={
                    "name": supplier.get("legal_name"),
                    "country": supplier.get("country"),
                    "tax_id": supplier.get("tax_id"),
                    "registration_number": supplier.get("registration_number"),
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "source": data.get("source", "configured_sanctions_provider"),
                "result_type": data.get("result_type", "provider_result"),
                "signal": data.get("signal", "Sanctions provider returned a reviewable result"),
                "severity": data.get("severity", "medium"),
                "confidence": float(data.get("confidence", 0.75)),
                "raw": data,
            }
        return {
            "source": "Configured sanctions provider stub",
            "result_type": "watchlist_candidate",
            "signal": "Potential regulatory notice candidate match",
            "severity": "high",
            "confidence": 0.86,
        }


class CreditProvider:
    def __init__(self, filings_client: SECFilingsClient | None = None):
        self.filings_client = filings_client or SECFilingsClient()

    def lookup(self, supplier: dict) -> dict:
        try:
            filings = self.filings_client.search_company_filings(supplier)
        except Exception as exc:
            filings = {
                "source": "sec_edgar",
                "found": False,
                "signal": f"SEC filing lookup failed: {exc}",
                "severity": "medium",
                "confidence": 0.5,
                "filings": [],
            }
        if filings.get("found"):
            return {
                "source": "SEC EDGAR",
                "signal": "Recent SEC filings found for configured supplier CIK",
                "severity": "low",
                "confidence": 0.75,
                "raw": filings,
            }
        return {
            "source": "Financial filing fallback",
            "signal": "Moderate credit and liquidity risk signal",
            "severity": "medium",
            "confidence": 0.76,
            "raw": filings,
        }


class NewsProvider:
    def __init__(self, search_client: WebSearchClient | None = None):
        self.search_client = search_client or WebSearchClient()

    def search(self, supplier: dict) -> dict:
        query = f'"{supplier.get("legal_name")}" adverse news regulatory litigation supplier risk'
        if settings.news_api_key:
            response = httpx.get(
                "https://newsapi.org/v2/everything",
                params={"q": query, "apiKey": settings.news_api_key, "pageSize": 5, "sortBy": "publishedAt"},
                timeout=15,
            )
            response.raise_for_status()
            articles = response.json().get("articles", [])
            if articles:
                return {
                    "source": "NewsAPI",
                    "signal": "Recent news articles found for supplier review",
                    "severity": "medium",
                    "confidence": 0.74,
                    "raw": {"articles": articles[:5]},
                }
        results = self.search_client.search(query)
        if results and results[0].get("source") != "local_fallback":
            return {
                "source": results[0].get("source", "web_search"),
                "signal": "Web search returned supplier news results for review",
                "severity": "medium",
                "confidence": 0.72,
                "raw": {"results": results},
            }
        return {
            "source": "Configured news provider stub",
            "signal": "Negative media mention requires validation",
            "severity": "medium",
            "confidence": 0.72,
            "raw": {"results": results},
        }


class ESGProvider:
    def __init__(self, search_client: WebSearchClient | None = None):
        self.search_client = search_client or WebSearchClient()

    def search(self, supplier: dict) -> dict:
        query = f'"{supplier.get("legal_name")}" ESG labor environment controversy'
        results = self.search_client.search(query)
        if results and results[0].get("source") != "local_fallback":
            return {
                "source": results[0].get("source", "web_search"),
                "signal": "ESG web search returned results for supplier review",
                "severity": "medium",
                "confidence": 0.68,
                "raw": {"results": results},
            }
        return {
            "source": "Configured ESG provider stub",
            "signal": "No material ESG controversy found in configured sources",
            "severity": "low",
            "confidence": 0.68,
            "raw": {"results": results},
        }


class RouteRiskProvider:
    def lookup(self, supplier: dict) -> dict:
        return {
            "source": "Configured route risk provider stub",
            "signal": "No material logistics disruption detected",
            "severity": "low",
            "confidence": 0.65,
        }
