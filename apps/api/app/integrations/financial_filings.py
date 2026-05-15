from __future__ import annotations

import re

import httpx

from app.config.settings import settings


class SECFilingsClient:
    base_url = "https://data.sec.gov"

    def search_company_filings(self, supplier: dict) -> dict:
        cik = supplier.get("metadata_json", "")
        if isinstance(cik, str):
            match = re.search(r'"cik"\s*:\s*"?(\\d+)"?', cik)
            cik = match.group(1) if match else None
        if not cik:
            return {
                "source": "sec_edgar",
                "configured": True,
                "found": False,
                "signal": "No SEC CIK configured for supplier",
                "severity": "low",
                "confidence": 0.4,
                "filings": [],
            }
        cik_padded = str(cik).zfill(10)
        headers = {"User-Agent": settings.sec_user_agent}
        response = httpx.get(f"{self.base_url}/submissions/CIK{cik_padded}.json", headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])[:10]
        dates = recent.get("filingDate", [])[:10]
        filings = [{"form": form, "filing_date": dates[index] if index < len(dates) else None} for index, form in enumerate(forms)]
        return {
            "source": "sec_edgar",
            "configured": True,
            "found": True,
            "signal": "SEC filings found for configured supplier CIK",
            "severity": "low",
            "confidence": 0.75,
            "filings": filings,
        }
