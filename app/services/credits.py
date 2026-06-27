import math

from app.config import Settings, get_settings


def count_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def billable_credits(
    prompt_tokens: int,
    completion_tokens: int,
    multiplier: float,
    settings: Settings | None = None,
) -> int:
    settings = settings or get_settings()
    weighted = (
        prompt_tokens * settings.input_weight
        + completion_tokens * settings.output_weight
    )
    credits = weighted / 1000 * settings.credits_per_1k_weighted_tokens * multiplier
    return math.ceil(credits)


def estimate_credits(
    prompt: str,
    multiplier: float,
    max_tokens: int | None = None,
    settings: Settings | None = None,
) -> int:
    settings = settings or get_settings()
    expected_completion = (
        max_tokens if max_tokens is not None else settings.estimated_completion_tokens
    )
    return billable_credits(
        count_tokens(prompt), expected_completion, multiplier, settings
    )
