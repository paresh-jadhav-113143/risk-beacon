from __future__ import annotations

import json
import uuid
from typing import Optional

from app.db.schema import now


def write_audit(
    conn,
    *,
    tenant_id: str,
    actor_type: str,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    correlation_id: Optional[str] = None,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO audit_events(id, tenant_id, correlation_id, actor_type, actor_id, action, entity_type,
          entity_id, before_json, after_json, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"AUD-{uuid.uuid4().hex[:12]}",
            tenant_id,
            correlation_id or f"corr-{uuid.uuid4().hex[:10]}",
            actor_type,
            actor_id,
            action,
            entity_type,
            entity_id,
            json.dumps(before) if before else None,
            json.dumps(after) if after else None,
            json.dumps(metadata or {}),
            now(),
        ),
    )
