from __future__ import annotations

from app.db.schema import now
from app.repositories.base import Repository


class SupplierRepository(Repository):
    def get(self, tenant_id: str, supplier_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM suppliers WHERE tenant_id = ? AND id = ?",
            (tenant_id, supplier_id),
        ).fetchone()
        return dict(row) if row else None

    def latest_onboarding_id(self, supplier_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT id FROM onboarding_requests WHERE supplier_id = ? ORDER BY created_at DESC LIMIT 1",
            (supplier_id,),
        ).fetchone()
        return row["id"] if row else None

    def set_status(self, supplier_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE suppliers SET status = ?, updated_at = ? WHERE id = ?",
            (status, now(), supplier_id),
        )

    def set_onboarding_status(self, onboarding_id: str | None, status: str) -> None:
        if onboarding_id:
            self.conn.execute(
                "UPDATE onboarding_requests SET status = ?, updated_at = ? WHERE id = ?",
                (status, now(), onboarding_id),
            )
