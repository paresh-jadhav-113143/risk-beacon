from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    secret_key: str = "change-me-local-secret"
    database_url: str = "sqlite:///./data/risk_beacon.db"
    sqlite_busy_timeout_ms: int = 5000
    api_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175,http://localhost:5176,http://127.0.0.1:5176,http://localhost:5177,http://127.0.0.1:5177,http://localhost:5178,http://127.0.0.1:5178"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    tavily_api_key: Optional[str] = None
    serpapi_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    sec_user_agent: str = "risk-beacon-local@example.com"
    sanctions_provider_base_url: Optional[str] = None
    sanctions_provider_api_key: Optional[str] = None
    news_provider_base_url: Optional[str] = None
    news_provider_api_key: Optional[str] = None
    local_storage_root: str = "./storage"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sqlite_path(self) -> Path:
        if not self.database_url.startswith("sqlite:///"):
            raise ValueError("MVP only supports sqlite:/// DATABASE_URL values")
        return Path(self.database_url.replace("sqlite:///", "", 1))

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
