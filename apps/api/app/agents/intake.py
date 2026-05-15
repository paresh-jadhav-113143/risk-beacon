from __future__ import annotations

from app.agents.base import Agent, AgentContext, AgentOutput


class IntakeAgent(Agent):
    name = "Intake Agent"

    def run(self, context: AgentContext) -> AgentOutput:
        supplier = context.supplier
        missing_fields = [
            field
            for field in ["legal_name", "country", "commodity_category"]
            if not supplier.get(field)
        ]
        return AgentOutput(
            agent_name=self.name,
            confidence=0.96 if not missing_fields else 0.78,
            extracted_facts=[
                {"field": "legal_name", "value": supplier.get("legal_name"), "confidence": 0.98},
                {"field": "country", "value": supplier.get("country"), "confidence": 0.96},
            ],
            payload={
                "normalized_supplier": {
                    "supplier_id": supplier["id"],
                    "legal_name": supplier.get("legal_name"),
                    "country": supplier.get("country"),
                    "category": supplier.get("commodity_category"),
                },
                "missing_fields": missing_fields,
            },
            warnings=[{"warning_code": "MISSING_FIELDS", "fields": missing_fields}] if missing_fields else [],
            next_actions=[{"action": "document_extraction"}],
        )
