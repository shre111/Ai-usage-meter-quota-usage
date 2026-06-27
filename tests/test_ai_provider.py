import pytest

from app.ai.base import AIGenerationError
from app.ai.factory import get_provider
from app.ai.mock import MockProvider


def test_mock_returns_deterministic_usage():
    provider = MockProvider(default_completion_tokens=100)
    result = provider.generate("hello world")
    again = provider.generate("hello world")
    assert result.prompt_tokens == again.prompt_tokens
    assert result.completion_tokens == 100
    assert result.total_tokens == result.prompt_tokens + 100


def test_mock_respects_max_tokens():
    provider = MockProvider()
    result = provider.generate("a prompt", max_tokens=42)
    assert result.completion_tokens == 42


def test_mock_forced_failure_raises():
    provider = MockProvider()
    with pytest.raises(AIGenerationError):
        provider.generate("please [FAIL] now")


def test_mock_partial_failure_carries_usage():
    provider = MockProvider()
    with pytest.raises(AIGenerationError) as exc:
        provider.generate("[FAIL_PARTIAL] here")
    assert exc.value.partial_usage is not None
    assert exc.value.partial_usage.prompt_tokens > 0


def test_factory_returns_mock_by_default():
    assert isinstance(get_provider(), MockProvider)
