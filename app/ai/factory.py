from app.ai.base import AIProvider
from app.ai.mock import MockProvider
from app.config import get_settings


def get_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider == "mock":
        return MockProvider()
    raise ValueError(f"Unknown AI provider: {settings.ai_provider}")
