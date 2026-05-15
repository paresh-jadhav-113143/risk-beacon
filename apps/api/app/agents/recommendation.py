from __future__ import annotations

from app.agents.base import Agent, AgentContext, AgentOutput
from app.integrations.llm import LLMClient


class RecommendationAgent(Agent):
    name = "Recommendation Agent"

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or LLMClient()

    def run(self, context: AgentContext) -> AgentOutput:
        if not context.score:
            raise ValueError("Recommendation Agent requires score in context")
        score = context.score["composite_score"]
        risk_level = context.score["risk_level"]
        action = "human_review" if risk_level in {"medium", "high", "critical"} else "recommend_onboarding"
        summary = self.llm_client.summarize_evidence(risk_level=risk_level, score=score, signals=context.risk_signals)
        return AgentOutput(
            agent_name=self.name,
            confidence=0.88,
            payload={
                "recommended_action": action,
                "recommended_owner_role": "Risk Analyst",
                "summary": summary,
                "rationale": [{"reason": "Recommendation derived from deterministic score and active risk signals"}],
            },
            next_actions=[{"action": "prepare_human_review"}],
        )
