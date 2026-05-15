from __future__ import annotations

from app.agents.base import Agent, AgentContext, AgentOutput


class NotificationAgent(Agent):
    name = "Notification Agent"

    def run(self, context: AgentContext) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            payload={"notifications": [], "failed_deliveries": []},
            next_actions=[],
        )
