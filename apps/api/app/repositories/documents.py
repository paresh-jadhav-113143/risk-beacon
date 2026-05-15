from __future__ import annotations

from app.repositories.base import Repository


class DocumentRepository(Repository):
    def list_for_supplier(self, tenant_id: str, supplier_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM documents WHERE tenant_id = ? AND supplier_id = ? ORDER BY uploaded_at DESC",
            (tenant_id, supplier_id),
        ).fetchall()
        return [dict(row) for row in rows]
