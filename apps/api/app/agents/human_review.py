from __future__ import annotations

from app.agents.base import Agent, AgentContext, AgentOutput


class HumanReviewAgent(Agent):
    name = "Human Review Agent"

    def run(self, context: AgentContext) -> AgentOutput:
        priority = context.score["risk_level"] if context.score else "medium"
        return AgentOutput(
            agent_name=self.name,
            confidence=1.0,
            payload={
                "assigned_role": "Risk Analyst",
                "priority": priority,
                "sections": [
                    {
                        "section": signal["category"],
                        "summary": signal["signal"],
                        "required_action": "validate_or_dismiss",
                    }
                    for signal in context.risk_signals
                ],
            },
            next_actions=[{"action": "create_review_queue_item", "owner_role": "Risk Analyst"}],
        )
