"""Configuration settings for article-generator."""

from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Determine root .env path if available
_CURRENT_DIR = Path(__file__).resolve().parent
_parents = _CURRENT_DIR.parents
_ROOT_ENV = _parents[2] / ".env" if len(_parents) > 2 else None
_LOCAL_ENV = _CURRENT_DIR.parent / ".env"

_env_files = []
if _LOCAL_ENV.exists():
    _env_files.append(str(_LOCAL_ENV))
if _ROOT_ENV and _ROOT_ENV.exists():
    _env_files.append(str(_ROOT_ENV))


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=tuple(_env_files),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ClickHouse Settings
    clickhouse_host: str = "localhost"
    clickhouse_http_port: int = 8123
    clickhouse_user: str = "statcast"
    clickhouse_password: str = "statcast_pass"
    clickhouse_db: str = "statcast"

    # Qdrant Settings
    qdrant_host: str = "localhost"
    qdrant_http_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_collection_name: str = "statcast_knowledge"

    # PostgreSQL Settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "statcast"
    postgres_password: str = "statcast_pass"
    postgres_db: str = "statcast"

    # Google Gemini Settings
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_embedding_model: str = "gemini-embedding-001"

    @property
    def qdrant_url(self) -> str:
        """Return the HTTP URL for Qdrant."""
        return f"http://{self.qdrant_host}:{self.qdrant_http_port}"


settings = Settings()
