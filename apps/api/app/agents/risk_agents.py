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
        suspicious = [doc for doc in context.documents if "certificate" in doc.get("document_type", "")]
        risk_signals = [
            {
                "category": "authenticity",
                "signal": "Certificate document requires metadata validation",
                "severity": "medium",
                "confidence": 0.7,
                "interpretation": "Certificate metadata should be validated by Risk Analyst.",
                "recommended_action": "Route to Risk Analyst for review",
            }
        ] if suspicious else []
        return AgentOutput(
            agent_name=self.name,
            confidence=0.72,
            risk_signals=risk_signals,
            payload={"checked_documents": [doc["id"] for doc in context.documents]},
        )


class AnomalyAgent(Agent):
    name = "Anomaly Agent"

    def run(self, context: AgentContext) -> AgentOutput:
        replacement_count = len([doc for doc in context.documents if doc.get("status") == "replaced"])
        risk_signals = [
            {
                "category": "anomaly",
                "signal": "Unusual document replacement frequency",
                "severity": "medium",
                "confidence": 0.76,
                "interpretation": "Document replacement frequency is above expected MVP baseline.",
                "recommended_action": "Route to Risk Analyst for review",
            }
        ] if replacement_count >= 2 else []
        return AgentOutput(agent_name=self.name, confidence=0.76, risk_signals=risk_signals, payload={"replacement_count": replacement_count})
