from __future__ import annotations

from app.agents.base import Agent, AgentContext, AgentOutput
from app.integrations.external_apis import CreditProvider, ESGProvider, NewsProvider, RouteRiskProvider, SanctionsProvider


def _risk_output(agent_name: str, category: str, provider_result: dict, source_type: str) -> AgentOutput:
    severity = provider_result["severity"]
    signal = provider_result["signal"]
    confidence = provider_result["confidence"]
    risk_signals = []
    if severity != "low":
        risk_signals.append(
            {
                "category": category,
                "signal": signal,
                "severity": severity,
                "confidence": confidence,
                "interpretation": f"{signal}. Risk Analyst review is required before final decision.",
                "recommended_action": "Route to Risk Analyst for review",
            }
        )
    return AgentOutput(
        agent_name=agent_name,
        confidence=confidence,
        evidence_sources=[
            {
                "source_type": source_type,
                "name": provider_result["source"],
                "credibility_score": 0.82,
                "metadata": {"category": category, "raw": provider_result.get("raw")},
            }
        ],
        risk_signals=risk_signals,
        payload={"provider_result": provider_result},
        next_actions=[{"action": "persist_risk_signals"}],
    )


class SanctionsComplianceAgent(Agent):
    name = "Sanctions and Compliance Agent"

    def __init__(self, provider: SanctionsProvider | None = None):
        self.provider = provider or SanctionsProvider()

    def run(self, context: AgentContext) -> AgentOutput:
        return _risk_output(self.name, "compliance", self.provider.screen(context.supplier), "external_api")


class FinancialRiskAgent(Agent):
    name = "Financial Risk Agent"

    def __init__(self, provider: CreditProvider | None = None):
        self.provider = provider or CreditProvider()

    def run(self, context: AgentContext) -> AgentOutput:
        return _risk_output(self.name, "financial", self.provider.lookup(context.supplier), "external_api")


class NewsReputationAgent(Agent):
    name = "News and Reputation Agent"

    def __init__(self, provider: NewsProvider | None = None):
        self.provider = provider or NewsProvider()

    def run(self, context: AgentContext) -> AgentOutput:
        return _risk_output(self.name, "reputation", self.provider.search(context.supplier), "news")


class ESGRiskAgent(Agent):
    name = "ESG Risk Agent"

    def __init__(self, provider: ESGProvider | None = None):
        self.provider = provider or ESGProvider()

    def run(self, context: AgentContext) -> AgentOutput:
        return _risk_output(self.name, "esg", self.provider.search(context.supplier), "external_api")


class LogisticsRiskAgent(Agent):
    name = "Logistics Risk Agent"

    def __init__(self, provider: RouteRiskProvider | None = None):
        self.provider = provider or RouteRiskProvider()

    def run(self, context: AgentContext) -> AgentOutput:
        return _risk_output(self.name, "logistics", self.provider.lookup(context.supplier), "external_api")


class AuthenticityAgent(Agent):
    name = "Authenticity Agent"

    def run(self, context: AgentContext) -> AgentOutput:
        failed_documents = [doc for doc in context.documents if doc.get("status") == "failed" or doc.get("authenticity_status") == "needs_review"]
        mismatch_signals = [signal for signal in context.risk_signals if signal.get("category") == "authenticity"]
        certificate_without_fields = [
            doc for doc in context.documents
            if "certificate" in doc.get("document_type", "") and not _fields_for_document(context.extracted_fields, doc["id"])
        ]
        risk_signals = []
        if failed_documents:
            risk_signals.append(
                {
                    "category": "authenticity",
                    "signal": "Document extraction or profile comparison requires authenticity review",
                    "severity": "medium",
                    "confidence": 0.78,
                    "interpretation": "One or more documents failed extraction or produced profile mismatches.",
                    "recommended_action": "Risk Analyst should review OCR output, source document, and supplier profile.",
                }
            )
        if certificate_without_fields and not mismatch_signals:
            risk_signals.append(
                {
                    "category": "authenticity",
                    "signal": "Certificate document lacks extractable validation fields",
                    "severity": "medium",
                    "confidence": 0.7,
                    "interpretation": "Certificate metadata or content could not be validated against supplier profile fields.",
                    "recommended_action": "Request a clearer certificate or manually validate issuing authority.",
                }
            )
        return AgentOutput(
            agent_name=self.name,
            confidence=0.78,
            risk_signals=risk_signals,
            payload={
                "checked_documents": [doc["id"] for doc in context.documents],
                "failed_documents": [doc["id"] for doc in failed_documents],
                "certificate_without_fields": [doc["id"] for doc in certificate_without_fields],
                "prior_authenticity_signal_count": len(mismatch_signals),
            },
        )


class AnomalyAgent(Agent):
    name = "Anomaly Agent"

    def run(self, context: AgentContext) -> AgentOutput:
        replacement_count = len([doc for doc in context.documents if doc.get("status") == "replaced"])
        expected_documents = {"business_registration", "tax_certificate", "bank_letter"}
        uploaded_types = {doc.get("document_type") for doc in context.documents}
        missing_expected = sorted(expected_documents - uploaded_types)
        duplicate_types = sorted({doc_type for doc_type in uploaded_types if doc_type and len([doc for doc in context.documents if doc.get("document_type") == doc_type]) > 1})
        risk_signals = []
        if replacement_count >= 2:
            risk_signals.append(
                {
                    "category": "anomaly",
                    "signal": "Unusual document replacement frequency",
                    "severity": "medium",
                    "confidence": 0.76,
                    "interpretation": "Document replacement frequency is above expected MVP baseline.",
                    "recommended_action": "Route to Risk Analyst for review",
                }
            )
        if missing_expected:
            risk_signals.append(
                {
                    "category": "anomaly",
                    "signal": "Expected onboarding documents are missing",
                    "severity": "medium",
                    "confidence": 0.8,
                    "interpretation": f"Missing document types: {', '.join(missing_expected)}.",
                    "recommended_action": "Request missing documents from Supplier Admin before final decision.",
                }
            )
        if duplicate_types:
            risk_signals.append(
                {
                    "category": "anomaly",
                    "signal": "Duplicate document types uploaded",
                    "severity": "low",
                    "confidence": 0.7,
                    "interpretation": f"Duplicate document types found: {', '.join(duplicate_types)}.",
                    "recommended_action": "Risk Analyst should confirm the latest valid version.",
                }
            )
        return AgentOutput(
            agent_name=self.name,
            confidence=0.78,
            risk_signals=risk_signals,
            payload={
                "replacement_count": replacement_count,
                "missing_expected_documents": missing_expected,
                "duplicate_document_types": duplicate_types,
            },
        )


def _fields_for_document(fields: list[dict], document_id: str) -> list[dict]:
    return [field for field in fields if field.get("document_id") == document_id]
