from __future__ import annotations

from app.db.schema import now
from app.repositories.base import Repository, new_id


class RiskSignalRepository(Repository):
    def create(
        self,
        *,
        tenant_id: str,
        supplier_id: str,
        agent_run_id: str,
        category: str,
        signal: str,
        severity: str,
        confidence: float,
        interpretation: str,
        recommended_action: str,
    ) -> str:
        signal_id = new_id("RSK")
        self.conn.execute(
            """
            INSERT INTO risk_signals(id, tenant_id, supplier_id, agent_run_id, category, signal, severity,
              confidence, interpretation, recommended_action, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_id,
                tenant_id,
                supplier_id,
                agent_run_id,
                category,
                signal,
                severity,
                confidence,
                interpretation,
                recommended_action,
                "active",
                now(),
            ),
        )
        return signal_id

    def active_for_supplier(self, supplier_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM risk_signals WHERE supplier_id = ? AND status = 'active' ORDER BY created_at DESC",
            (supplier_id,),
        ).fetchall()
        return [dict(row) for row in rows]
