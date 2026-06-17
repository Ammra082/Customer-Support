"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── LLM ──────────────────────────────────────────────────────────────────
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = Field(default="development", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite:///./data/taskflow.db", env="DATABASE_URL"
    )

    # ── RAG ───────────────────────────────────────────────────────────────────
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL"
    )
    faiss_index_path: str = Field(
        default="./data/faiss_index", env="FAISS_INDEX_PATH"
    )
    faq_dataset_path: str = Field(
        default="./data/taskflow_support_dataset_150.jsonl", env="FAQ_DATASET_PATH"
    )
    retrieval_confidence_threshold: float = Field(
        default=0.45, env="RETRIEVAL_CONFIDENCE_THRESHOLD"
    )

    # ── API ───────────────────────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")

    # ── Frontend ──────────────────────────────────────────────────────────────
    backend_url: str = Field(default="http://localhost:8000", env="BACKEND_URL")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def validate_api_key(self) -> None:
        """Raise a descriptive error if the Groq API key is missing."""
        if not self.groq_api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set.\n"
                "1. Copy .env.example to .env\n"
                "2. Add your Groq API key (https://console.groq.com)\n"
                "3. Restart the server"
            )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    # Walk up from CWD to find .env
    env_path = Path(".env")
    if not env_path.exists():
        alt = Path(__file__).parent.parent.parent / ".env"
        if alt.exists():
            os.chdir(alt.parent)
    return Settings()
