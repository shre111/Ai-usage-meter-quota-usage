import pytest

from app.ai.base import AIGenerationError, GenerationResult
from app.ai.factory import get_provider
from app.main import app


def _configure(client, user_id, allowance, multiplier=1.0):
    client.put(
        f"/users/{user_id}/config",
        json={"monthly_allowance": allowance, "multiplier": multiplier},
    )


def test_generate_success_records_usage(client):
    _configure(client, "alice", 1000)
    response = client.post("/users/alice/generate", json={"prompt": "Write a haiku"})
    assert response.status_code == 200
    body = response.json()
    assert body["text"]
    assert body["usage"]["actual_credits"] > 0
    assert body["remaining_credits"] == 1000 - body["usage"]["actual_credits"]

    summary = client.get("/users/alice/usage").json()
    assert summary["used_credits"] == body["usage"]["actual_credits"]
    assert summary["reserved_credits"] == 0


def test_generate_quota_exceeded_returns_402(client):
    _configure(client, "bob", 5)
    response = client.post("/users/bob/generate", json={"prompt": "hello"})
    assert response.status_code == 402
    detail = response.json()["detail"]
    assert detail["error"] == "quota_exceeded"
    assert detail["remaining_credits"] == 5
    summary = client.get("/users/bob/usage").json()
    assert summary["used_credits"] == 0
    assert summary["reserved_credits"] == 0


def test_generate_unconfigured_user_404(client):
    response = client.post("/users/ghost/generate", json={"prompt": "hello"})
    assert response.status_code == 404


def test_ai_failure_releases_reservation(client):
    _configure(client, "carol", 1000)
    response = client.post("/users/carol/generate", json={"prompt": "do [FAIL] now"})
    assert response.status_code == 502
    summary = client.get("/users/carol/usage").json()
    assert summary["used_credits"] == 0
    assert summary["reserved_credits"] == 0


def test_partial_failure_records_committed_usage(client):
    _configure(client, "dave", 1000)
    response = client.post(
        "/users/dave/generate", json={"prompt": "[FAIL_PARTIAL] here"}
    )
    assert response.status_code == 502
    summary = client.get("/users/dave/usage").json()
    assert summary["used_credits"] > 0


def test_actual_lower_than_estimate(client):
    _configure(client, "erin", 1000)
    body = client.post("/users/erin/generate", json={"prompt": "hi"}).json()
    assert body["usage"]["actual_credits"] < body["usage"]["estimated_credits"]


def test_actual_higher_than_estimate_allows_overage(client):
    class BigProvider:
        def generate(self, prompt, max_tokens=None):
            return GenerationResult(text="big", prompt_tokens=4, completion_tokens=5000)

    app.dependency_overrides[get_provider] = lambda: BigProvider()
    try:
        _configure(client, "frank", 10)
        body = client.post("/users/frank/generate", json={"prompt": "hi"}).json()
        assert body["usage"]["actual_credits"] > body["usage"]["estimated_credits"]
        assert body["remaining_credits"] < 0
        # subsequent request is now blocked by the overage
        second = client.post("/users/frank/generate", json={"prompt": "hi"})
        assert second.status_code == 402
    finally:
        app.dependency_overrides.pop(get_provider, None)


def test_multiplier_affects_credits(client):
    _configure(client, "u_low", 1000, multiplier=1.0)
    _configure(client, "u_high", 1000, multiplier=2.0)
    low = client.post("/users/u_low/generate", json={"prompt": "same prompt"}).json()
    high = client.post("/users/u_high/generate", json={"prompt": "same prompt"}).json()
    assert high["usage"]["actual_credits"] == 2 * low["usage"]["actual_credits"]
