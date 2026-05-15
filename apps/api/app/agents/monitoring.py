from __future__ import annotations

from app.agents.base import Agent, AgentContext, AgentOutput


class MonitoringAgent(Agent):
    name = "Monitoring Agent"

    def run(self, context: AgentContext) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            payload={"detected_events": [], "refresh_plan": []},
            next_actions=[],
        )
