from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import current_user
from app.db.sqlite import db_session

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/review-queue")
def review_queue(user: dict = Depends(current_user)) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT r.*, s.legal_name, s.country
            FROM review_queue_items r
            JOIN suppliers s ON s.id = r.supplier_id
            WHERE r.tenant_id = ? AND r.status = 'open'
            ORDER BY r.created_at DESC
            """,
            (user["tenant_id"],),
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/notifications")
def notifications(user: dict = Depends(current_user)) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM notifications WHERE tenant_id = ? AND recipient_id = ? ORDER BY created_at DESC LIMIT 50",
            (user["tenant_id"], user["id"]),
        ).fetchall()
        return [dict(row) for row in rows]
