from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import current_user
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
        if not roles.intersection({"Supplier Admin", "Procurement Buyer", "System Administrator"}):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update supplier")
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
        get_supplier_or_404(conn, user, supplier_id)
        if not set(user["roles"]).intersection({"Supplier Admin", "Procurement Buyer", "System Administrator"}):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot add documents")
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


@router.post("/{supplier_id}/run-assessment")
def assess(supplier_id: str, user: dict = Depends(current_user)) -> dict:
    with db_session() as conn:
        get_supplier_or_404(conn, user, supplier_id)
        if not set(user["roles"]).intersection({"Procurement Buyer", "Risk Analyst", "System Administrator"}):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot run assessment")
        result = run_assessment(conn, user, supplier_id)
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


@router.post("/{supplier_id}/decisions")
def decide(supplier_id: str, payload: DecisionCreate, user: dict = Depends(current_user)) -> dict:
    with db_session() as conn:
        get_supplier_or_404(conn, user, supplier_id)
        if "Approver / Risk Committee" not in user["roles"] and "System Administrator" not in user["roles"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only approvers can make final decisions")
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
        if onboarding:
            conn.execute("UPDATE onboarding_requests SET status = ?, decided_at = ?, updated_at = ? WHERE id = ?", (payload.decision if payload.decision != "approve" else "approved", timestamp, timestamp, onboarding["id"]))
        write_audit(conn, tenant_id=user["tenant_id"], actor_type="user", actor_id=user["id"], action=f"decision.{payload.decision}", entity_type="supplier", entity_id=supplier_id, after=payload.model_dump())
        return get_supplier_or_404(conn, user, supplier_id)
