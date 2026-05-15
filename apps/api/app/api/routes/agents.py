from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from app.api.dependencies import current_user
from app.db.sqlite import db_session

router = APIRouter(prefix="/agents", tags=["agents"])


AGENT_CATALOG = [
    {"name": "Intake Agent", "stage": "intake", "owner_role": "system"},
    {"name": "Document Intelligence Agent", "stage": "documents", "owner_role": "system"},
    {"name": "Entity Resolution Agent", "stage": "entity", "owner_role": "system"},
    {"name": "Sanctions and Compliance Agent", "stage": "risk_enrichment", "owner_role": "system"},
    {"name": "Financial Risk Agent", "stage": "risk_enrichment", "owner_role": "system"},
    {"name": "ESG Risk Agent", "stage": "risk_enrichment", "owner_role": "system"},
    {"name": "News and Reputation Agent", "stage": "risk_enrichment", "owner_role": "system"},
    {"name": "Logistics Risk Agent", "stage": "risk_enrichment", "owner_role": "system"},
    {"name": "Authenticity Agent", "stage": "risk_enrichment", "owner_role": "system"},
    {"name": "Anomaly Agent", "stage": "risk_enrichment", "owner_role": "system"},
    {"name": "Scoring Agent", "stage": "scoring", "owner_role": "system"},
    {"name": "Recommendation Agent", "stage": "recommendation", "owner_role": "system"},
    {"name": "Human Review Agent", "stage": "review", "owner_role": "Risk Analyst"},
    {"name": "Monitoring Agent", "stage": "monitoring", "owner_role": "system"},
    {"name": "Notification Agent", "stage": "notification", "owner_role": "system"},
]


@router.get("/catalog")
def catalog(user: dict = Depends(current_user)) -> list[dict]:
    return AGENT_CATALOG


@router.get("/runs")
def runs(user: dict = Depends(current_user), supplier_id: Optional[str] = None) -> list[dict]:
    query = """
        SELECT id, agent_name, supplier_id, onboarding_request_id, correlation_id, status, started_at, completed_at
        FROM agent_runs
        WHERE tenant_id = ?
    """
    params: list[str] = [user["tenant_id"]]
    if supplier_id:
        query += " AND supplier_id = ?"
        params.append(supplier_id)
    query += " ORDER BY started_at DESC LIMIT 100"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
