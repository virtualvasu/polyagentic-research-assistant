# app/config.py

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Central config. Values load from backend/.env, then process env (which wins)."""

    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    groq_api_key: str | None = None
    tavily_api_key: str | None = None

    ollama_base_url: str = "http://localhost:11434"
    ollama_models: str = "llama3.1:latest,llama3.1:8b,qwen2.5:7b"

    default_groq_model: str = "llama-3.3-70b-versatile"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 3

    checkpoint_db_path: str = "data/checkpoints.db"
    max_revisions: int = 3
    max_sub_queries: int = 3

    frontend_origin: str = "http://localhost:3000"

    # LangSmith tracing is picked up natively by langchain from these env vars
    # (LANGSMITH_TRACING, LANGSMITH_API_KEY, LANGSMITH_PROJECT) if set — no code
    # changes needed here, just documented in .env.example.

    @property
    def ollama_model_list(self) -> list[str]:
        return [m.strip() for m in self.ollama_models.split(",") if m.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
