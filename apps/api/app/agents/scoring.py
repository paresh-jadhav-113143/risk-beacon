from __future__ import annotations

from app.agents.base import Agent, AgentContext, AgentOutput


CATEGORY_WEIGHTS = {
    "compliance": 0.25,
    "financial": 0.15,
    "esg": 0.15,
    "cyber": 0.10,
    "operational": 0.10,
    "reputation": 0.10,
    "logistics": 0.05,
    "authenticity": 0.10,
    "anomaly": 0.05,
}


class ScoringAgent(Agent):
    name = "Scoring Agent"

    def run(self, context: AgentContext) -> AgentOutput:
        severity_points = {"low": 20, "medium": 55, "high": 78, "critical": 92}
        category_scores: dict[str, int] = {}
        for signal in context.risk_signals:
            points = int(severity_points[signal["severity"]] * float(signal["confidence"]))
            category_scores[signal["category"]] = max(category_scores.get(signal["category"], 0), points)
        composite = 0
        components = []
        for category, weight in CATEGORY_WEIGHTS.items():
            category_score = category_scores.get(category, 10)
            composite += int(category_score * weight)
            components.append(
                {
                    "category": category,
                    "score": category_score,
                    "weight": weight,
                    "explanation": f"{category.title()} score calculated from active risk signals",
                }
            )
        composite = max(0, min(100, composite))
        risk_level = "low" if composite <= 39 else "medium" if composite <= 69 else "high" if composite <= 84 else "critical"
        return AgentOutput(
            agent_name=self.name,
            confidence=1.0,
            payload={"composite_score": composite, "risk_level": risk_level, "components": components},
            next_actions=[{"action": "generate_recommendation"}],
        )
