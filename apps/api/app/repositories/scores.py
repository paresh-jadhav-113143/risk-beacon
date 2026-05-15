from __future__ import annotations

from app.db.schema import now
from app.repositories.base import Repository, new_id


class ScoreRepository(Repository):
    def create_score(
        self,
        *,
        tenant_id: str,
        supplier_id: str,
        onboarding_request_id: str | None,
        agent_run_id: str,
        composite_score: int,
        risk_level: str,
        components: list[dict],
    ) -> str:
        score_id = new_id("SCORE")
        self.conn.execute(
            """
            INSERT INTO risk_scores(id, tenant_id, supplier_id, onboarding_request_id, agent_run_id,
              composite_score, risk_level, calculated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (score_id, tenant_id, supplier_id, onboarding_request_id, agent_run_id, composite_score, risk_level, now()),
        )
        for component in components:
            self.conn.execute(
                """
                INSERT INTO score_components(id, tenant_id, risk_score_id, category, score, weight, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("SC"),
                    tenant_id,
                    score_id,
                    component["category"],
                    component["score"],
                    component["weight"],
                    component["explanation"],
                ),
            )
        return score_id
