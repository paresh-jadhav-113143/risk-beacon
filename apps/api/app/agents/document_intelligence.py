from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.agents.base import Agent, AgentContext, AgentOutput
from app.integrations.llm import LLMClient
from app.integrations.ocr import OCRClient


class DocumentIntelligenceAgent(Agent):
    name = "Document Intelligence Agent"

    def __init__(self, ocr_client: OCRClient | None = None, llm_client: LLMClient | None = None):
        self.ocr_client = ocr_client or OCRClient()
        self.llm_client = llm_client or LLMClient()

    def run(self, context: AgentContext) -> AgentOutput:
        document_results = self.ocr_client.extract_documents(context.documents)
        low_confidence = [doc for doc in document_results if doc["confidence"] < 0.75]
        extracted_facts = []
        risk_signals = []
        evidence_sources = []
        enriched_results = []
        supplier = context.supplier
        for result in document_results:
            deterministic_fields = _extract_fields(result)
            llm_result = _extract_fields_with_llm(self.llm_client, result, deterministic_fields)
            fields = _merge_fields(deterministic_fields, llm_result["fields"])
            comparisons = _compare_fields(fields, supplier)
            enriched_results.append(
                {
                    **result,
                    "extracted_fields": fields,
                    "profile_comparisons": comparisons,
                    "llm_extraction": llm_result["metadata"],
                }
            )
            evidence_sources.append(
                {
                    "source_type": "document",
                    "name": f"{result['document_type']} extraction",
                    "credibility_score": result["confidence"],
                    "metadata": {
                        "document_id": result["document_id"],
                        "provider": result["provider"],
                        "status": result["status"],
                        "field_count": len(fields),
                        "llm_provider": llm_result["metadata"]["provider"],
                    },
                }
            )
            for field in fields:
                extracted_facts.append(
                    {
                        "field": field["field_name"],
                        "value": field["field_value"],
                        "document_id": result["document_id"],
                        "confidence": field["confidence"],
                        "source_text": field.get("source_text"),
                    }
                )
            for comparison in comparisons:
                if comparison["status"] == "mismatch":
                    risk_signals.append(
                        {
                            "category": "authenticity",
                            "signal": f"Document field mismatch: {comparison['field_name']}",
                            "severity": "medium",
                            "confidence": comparison["confidence"],
                            "interpretation": (
                                f"Extracted value '{comparison['document_value']}' does not match supplier profile "
                                f"value '{comparison['profile_value']}'."
                            ),
                            "recommended_action": "Risk Analyst should validate the source document and supplier profile.",
                        }
                    )
            if result["status"] != "extracted":
                risk_signals.append(
                    {
                        "category": "operational",
                        "signal": f"{result['document_type']} could not be fully extracted",
                        "severity": "medium",
                        "confidence": 0.72,
                        "interpretation": "OCR or structured extraction did not produce enough text for reliable validation.",
                        "recommended_action": "Ask Supplier Admin to upload a readable document or provide a text sidecar for MVP OCR.",
                    }
                )
            if not fields and result["document_type"] in REQUIRED_FIELDS_BY_TYPE:
                risk_signals.append(
                    {
                        "category": "anomaly",
                        "signal": f"No expected fields extracted from {result['document_type']}",
                        "severity": "medium",
                        "confidence": 0.74,
                        "interpretation": "The document type normally contains structured fields, but extraction returned none.",
                        "recommended_action": "Risk Analyst should review document quality and authenticity.",
                    }
                )
        return AgentOutput(
            agent_name=self.name,
            confidence=0.9,
            extracted_facts=extracted_facts,
            evidence_sources=evidence_sources,
            risk_signals=risk_signals,
            payload={"document_results": enriched_results},
            warnings=[
                {"warning_code": "LOW_CONFIDENCE_DOCUMENT", "document_id": doc["document_id"]}
                for doc in low_confidence
            ],
            next_actions=[{"action": "entity_resolution"}],
        )


REQUIRED_FIELDS_BY_TYPE = {
    "business_registration": ["legal_name", "registration_number", "country"],
    "tax_certificate": ["tax_id", "legal_name"],
    "bank_letter": ["legal_name"],
    "financial_statement": ["legal_name"],
    "sustainability_certificate": ["legal_name"],
    "insurance_certificate": ["legal_name"],
    "quality_certificate": ["legal_name"],
}

FIELD_PATTERNS = {
    "legal_name": [r"(?:legal name|company name|supplier name|entity name)\s*[:\-]\s*(.+)"],
    "registration_number": [r"(?:registration(?: no\.?| number)?|cin)\s*[:\-]\s*([A-Z0-9\-\/]+)"],
    "tax_id": [r"(?:tax id|gstin|vat|tin)\s*[:\-]\s*([A-Z0-9\-\/]+)"],
    "country": [r"(?:country)\s*[:\-]\s*([A-Za-z ]{2,64})"],
    "website": [r"(?:website|url)\s*[:\-]\s*(https?://\S+|www\.\S+)"],
    "industry": [r"(?:industry)\s*[:\-]\s*(.+)"],
}

LLM_EXTRACTION_PROMPT = """
You extract supplier onboarding document fields from OCR text.
Return only valid JSON with this schema:
{
  "provider": "openai_langchain",
  "summary": "short factual summary",
  "extracted_fields": [
    {
      "field_name": "legal_name|registration_number|tax_id|country|website|industry",
      "field_value": "normalized value",
      "confidence": 0.0,
      "source_text": "short supporting text"
    }
  ],
  "warnings": []
}
Use only facts present in OCR text. Do not invent missing values.
"""


def _extract_fields(result: dict) -> list[dict]:
    text = result.get("text", "")
    if not text.strip():
        return []
    fields = []
    wanted = REQUIRED_FIELDS_BY_TYPE.get(result["document_type"], list(FIELD_PATTERNS))
    for field_name in wanted:
        for pattern in FIELD_PATTERNS.get(field_name, []):
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = _clean_value(match.group(1))
                if value:
                    fields.append(
                        {
                            "field_name": field_name,
                            "field_value": value,
                            "confidence": _field_confidence(result["confidence"], field_name, value, match.group(0)),
                            "source_text": match.group(0)[:240],
                        }
                    )
                break
    return fields


def _extract_fields_with_llm(llm_client: LLMClient, result: dict, deterministic_fields: list[dict]) -> dict:
    text = result.get("text", "")
    if not text.strip():
        return {
            "fields": [],
            "metadata": {"provider": "not_invoked", "reason": "empty_ocr_text"},
        }
    payload = {
        "document_id": result["document_id"],
        "document_type": result["document_type"],
        "ocr_provider": result["provider"],
        "ocr_confidence": result["confidence"],
        "ocr_text": text[:8000],
        "deterministic_fields": deterministic_fields,
        "required_fields": REQUIRED_FIELDS_BY_TYPE.get(result["document_type"], []),
    }
    response = llm_client.extract_structured_json(LLM_EXTRACTION_PROMPT, payload)
    provider = response.get("provider", "unknown")
    raw_fields = response.get("extracted_fields", []) if isinstance(response, dict) else []
    fields = []
    for field in raw_fields:
        normalized = _normalize_llm_field(field, result["confidence"])
        if normalized:
            fields.append(normalized)
    return {
        "fields": fields,
        "metadata": {
            "provider": provider,
            "field_count": len(fields),
            "summary": response.get("summary") if isinstance(response, dict) else None,
            "warnings": response.get("warnings", []) if isinstance(response, dict) else [],
        },
    }


def _normalize_llm_field(field: dict, document_confidence: float) -> dict | None:
    field_name = str(field.get("field_name", "")).strip()
    field_value = str(field.get("field_value") or field.get("value") or "").strip()
    if field_name not in FIELD_PATTERNS or not field_value:
        return None
    try:
        llm_confidence = float(field.get("confidence", document_confidence))
    except (TypeError, ValueError):
        llm_confidence = document_confidence
    confidence = round(min(max(llm_confidence, 0.35), document_confidence, 0.95), 2)
    return {
        "field_name": field_name,
        "field_value": _clean_value(field_value),
        "confidence": confidence,
        "source_text": str(field.get("source_text") or "")[:240],
        "extraction_method": "llm_structured_extract",
    }


def _merge_fields(deterministic_fields: list[dict], llm_fields: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for field in deterministic_fields:
        merged[field["field_name"]] = {**field, "extraction_method": "deterministic_pattern"}
    for field in llm_fields:
        existing = merged.get(field["field_name"])
        if not existing or field["confidence"] > existing["confidence"]:
            merged[field["field_name"]] = field
    return list(merged.values())


def _compare_fields(fields: list[dict], supplier: dict) -> list[dict]:
    comparable = {"legal_name", "registration_number", "tax_id", "country", "website", "industry"}
    comparisons = []
    for field in fields:
        field_name = field["field_name"]
        profile_value = supplier.get(field_name)
        if field_name not in comparable or not profile_value:
            continue
        score = _similarity(str(field["field_value"]), str(profile_value))
        comparisons.append(
            {
                "field_name": field_name,
                "document_value": field["field_value"],
                "profile_value": profile_value,
                "match_score": score,
                "status": "match" if score >= 0.82 else "mismatch",
                "confidence": round(min(field["confidence"], max(0.65, 1 - score / 2)), 2),
            }
        )
    return comparisons


def _clean_value(value: str) -> str:
    return value.strip().strip(" .;,")


def _field_confidence(document_confidence: float, field_name: str, value: str, source_text: str) -> float:
    score = document_confidence * 0.72
    score += min(len(value.strip()) / 80, 1.0) * 0.08
    score += 0.08 if field_name in source_text.lower().replace(" ", "_") or field_name.replace("_", " ") in source_text.lower() else 0.03
    if field_name in {"registration_number", "tax_id"} and re.fullmatch(r"[A-Z0-9\-\/]{6,}", value.strip(), re.IGNORECASE):
        score += 0.08
    if field_name == "website" and value.lower().startswith(("http://", "https://", "www.")):
        score += 0.08
    return round(min(max(score, 0.35), 0.95), 2)


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _normalize(left), _normalize(right)).ratio()


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())
