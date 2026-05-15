from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from app.db.sqlite import db_session, row_to_dict


def _bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return authorization.removeprefix("Bearer ").strip()


def current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    token = _bearer_token(authorization)
    with db_session() as conn:
        row = conn.execute(
            """
            SELECT u.*
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ? AND s.expires_at > ?
            """,
            (token, datetime.now(timezone.utc).isoformat()),
        ).fetchone()
        user = row_to_dict(row)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
        roles = conn.execute(
            """
            SELECT r.name
            FROM roles r
            JOIN user_roles ur ON ur.role_id = r.id
            WHERE ur.user_id = ?
            ORDER BY r.name
            """,
            (user["id"],),
        ).fetchall()
        user["roles"] = [role["name"] for role in roles]
        return user


def require_roles(*allowed_roles: str):
    def dependency(user: dict = Depends(current_user)) -> dict:
        if not set(user["roles"]).intersection(allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dependency


def can_access_supplier(conn, user: dict, supplier_id: str) -> bool:
    roles = set(user["roles"])
    if "System Administrator" in roles or "Auditor" in roles:
        return True
    if "Risk Analyst" in roles:
        review = conn.execute(
            """
            SELECT 1 FROM review_queue_items
            WHERE tenant_id = ? AND supplier_id = ? AND status != 'cancelled'
            LIMIT 1
            """,
            (user["tenant_id"], supplier_id),
        ).fetchone()
        if review:
            return True
    if "Approver / Risk Committee" in roles:
        score = conn.execute(
            """
            SELECT 1 FROM risk_scores
            WHERE tenant_id = ? AND supplier_id = ?
            LIMIT 1
            """,
            (user["tenant_id"], supplier_id),
        ).fetchone()
        if score:
            return True
    if "Supplier Relationship Manager" in roles:
        approved = conn.execute(
            "SELECT 1 FROM suppliers WHERE tenant_id = ? AND id = ? AND status = 'approved'",
            (user["tenant_id"], supplier_id),
        ).fetchone()
        if approved:
            return True
    buyer = conn.execute(
        """
        SELECT 1 FROM buyer_supplier_access
        WHERE tenant_id = ? AND supplier_id = ? AND user_id = ? AND status = 'active'
        LIMIT 1
        """,
        (user["tenant_id"], supplier_id, user["id"]),
    ).fetchone()
    if buyer:
        return True
    supplier = conn.execute(
        """
        SELECT 1 FROM supplier_user_access
        WHERE tenant_id = ? AND supplier_id = ? AND user_id = ? AND status = 'active'
        LIMIT 1
        """,
        (user["tenant_id"], supplier_id, user["id"]),
    ).fetchone()
    return bool(supplier)
