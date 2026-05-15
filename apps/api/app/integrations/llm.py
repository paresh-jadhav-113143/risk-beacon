from __future__ import annotations

import json

from app.config.settings import settings


class LLMClient:
    def _chat_model(self):
        if not settings.openai_api_key:
            return None
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return None
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            timeout=60,
        )

    def extract_structured_json(self, system_prompt: str, payload: dict) -> dict:
        model = self._chat_model()
        if not model:
            return {
                "provider": "local_fallback",
                "summary": "LLM extraction not configured. Set OPENAI_API_KEY and install langchain-openai.",
                "input_keys": sorted(payload.keys()),
            }
        response = model.invoke(
            [
                ("system", system_prompt),
                ("human", json.dumps(payload, default=str)),
            ]
        )
        content = response.content if hasattr(response, "content") else str(response)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"provider": "openai_langchain", "raw_text": content}

    def summarize_evidence(self, *, risk_level: str, score: int, signals: list[dict]) -> str:
        model = self._chat_model()
        if model:
            response = model.invoke(
                [
                    (
                        "system",
                        "Summarize supplier risk evidence concisely. Separate facts from interpretation. Do not make final decisions.",
                    ),
                    (
                        "human",
                        json.dumps(
                            {"risk_level": risk_level, "score": score, "signals": signals},
                            default=str,
                        ),
                    ),
                ]
            )
            return response.content if hasattr(response, "content") else str(response)
        categories = sorted({signal["category"] for signal in signals})
        category_text = ", ".join(categories) if categories else "no material categories"
        return (
            f"Supplier is {risk_level} risk with composite score {score}. "
            f"Review is based on {category_text}. Final decision requires authorized human approval."
        )
