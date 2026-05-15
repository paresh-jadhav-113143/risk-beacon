from __future__ import annotations

from app.agents.base import Agent, AgentContext, AgentOutput


class EntityResolutionAgent(Agent):
    name = "Entity Resolution Agent"

    def run(self, context: AgentContext) -> AgentOutput:
        supplier = context.supplier
        return AgentOutput(
            agent_name=self.name,
            confidence=0.91,
            evidence_sources=[
                {
                    "source_type": "internal",
                    "name": "Supplier master profile",
                    "credibility_score": 0.8,
                    "metadata": {"match_factors": ["legal_name", "country", "registration_number"]},
                }
            ],
            payload={
                "entity_matches": [
                    {
                        "match_type": "legal_entity",
                        "matched_name": supplier.get("legal_name"),
                        "matched_identifier": supplier.get("registration_number"),
                        "confidence": 0.91,
                    }
                ]
            },
            next_actions=[{"action": "risk_enrichment"}],
        )
