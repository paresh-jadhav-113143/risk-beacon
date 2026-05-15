from __future__ import annotations

from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.dependencies import current_user
from app.config.settings import settings
from app.db.schema import now
from app.db.sqlite import db_session
from app.schemas import DecisionCreate, DocumentCreate, FindingReview, SupplierCreate, SupplierUpdate
from app.services.agent_service import run_assessment
from app.services.audit_service import write_audit
from app.services.supplier_service import create_supplier, get_supplier_or_404, list_suppliers

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("")
def suppliers(user: dict = Depends(current_user)) -> list[dict]:
    with db_session() as conn:
        return list_suppliers(conn, user)


@router.post("")
def create(payload: SupplierCreate, user: dict = Depends(current_user)) -> dict:
    with db_session() as conn:
        return create_supplier(conn, user, payload)


@router.get("/{supplier_id}")
def detail(supplier_id: str, user: dict = Depends(current_user)) -> dict:
    with db_session() as conn:
        return get_supplier_or_404(conn, user, supplier_id)


@router.patch("/{supplier_id}")
def update_supplier(supplier_id: str, payload: SupplierUpdate, user: dict = Depends(current_user)) -> dict:
    with db_session() as conn:
        supplier = get_supplier_or_404(conn, user, supplier_id)
        roles = set(user["roles"])
        if not roles.intersection({"Supplier Admin", "System Administrator"}):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update supplier")
        if "System Administrator" not in roles and supplier["status"] not in {"pending_onboarding", "needs_information"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Supplier profile cannot be edited in the current workflow status")
        updates = payload.model_dump(exclude_unset=True)
        if updates:
            columns = ", ".join(f"{key} = ?" for key in updates)
            conn.execute(
                f"UPDATE suppliers SET {columns}, updated_at = ? WHERE id = ?",
                (*updates.values(), now(), supplier_id),
            )
            write_audit(
                conn,
                tenant_id=user["tenant_id"],
                actor_type="user",
                actor_id=user["id"],
                action="supplier.profile_updated",
                entity_type="supplier",
                entity_id=supplier_id,
                before=supplier,
                after=updates,
            )
        return get_supplier_or_404(conn, user, supplier_id)


@router.post("/{supplier_id}/documents")
def add_document(supplier_id: str, payload: DocumentCreate, user: dict = Depends(current_user)) -> dict:
    with db_session() as conn:
        supplier = get_supplier_or_404(conn, user, supplier_id)
        roles = set(user["roles"])
        if not roles.intersection({"Supplier Admin", "System Administrator"}):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot add documents")
        if "System Administrator" not in roles and supplier["status"] not in {"pending_onboarding", "needs_information"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Documents cannot be added in the current workflow status")
        duplicate = conn.execute(
            """
            SELECT id FROM documents
            WHERE tenant_id = ? AND supplier_id = ? AND document_type = ? AND status NOT IN ('replaced', 'archived')
            LIMIT 1
            """,
            (user["tenant_id"], supplier_id, payload.document_type),
        ).fetchone()
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{payload.document_type} already exists for this supplier")
        onboarding = conn.execute("SELECT id FROM onboarding_requests WHERE supplier_id = ? ORDER BY created_at DESC LIMIT 1", (supplier_id,)).fetchone()
        doc_id = f"DOC-{uuid.uuid4().hex[:10]}"
        timestamp = now()
        conn.execute(
            """
            INSERT INTO documents(id, tenant_id, supplier_id, onboarding_request_id, document_type, file_name,
              storage_key, status, uploaded_by, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, user["tenant_id"], supplier_id, onboarding["id"] if onboarding else None, payload.document_type, payload.file_name, f"documents/{doc_id}-{payload.file_name}", "uploaded", user["id"], timestamp),
        )
        write_audit(conn, tenant_id=user["tenant_id"], actor_type="user", actor_id=user["id"], action="document.uploaded", entity_type="document", entity_id=doc_id, metadata={"supplier_id": supplier_id})
        return get_supplier_or_404(conn, user, supplier_id)


@router.get("/{supplier_id}/documents/{document_id}/download")
def download_document(supplier_id: str, document_id: str, user: dict = Depends(current_user)):
    with db_session() as conn:
        get_supplier_or_404(conn, user, supplier_id)
        if not set(user["roles"]).intersection({"Supplier Admin", "Risk Analyst", "Approver / Risk Committee", "System Administrator", "Auditor"}):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot download documents")
        document = conn.execute(
            "SELECT * FROM documents WHERE tenant_id = ? AND supplier_id = ? AND id = ?",
            (user["tenant_id"], supplier_id, document_id),
        ).fetchone()
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        path = Path(settings.local_storage_root) / document["storage_key"]
        if not path.exists():
            sidecar = path.with_suffix(path.suffix + ".txt")
            if sidecar.exists():
                path = sidecar
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is not available in local storage")
        return FileResponse(path, filename=document["file_name"])


@router.post("/{supplier_id}/run-assessment")
def assess(supplier_id: str, user: dict = Depends(current_user)) -> dict:
    with db_session() as conn:
        get_supplier_or_404(conn, user, supplier_id)
        if not set(user["roles"]).intersection({"Procurement Buyer", "Risk Analyst", "System Administrator"}):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot run assessment")
        result = run_assessment(conn, user, supplier_id)
        timestamp = now()
        _notify_role(
            conn,
            tenant_id=user["tenant_id"],
            role_name="Risk Analyst",
            supplier_id=supplier_id,
            notification_type="risk_review_assigned",
            title="Supplier risk review assigned",
            body="Assessment is complete. Risk findings are ready for analyst review.",
            severity="info",
            timestamp=timestamp,
        )
        return {"result": result, "supplier": get_supplier_or_404(conn, user, supplier_id)}


@router.post("/{supplier_id}/risk-signals/{signal_id}/review")
def review_finding(supplier_id: str, signal_id: str, payload: FindingReview, user: dict = Depends(current_user)) -> dict:
    with db_session() as conn:
        get_supplier_or_404(conn, user, supplier_id)
        if "Risk Analyst" not in user["roles"] and "System Administrator" not in user["roles"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Risk Analysts can review findings")
        signal = conn.execute(
            "SELECT * FROM risk_signals WHERE tenant_id = ? AND supplier_id = ? AND id = ?",
            (user["tenant_id"], supplier_id, signal_id),
        ).fetchone()
        if not signal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
        status_by_action = {
            "accept": "accepted",
            "dismiss": "dismissed",
            "request_information": "needs_information",
        }
        new_status = status_by_action[payload.action]
        updated_interpretation = f"{signal['interpretation']}\n\nRisk Analyst review: {payload.reason}"
        conn.execute(
            "UPDATE risk_signals SET status = ?, interpretation = ? WHERE id = ?",
            (new_status, updated_interpretation, signal_id),
        )
        if payload.action == "request_information":
            onboarding = conn.execute("SELECT id FROM onboarding_requests WHERE supplier_id = ? ORDER BY created_at DESC LIMIT 1", (supplier_id,)).fetchone()
            timestamp = now()
            conn.execute("UPDATE suppliers SET status = ?, updated_at = ? WHERE id = ?", ("pending_onboarding", timestamp, supplier_id))
            if onboarding:
                conn.execute("UPDATE onboarding_requests SET status = ?, updated_at = ? WHERE id = ?", ("needs_information", timestamp, onboarding["id"]))
        elif payload.action in {"accept", "dismiss"}:
            _route_to_approver_if_ready(conn, user, supplier_id)
        write_audit(
            conn,
            tenant_id=user["tenant_id"],
            actor_type="user",
            actor_id=user["id"],
            action=f"finding.{payload.action}",
            entity_type="risk_signal",
            entity_id=signal_id,
            before=dict(signal),
            after={"status": new_status, "reason": payload.reason},
        )
        return get_supplier_or_404(conn, user, supplier_id)


def _route_to_approver_if_ready(conn, user: dict, supplier_id: str) -> None:
    unresolved = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM risk_signals
        WHERE tenant_id = ? AND supplier_id = ? AND status = 'active'
        """,
        (user["tenant_id"], supplier_id),
    ).fetchone()
    if unresolved and unresolved["total"] > 0:
        return

    onboarding = conn.execute(
        "SELECT id FROM onboarding_requests WHERE supplier_id = ? ORDER BY created_at DESC LIMIT 1",
        (supplier_id,),
    ).fetchone()
    latest_score = conn.execute(
        "SELECT risk_level FROM risk_scores WHERE tenant_id = ? AND supplier_id = ? ORDER BY calculated_at DESC LIMIT 1",
        (user["tenant_id"], supplier_id),
    ).fetchone()
    timestamp = now()
    conn.execute("UPDATE suppliers SET status = ?, updated_at = ? WHERE id = ?", ("pending_approval", timestamp, supplier_id))
    if onboarding:
        conn.execute("UPDATE onboarding_requests SET status = ?, updated_at = ? WHERE id = ?", ("pending_approval", timestamp, onboarding["id"]))
    conn.execute(
        """
        UPDATE review_queue_items
        SET status = 'completed'
        WHERE tenant_id = ? AND supplier_id = ? AND assigned_role = 'Risk Analyst' AND status = 'open'
        """,
        (user["tenant_id"], supplier_id),
    )
    approver_queue = conn.execute(
        """
        SELECT id FROM review_queue_items
        WHERE tenant_id = ? AND supplier_id = ? AND assigned_role = 'Approver / Risk Committee' AND status = 'open'
        LIMIT 1
        """,
        (user["tenant_id"], supplier_id),
    ).fetchone()
    if not approver_queue:
        conn.execute(
            """
            INSERT INTO review_queue_items(id, tenant_id, supplier_id, onboarding_request_id,
              assigned_role, priority, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"REV-{uuid.uuid4().hex[:10]}",
                user["tenant_id"],
                supplier_id,
                onboarding["id"] if onboarding else None,
                "Approver / Risk Committee",
                latest_score["risk_level"] if latest_score else "medium",
                "open",
                timestamp,
            ),
        )
    _notify_role(
        conn,
        tenant_id=user["tenant_id"],
        role_name="Approver / Risk Committee",
        supplier_id=supplier_id,
        notification_type="final_approval_ready",
        title="Supplier ready for final approval",
        body="Risk Analyst has completed finding review. Final approval is now pending.",
        severity="info",
        timestamp=timestamp,
    )
    _notify_buyer_requester(
        conn,
        tenant_id=user["tenant_id"],
        supplier_id=supplier_id,
        notification_type="risk_review_completed",
        title="Risk review completed",
        body="Risk Analyst has completed finding review and routed the supplier for final approval.",
        severity="info",
        timestamp=timestamp,
    )
    write_audit(
        conn,
        tenant_id=user["tenant_id"],
        actor_type="user",
        actor_id=user["id"],
        action="review.routed_to_approver",
        entity_type="supplier",
        entity_id=supplier_id,
        after={"supplier_status": "pending_approval", "onboarding_status": "pending_approval"},
    )


def _notify_role(
    conn,
    *,
    tenant_id: str,
    role_name: str,
    supplier_id: str,
    notification_type: str,
    title: str,
    body: str,
    severity: str,
    timestamp: str,
) -> None:
    recipients = conn.execute(
        """
        SELECT DISTINCT u.id
        FROM users u
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r ON r.id = ur.role_id
        WHERE u.tenant_id = ? AND r.name = ? AND u.status = 'active'
        """,
        (tenant_id, role_name),
    ).fetchall()
    for recipient in recipients:
        _insert_notification(conn, tenant_id, recipient["id"], supplier_id, notification_type, title, body, severity, timestamp)


def _notify_buyer_requester(
    conn,
    *,
    tenant_id: str,
    supplier_id: str,
    notification_type: str,
    title: str,
    body: str,
    severity: str,
    timestamp: str,
) -> None:
    recipients = conn.execute(
        """
        SELECT DISTINCT requester_id AS id
        FROM onboarding_requests
        WHERE tenant_id = ? AND supplier_id = ?
        """,
        (tenant_id, supplier_id),
    ).fetchall()
    for recipient in recipients:
        _insert_notification(conn, tenant_id, recipient["id"], supplier_id, notification_type, title, body, severity, timestamp)


def _insert_notification(conn, tenant_id: str, recipient_id: str, supplier_id: str, notification_type: str, title: str, body: str, severity: str, timestamp: str) -> None:
    conn.execute(
        """
        INSERT INTO notifications(id, tenant_id, recipient_id, supplier_id, type, title, body, status, severity, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (f"NOT-{uuid.uuid4().hex[:10]}", tenant_id, recipient_id, supplier_id, notification_type, title, body, "unread", severity, timestamp),
    )


@router.post("/{supplier_id}/decisions")
def decide(supplier_id: str, payload: DecisionCreate, user: dict = Depends(current_user)) -> dict:
    with db_session() as conn:
        supplier = get_supplier_or_404(conn, user, supplier_id)
        if "Approver / Risk Committee" not in user["roles"] and "System Administrator" not in user["roles"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only approvers can make final decisions")
        if "System Administrator" not in user["roles"] and supplier["status"] != "pending_approval":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Supplier is not ready for final approval")
        allowed = {"approve": "approved", "reject": "rejected", "defer": "pending_review", "request_information": "pending_onboarding", "enhanced_due_diligence": "pending_review"}
        if payload.decision not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported decision")
        onboarding = conn.execute("SELECT id FROM onboarding_requests WHERE supplier_id = ? ORDER BY created_at DESC LIMIT 1", (supplier_id,)).fetchone()
        decision_id = f"DEC-{uuid.uuid4().hex[:10]}"
        timestamp = now()
        conn.execute(
            """
            INSERT INTO decisions(id, tenant_id, supplier_id, onboarding_request_id, decision, reason, decided_by, decided_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (decision_id, user["tenant_id"], supplier_id, onboarding["id"] if onboarding else None, payload.decision, payload.reason, user["id"], timestamp),
        )
        conn.execute("UPDATE suppliers SET status = ?, updated_at = ? WHERE id = ?", (allowed[payload.decision], timestamp, supplier_id))
        conn.execute(
            """
            UPDATE review_queue_items
            SET status = 'completed'
            WHERE tenant_id = ? AND supplier_id = ? AND assigned_role = 'Approver / Risk Committee' AND status = 'open'
            """,
            (user["tenant_id"], supplier_id),
        )
        if onboarding:
            conn.execute("UPDATE onboarding_requests SET status = ?, decided_at = ?, updated_at = ? WHERE id = ?", (payload.decision if payload.decision != "approve" else "approved", timestamp, timestamp, onboarding["id"]))
        decision_title = f"Supplier decision: {payload.decision.replace('_', ' ')}"
        decision_body = f"Final supplier decision recorded by Approver / Risk Committee. Reason: {payload.reason}"
        _notify_buyer_requester(
            conn,
            tenant_id=user["tenant_id"],
            supplier_id=supplier_id,
            notification_type="final_decision",
            title=decision_title,
            body=decision_body,
            severity="info",
            timestamp=timestamp,
        )
        _notify_supplier_users(
            conn,
            tenant_id=user["tenant_id"],
            supplier_id=supplier_id,
            notification_type="final_decision",
            title=decision_title,
            body=decision_body,
            severity="info",
            timestamp=timestamp,
        )
        write_audit(conn, tenant_id=user["tenant_id"], actor_type="user", actor_id=user["id"], action=f"decision.{payload.decision}", entity_type="supplier", entity_id=supplier_id, after=payload.model_dump())
        return get_supplier_or_404(conn, user, supplier_id)


def _notify_supplier_users(
    conn,
    *,
    tenant_id: str,
    supplier_id: str,
    notification_type: str,
    title: str,
    body: str,
    severity: str,
    timestamp: str,
) -> None:
    recipients = conn.execute(
        """
        SELECT DISTINCT user_id AS id
        FROM supplier_user_access
        WHERE tenant_id = ? AND supplier_id = ? AND status = 'active'
        """,
        (tenant_id, supplier_id),
    ).fetchall()
    for recipient in recipients:
        _insert_notification(conn, tenant_id, recipient["id"], supplier_id, notification_type, title, body, severity, timestamp)
