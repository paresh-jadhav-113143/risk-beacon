from __future__ import annotations

import json

from app.db.schema import now
from app.repositories.base import Repository, new_id


class RecommendationRepository(Repository):
    def create(
        self,
        *,
        tenant_id: str,
        supplier_id: str,
        onboarding_request_id: str | None,
        agent_run_id: str,
        risk_score_id: str,
        recommended_action: str,
        summary: str,
        rationale: list[dict],
    ) -> str:
        recommendation_id = new_id("REC")
        self.conn.execute(
            """
            INSERT INTO recommendations(id, tenant_id, supplier_id, onboarding_request_id, agent_run_id, risk_score_id,
              recommended_action, recommended_owner_role, summary, rationale_json, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recommendation_id,
                tenant_id,
                supplier_id,
                onboarding_request_id,
                agent_run_id,
                risk_score_id,
                recommended_action,
                "Risk Analyst",
                summary,
                json.dumps(rationale),
                "active",
                now(),
            ),
        )
        return recommendation_id
