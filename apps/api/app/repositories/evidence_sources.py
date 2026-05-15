from __future__ import annotations

import json

from app.db.schema import now
from app.repositories.base import Repository, new_id


class EvidenceSourceRepository(Repository):
    def create(
        self,
        *,
        tenant_id: str,
        supplier_id: str,
        agent_run_id: str,
        source_type: str,
        name: str,
        credibility_score: float,
        url: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        evidence_id = new_id("EVD")
        self.conn.execute(
            """
            INSERT INTO evidence_sources(id, tenant_id, supplier_id, agent_run_id, source_type, name, url,
              retrieved_at, credibility_score, snapshot_storage_key, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                tenant_id,
                supplier_id,
                agent_run_id,
                source_type,
                name,
                url,
                now(),
                credibility_score,
                f"evidence/{evidence_id}.json",
                json.dumps(metadata or {}),
            ),
        )
        return evidence_id
