from __future__ import annotations

import json

from app.db.schema import now
from app.repositories.base import Repository, new_id


class AgentRunRepository(Repository):
    def create_succeeded(
        self,
        *,
        tenant_id: str,
        agent_name: str,
        supplier_id: str,
        onboarding_request_id: str | None,
        correlation_id: str,
        input_payload: dict,
        output_payload: dict,
    ) -> str:
        run_id = new_id("RUN")
        timestamp = now()
        self.conn.execute(
            """
            INSERT INTO agent_runs(id, tenant_id, agent_name, supplier_id, onboarding_request_id, correlation_id,
              status, input_json, output_json, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                tenant_id,
                agent_name,
                supplier_id,
                onboarding_request_id,
                correlation_id,
                "succeeded",
                json.dumps(input_payload),
                json.dumps(output_payload),
                timestamp,
                timestamp,
            ),
        )
        return run_id
