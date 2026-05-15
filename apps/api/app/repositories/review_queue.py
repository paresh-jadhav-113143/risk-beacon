from __future__ import annotations

from app.db.schema import now
from app.repositories.base import Repository, new_id


class ReviewQueueRepository(Repository):
    def create(
        self,
        *,
        tenant_id: str,
        supplier_id: str,
        onboarding_request_id: str | None,
        assigned_role: str,
        priority: str,
    ) -> str:
        review_id = new_id("REV")
        self.conn.execute(
            """
            INSERT INTO review_queue_items(id, tenant_id, supplier_id, onboarding_request_id,
              assigned_role, priority, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (review_id, tenant_id, supplier_id, onboarding_request_id, assigned_role, priority, "open", now()),
        )
        return review_id
