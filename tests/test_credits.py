from app.config import get_settings
from app.services.credits import billable_credits, count_tokens, estimate_credits


def test_billable_credits_weights_output_more_than_input():
    settings = get_settings()
    credits = billable_credits(1000, 1000, multiplier=1.0, settings=settings)
    assert credits == 40


def test_multiplier_scales_credits_linearly():
    base = billable_credits(1000, 1000, multiplier=1.0)
    doubled = billable_credits(1000, 1000, multiplier=2.0)
    assert doubled == base * 2


def test_different_users_get_different_credits_for_same_usage():
    standard = billable_credits(500, 500, multiplier=1.0)
    premium = billable_credits(500, 500, multiplier=1.5)
    assert premium > standard


def test_estimate_uses_configured_completion_estimate():
    settings = get_settings()
    expected = billable_credits(
        count_tokens("hello"),
        settings.estimated_completion_tokens,
        multiplier=1.0,
        settings=settings,
    )
    assert estimate_credits("hello", multiplier=1.0) == expected
