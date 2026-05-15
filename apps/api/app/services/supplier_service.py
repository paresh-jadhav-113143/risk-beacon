from __future__ import annotations

import uuid

from fastapi import HTTPException, status

from app.api.dependencies import can_access_supplier
from app.db.schema import now
from app.security.auth import hash_password
from app.services.audit_service import write_audit

DEFAULT_SUPPLIER_PASSWORD = "Password123!"


def list_suppliers(conn, user: dict) -> list[dict]:
    roles = set(user["roles"])
    tenant_id = user["tenant_id"]
    if "System Administrator" in roles or "Auditor" in roles:
        rows = conn.execute("SELECT * FROM suppliers WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,)).fetchall()
    elif "Risk Analyst" in roles:
        rows = conn.execute(
            """
            SELECT DISTINCT s.*
            FROM suppliers s
            LEFT JOIN review_queue_items r ON r.supplier_id = s.id AND r.tenant_id = s.tenant_id
            WHERE s.tenant_id = ? AND (r.id IS NOT NULL OR s.status IN ('pending_review', 'approved'))
            ORDER BY s.created_at DESC
            """,
            (tenant_id,),
        ).fetchall()
    elif "Approver / Risk Committee" in roles:
        rows = conn.execute(
            """
            SELECT DISTINCT s.*
            FROM suppliers s
            JOIN risk_scores rs ON rs.supplier_id = s.id AND rs.tenant_id = s.tenant_id
            WHERE s.tenant_id = ?
            ORDER BY rs.calculated_at DESC
            """,
            (tenant_id,),
        ).fetchall()
    elif "Supplier Relationship Manager" in roles:
        rows = conn.execute(
            "SELECT * FROM suppliers WHERE tenant_id = ? AND status = 'approved' ORDER BY created_at DESC",
            (tenant_id,),
        ).fetchall()
    elif "Procurement Buyer" in roles:
        rows = conn.execute(
            """
            SELECT s.*
            FROM suppliers s
            JOIN buyer_supplier_access b ON b.supplier_id = s.id AND b.tenant_id = s.tenant_id
            WHERE s.tenant_id = ? AND b.user_id = ? AND b.status = 'active'
            ORDER BY s.created_at DESC
            """,
            (tenant_id, user["id"]),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT s.*
            FROM suppliers s
            JOIN supplier_user_access a ON a.supplier_id = s.id AND a.tenant_id = s.tenant_id
            WHERE s.tenant_id = ? AND a.user_id = ? AND a.status = 'active'
            ORDER BY s.created_at DESC
            """,
            (tenant_id, user["id"]),
        ).fetchall()
    return [enrich_supplier(conn, dict(row)) for row in rows]


def get_supplier_or_404(conn, user: dict, supplier_id: str) -> dict:
    if not can_access_supplier(conn, user, supplier_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    row = conn.execute("SELECT * FROM suppliers WHERE tenant_id = ? AND id = ?", (user["tenant_id"], supplier_id)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    supplier = enrich_supplier(conn, dict(row))
    supplier["documents"] = [dict(r) for r in conn.execute("SELECT * FROM documents WHERE supplier_id = ? ORDER BY uploaded_at DESC", (supplier_id,))]
    supplier["contacts"] = [dict(r) for r in conn.execute("SELECT * FROM supplier_contacts WHERE supplier_id = ? ORDER BY is_primary DESC, created_at DESC", (supplier_id,))]
    supplier["extracted_fields"] = [dict(r) for r in conn.execute("SELECT * FROM extracted_fields WHERE supplier_id = ? ORDER BY created_at DESC", (supplier_id,))]
    supplier["risk_signals"] = [dict(r) for r in conn.execute("SELECT * FROM risk_signals WHERE supplier_id = ? ORDER BY created_at DESC", (supplier_id,))]
    supplier["scores"] = [dict(r) for r in conn.execute("SELECT * FROM risk_scores WHERE supplier_id = ? ORDER BY calculated_at DESC", (supplier_id,))]
    supplier["recommendations"] = [dict(r) for r in conn.execute("SELECT * FROM recommendations WHERE supplier_id = ? ORDER BY created_at DESC", (supplier_id,))]
    supplier["audit_events"] = [dict(r) for r in conn.execute("SELECT * FROM audit_events WHERE entity_id = ? OR metadata_json LIKE ? ORDER BY created_at DESC LIMIT 50", (supplier_id, f"%{supplier_id}%"))]
    return supplier


def enrich_supplier(conn, supplier: dict) -> dict:
    latest_score = conn.execute(
        "SELECT composite_score, risk_level, calculated_at FROM risk_scores WHERE supplier_id = ? ORDER BY calculated_at DESC LIMIT 1",
        (supplier["id"],),
    ).fetchone()
    active_onboarding = conn.execute(
        "SELECT id, status FROM onboarding_requests WHERE supplier_id = ? ORDER BY created_at DESC LIMIT 1",
        (supplier["id"],),
    ).fetchone()
    docs = conn.execute("SELECT COUNT(*) AS total FROM documents WHERE supplier_id = ?", (supplier["id"],)).fetchone()
    signals = conn.execute("SELECT COUNT(*) AS total FROM risk_signals WHERE supplier_id = ? AND status = 'active'", (supplier["id"],)).fetchone()
    supplier["latest_score"] = dict(latest_score) if latest_score else None
    supplier["onboarding"] = dict(active_onboarding) if active_onboarding else None
    supplier["document_count"] = docs["total"] if docs else 0
    supplier["active_signal_count"] = signals["total"] if signals else 0
    return supplier


def create_supplier(conn, user: dict, payload) -> dict:
    if "Procurement Buyer" not in user["roles"] and "System Administrator" not in user["roles"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only buyers can create onboarding requests")
    timestamp = now()
    supplier_id = f"SUP-{uuid.uuid4().hex[:8].upper()}"
    onboarding_id = f"ONB-{uuid.uuid4().hex[:8].upper()}"
    conn.execute(
        """
        INSERT INTO suppliers(id, tenant_id, legal_name, country, commodity_category, supplier_tier, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (supplier_id, user["tenant_id"], payload.legal_name, payload.country, payload.commodity_category, payload.supplier_tier, "pending_onboarding", timestamp),
    )
    conn.execute(
        """
        INSERT INTO onboarding_requests(id, tenant_id, supplier_id, requester_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (onboarding_id, user["tenant_id"], supplier_id, user["id"], "draft", timestamp),
    )
    conn.execute(
        """
        INSERT INTO buyer_supplier_access(id, tenant_id, supplier_id, user_id, access_level, status, assigned_by, assigned_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (f"BSA-{uuid.uuid4().hex[:10]}", user["tenant_id"], supplier_id, user["id"], "manage_onboarding", "active", user["id"], timestamp),
    )
    invitation = None
    if payload.supplier_contact_email:
        contact_id = f"CON-{uuid.uuid4().hex[:10]}"
        contact_email = str(payload.supplier_contact_email).lower()
        contact_name = payload.supplier_contact_name or contact_email.split("@", 1)[0].replace(".", " ").title()
        conn.execute(
            """
            INSERT INTO supplier_contacts(id, tenant_id, supplier_id, name, email, role, is_primary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (contact_id, user["tenant_id"], supplier_id, contact_name, contact_email, "Supplier Admin", 1, timestamp),
        )
        invitation = _invite_supplier_admin(
            conn=conn,
            tenant_id=user["tenant_id"],
            supplier_id=supplier_id,
            contact_id=contact_id,
            email=contact_email,
            name=contact_name,
            invited_by=user["id"],
            timestamp=timestamp,
        )
    write_audit(
        conn,
        tenant_id=user["tenant_id"],
        actor_type="user",
        actor_id=user["id"],
        action="onboarding.created",
        entity_type="supplier",
        entity_id=supplier_id,
        after={"supplier_id": supplier_id, "onboarding_request_id": onboarding_id},
    )
    created = get_supplier_or_404(conn, user, supplier_id)
    if invitation:
        created["invitation"] = invitation
    return created


def _invite_supplier_admin(
    conn,
    tenant_id: str,
    supplier_id: str,
    contact_id: str,
    email: str,
    name: str,
    invited_by: str,
    timestamp: str,
) -> dict:
    user_row = conn.execute(
        "SELECT id FROM users WHERE tenant_id = ? AND lower(email) = lower(?)",
        (tenant_id, email),
    ).fetchone()
    created_new_user = user_row is None
    if user_row:
        supplier_user_id = user_row["id"]
    else:
        supplier_user_id = f"USR-{uuid.uuid4().hex[:10]}"
        conn.execute(
            """
            INSERT INTO users(id, tenant_id, email, password_hash, name, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (supplier_user_id, tenant_id, email, hash_password(DEFAULT_SUPPLIER_PASSWORD), name, "active", timestamp),
        )

    role = conn.execute(
        "SELECT id FROM roles WHERE tenant_id = ? AND name = ?",
        (tenant_id, "Supplier Admin"),
    ).fetchone()
    if not role:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Supplier Admin role is not configured")
    conn.execute(
        "INSERT OR IGNORE INTO user_roles(user_id, role_id, assigned_at, assigned_by) VALUES (?, ?, ?, ?)",
        (supplier_user_id, role["id"], timestamp, invited_by),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO supplier_user_access(id, tenant_id, supplier_id, user_id, supplier_contact_id,
          access_role, status, invited_by, invited_at, accepted_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"SUA-{uuid.uuid4().hex[:10]}",
            tenant_id,
            supplier_id,
            supplier_user_id,
            contact_id,
            "supplier_admin",
            "active",
            invited_by,
            timestamp,
            timestamp if created_new_user else None,
            timestamp,
        ),
    )
    conn.execute(
        """
        INSERT INTO notifications(id, tenant_id, recipient_id, supplier_id, type, title, body, status, severity, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"NOT-{uuid.uuid4().hex[:10]}",
            tenant_id,
            supplier_user_id,
            supplier_id,
            "supplier_invitation",
            "Supplier onboarding invitation",
            "You have been invited to complete supplier onboarding.",
            "unread",
            "info",
            timestamp,
        ),
    )
    write_audit(
        conn,
        tenant_id=tenant_id,
        actor_type="user",
        actor_id=invited_by,
        action="supplier.invitation_sent",
        entity_type="supplier",
        entity_id=supplier_id,
        after={"supplier_user_id": supplier_user_id, "email": email, "created_new_user": created_new_user},
    )
    invitation = {
        "status": "created" if created_new_user else "linked_existing_user",
        "supplier_user_id": supplier_user_id,
        "email": email,
        "role": "Supplier Admin",
        "supplier_id": supplier_id,
        "login_url": "/auth/login",
        "password_delivery": "default_password" if created_new_user else "existing_user_password",
    }
    if created_new_user:
        invitation["default_password"] = DEFAULT_SUPPLIER_PASSWORD
    return invitation
