from __future__ import annotations

import uuid

from app.agents.base import AgentContext, AgentOutput
from app.agents.document_intelligence import DocumentIntelligenceAgent
from app.agents.entity_resolution import EntityResolutionAgent
from app.agents.human_review import HumanReviewAgent
from app.agents.intake import IntakeAgent
from app.agents.recommendation import RecommendationAgent
from app.agents.risk_agents import (
    AnomalyAgent,
    AuthenticityAgent,
    ESGRiskAgent,
    FinancialRiskAgent,
    LogisticsRiskAgent,
    NewsReputationAgent,
    SanctionsComplianceAgent,
)
from app.agents.scoring import ScoringAgent
from app.repositories import (
    AgentRunRepository,
    DocumentRepository,
    EvidenceSourceRepository,
    RecommendationRepository,
    ReviewQueueRepository,
    RiskSignalRepository,
    ScoreRepository,
    SupplierRepository,
)
from app.services.audit_service import write_audit


class AgentOrchestrator:
    def __init__(self, conn):
        self.conn = conn
        self.agent_runs = AgentRunRepository(conn)
        self.documents = DocumentRepository(conn)
        self.evidence = EvidenceSourceRepository(conn)
        self.recommendations = RecommendationRepository(conn)
        self.review_queue = ReviewQueueRepository(conn)
        self.risk_signals = RiskSignalRepository(conn)
        self.scores = ScoreRepository(conn)
        self.suppliers = SupplierRepository(conn)

    def run_pre_onboarding(self, *, user: dict, supplier_id: str) -> dict:
        supplier = self.suppliers.get(user["tenant_id"], supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")
        context = AgentContext(
            tenant_id=user["tenant_id"],
            supplier_id=supplier_id,
            onboarding_request_id=self.suppliers.latest_onboarding_id(supplier_id),
            correlation_id=f"corr-{uuid.uuid4().hex[:10]}",
            user=user,
            supplier=supplier,
            documents=self.documents.list_for_supplier(user["tenant_id"], supplier_id),
        )

        intake_output = IntakeAgent().run(context)
        self._persist_output(context, intake_output)

        document_output = DocumentIntelligenceAgent().run(context)
        document_run_id = self._persist_output(context, document_output)
        self._persist_document_extraction(context, document_run_id, document_output)
        context.extracted_fields.extend(document_output.extracted_facts)
        context.risk_signals.extend(document_output.risk_signals)
        context.documents = self.documents.list_for_supplier(user["tenant_id"], supplier_id)

        entity_output = EntityResolutionAgent().run(context)
        self._persist_output(context, entity_output)
        context.risk_signals.extend(entity_output.risk_signals)

        for agent in [
            SanctionsComplianceAgent(),
            FinancialRiskAgent(),
            NewsReputationAgent(),
            ESGRiskAgent(),
            LogisticsRiskAgent(),
            AuthenticityAgent(),
            AnomalyAgent(),
        ]:
            output = agent.run(context)
            self._persist_output(context, output)
            context.risk_signals.extend(output.risk_signals)

        score_output = ScoringAgent().run(context)
        score_run_id = self._persist_output(context, score_output)
        score_payload = score_output.payload
        score_id = self.scores.create_score(
            tenant_id=context.tenant_id,
            supplier_id=context.supplier_id,
            onboarding_request_id=context.onboarding_request_id,
            agent_run_id=score_run_id,
            composite_score=score_payload["composite_score"],
            risk_level=score_payload["risk_level"],
            components=score_payload["components"],
        )
        context.score = {
            "risk_score_id": score_id,
            "composite_score": score_payload["composite_score"],
            "risk_level": score_payload["risk_level"],
        }

        recommendation_output = RecommendationAgent().run(context)
        recommendation_run_id = self._persist_output(context, recommendation_output)
        recommendation_id = self.recommendations.create(
            tenant_id=context.tenant_id,
            supplier_id=context.supplier_id,
            onboarding_request_id=context.onboarding_request_id,
            agent_run_id=recommendation_run_id,
            risk_score_id=score_id,
            recommended_action=recommendation_output.payload["recommended_action"],
            summary=recommendation_output.payload["summary"],
            rationale=recommendation_output.payload["rationale"],
        )
        context.recommendation = {
            "recommendation_id": recommendation_id,
            "recommended_action": recommendation_output.payload["recommended_action"],
            "summary": recommendation_output.payload["summary"],
        }

        review_output = HumanReviewAgent().run(context)
        self._persist_output(context, review_output)
        self.review_queue.create(
            tenant_id=context.tenant_id,
            supplier_id=context.supplier_id,
            onboarding_request_id=context.onboarding_request_id,
            assigned_role=review_output.payload["assigned_role"],
            priority=review_output.payload["priority"],
        )
        self.suppliers.set_status(context.supplier_id, "pending_review")
        self.suppliers.set_onboarding_status(context.onboarding_request_id, "in_review")
        write_audit(
            self.conn,
            tenant_id=context.tenant_id,
            actor_type="agent",
            actor_id="orchestrator",
            action="assessment.completed",
            entity_type="supplier",
            entity_id=context.supplier_id,
            correlation_id=context.correlation_id,
            after={"score": context.score, "recommendation": context.recommendation},
        )
        return {"correlation_id": context.correlation_id, "score": context.score, "recommendation": context.recommendation}

    def _persist_output(self, context: AgentContext, output: AgentOutput) -> str:
        run_id = self.agent_runs.create_succeeded(
            tenant_id=context.tenant_id,
            agent_name=output.agent_name,
            supplier_id=context.supplier_id,
            onboarding_request_id=context.onboarding_request_id,
            correlation_id=context.correlation_id,
            input_payload={"supplier_id": context.supplier_id},
            output_payload={
                "status": output.status,
                "confidence": output.confidence,
                "extracted_facts": output.extracted_facts,
                "risk_signals": output.risk_signals,
                "payload": output.payload,
                "warnings": output.warnings,
                "next_actions": output.next_actions,
            },
        )
        for evidence in output.evidence_sources:
            self.evidence.create(
                tenant_id=context.tenant_id,
                supplier_id=context.supplier_id,
                agent_run_id=run_id,
                source_type=evidence["source_type"],
                name=evidence["name"],
                credibility_score=evidence["credibility_score"],
                url=evidence.get("url"),
                metadata=evidence.get("metadata"),
            )
        for signal in output.risk_signals:
            self.risk_signals.create(
                tenant_id=context.tenant_id,
                supplier_id=context.supplier_id,
                agent_run_id=run_id,
                category=signal["category"],
                signal=signal["signal"],
                severity=signal["severity"],
                confidence=signal["confidence"],
                interpretation=signal["interpretation"],
                recommended_action=signal["recommended_action"],
            )
        write_audit(
            self.conn,
            tenant_id=context.tenant_id,
            actor_type="agent",
            actor_id=run_id,
            action="agent.run_completed",
            entity_type="supplier",
            entity_id=context.supplier_id,
            correlation_id=context.correlation_id,
            after={"agent_name": output.agent_name, "status": output.status},
        )
        return run_id

    def _persist_document_extraction(self, context: AgentContext, run_id: str, output: AgentOutput) -> None:
        timestamped_documents = output.payload.get("document_results", [])
        for result in timestamped_documents:
            status = "extracted" if result.get("status") == "extracted" else "failed"
            authenticity_status = "warning" if result.get("profile_comparisons") else "not_checked"
            mismatches = [item for item in result.get("profile_comparisons", []) if item.get("status") == "mismatch"]
            if mismatches:
                authenticity_status = "needs_review"
            self.conn.execute(
                "UPDATE documents SET status = ?, authenticity_status = ? WHERE tenant_id = ? AND id = ?",
                (status, authenticity_status, context.tenant_id, result["document_id"]),
            )
            for field in result.get("extracted_fields", []):
                self.conn.execute(
                    """
                    INSERT INTO extracted_fields(id, tenant_id, supplier_id, document_id, agent_run_id,
                      field_name, field_value, confidence, source_text, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        f"EXT-{uuid.uuid4().hex[:10]}",
                        context.tenant_id,
                        context.supplier_id,
                        result["document_id"],
                        run_id,
                        field["field_name"],
                        field.get("field_value"),
                        field["confidence"],
                        field.get("source_text"),
                    ),
                )
