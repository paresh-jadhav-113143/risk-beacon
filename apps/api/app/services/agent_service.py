from __future__ import annotations

from app.agents import AgentOrchestrator


def run_assessment(conn, user: dict, supplier_id: str) -> dict:
    """Run the MVP pre-onboarding assessment through concrete agent modules."""
    return AgentOrchestrator(conn).run_pre_onboarding(user=user, supplier_id=supplier_id)
