from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QUOTA_", env_file=".env")

    app_name: str = "AI Usage Metering & Quota Service"
    database_url: str = "sqlite:///./quota.db"

    ai_provider: str = "mock"

    input_weight: float = 1.0
    output_weight: float = 3.0
    credits_per_1k_weighted_tokens: float = 10.0

    estimated_completion_tokens: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
