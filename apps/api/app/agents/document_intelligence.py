from __future__ import annotations

from app.agents.base import Agent, AgentContext, AgentOutput
from app.integrations.ocr import OCRClient


class DocumentIntelligenceAgent(Agent):
    name = "Document Intelligence Agent"

    def __init__(self, ocr_client: OCRClient | None = None):
        self.ocr_client = ocr_client or OCRClient()

    def run(self, context: AgentContext) -> AgentOutput:
        document_results = self.ocr_client.extract_documents(context.documents)
        low_confidence = [doc for doc in document_results if doc["confidence"] < 0.75]
        return AgentOutput(
            agent_name=self.name,
            confidence=0.9,
            extracted_facts=[
                {
                    "field": "document_status",
                    "value": result["status"],
                    "document_id": result["document_id"],
                    "confidence": result["confidence"],
                }
                for result in document_results
            ],
            payload={"document_results": document_results},
            warnings=[
                {"warning_code": "LOW_CONFIDENCE_DOCUMENT", "document_id": doc["document_id"]}
                for doc in low_confidence
            ],
            next_actions=[{"action": "entity_resolution"}],
        )
