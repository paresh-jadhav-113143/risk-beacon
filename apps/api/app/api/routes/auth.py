from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies import current_user
from app.db.schema import now
from app.db.sqlite import db_session, row_to_dict
from app.schemas import LoginRequest, LoginResponse
from app.security.auth import new_token, token_expiry, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE lower(email) = lower(?) AND status = 'active'",
            (payload.email,),
        ).fetchone()
        user = row_to_dict(row)
        if not user or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        token = new_token()
        conn.execute(
            "INSERT INTO sessions(token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user["id"], now(), token_expiry()),
        )
        conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (datetime.now(timezone.utc).isoformat(), user["id"]))
        roles = conn.execute(
            """
            SELECT r.name FROM roles r
            JOIN user_roles ur ON ur.role_id = r.id
            WHERE ur.user_id = ?
            ORDER BY r.name
            """,
            (user["id"],),
        ).fetchall()
        safe_user = _safe_user(user, [r["name"] for r in roles])
        return LoginResponse(token=token, user=safe_user)


@router.post("/logout")
def logout(authorization: Optional[str] = Header(default=None)) -> dict:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        with db_session() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    return {"ok": True}


@router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    return _safe_user(user, user["roles"])


def _safe_user(user: dict, roles: list[str]) -> dict:
    return {
        "id": user["id"],
        "tenant_id": user["tenant_id"],
        "email": user["email"],
        "name": user["name"],
        "status": user["status"],
        "roles": roles,
    }
