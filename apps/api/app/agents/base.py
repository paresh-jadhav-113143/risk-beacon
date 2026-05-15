from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    tenant_id: str
    supplier_id: str
    onboarding_request_id: str | None
    correlation_id: str
    user: dict
    supplier: dict
    documents: list[dict] = field(default_factory=list)
    extracted_fields: list[dict] = field(default_factory=list)
    risk_signals: list[dict] = field(default_factory=list)
    score: dict | None = None
    recommendation: dict | None = None


@dataclass
class AgentOutput:
    agent_name: str
    status: str = "succeeded"
    confidence: float = 1.0
    extracted_facts: list[dict] = field(default_factory=list)
    evidence_sources: list[dict] = field(default_factory=list)
    risk_signals: list[dict] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict] = field(default_factory=list)
    next_actions: list[dict] = field(default_factory=list)


class Agent:
    name = "Base Agent"

    def run(self, context: AgentContext) -> AgentOutput:
        raise NotImplementedError
