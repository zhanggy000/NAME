"""应用配置 · 从环境变量加载"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # DB
    database_url: str = "postgresql://postgres:postgres@localhost:5432/name_db"
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    llm_provider: str = "deepseek"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_base_url: str = "https://api.deepseek.com"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-7"

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # Monitoring
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.1


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
