def test_configure_user_creates_quota(client):
    response = client.put(
        "/users/alice/config",
        json={"monthly_allowance": 1000, "multiplier": 1.5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {"user_id": "alice", "monthly_allowance": 1000, "multiplier": 1.5}


def test_configure_user_partial_update(client):
    client.put("/users/bob/config", json={"monthly_allowance": 500, "multiplier": 1.0})
    response = client.put("/users/bob/config", json={"multiplier": 2.0})
    assert response.status_code == 200
    assert response.json()["monthly_allowance"] == 500
    assert response.json()["multiplier"] == 2.0


def test_configure_requires_a_field(client):
    response = client.put("/users/bob/config", json={})
    assert response.status_code == 422


def test_usage_summary_reports_remaining(client):
    client.put("/users/carol/config", json={"monthly_allowance": 200, "multiplier": 1.0})
    response = client.get("/users/carol/usage")
    assert response.status_code == 200
    body = response.json()
    assert body["remaining_credits"] == 200
    assert body["used_credits"] == 0


def test_usage_summary_unknown_user_404(client):
    response = client.get("/users/ghost/usage")
    assert response.status_code == 404


def test_different_users_have_independent_config(client):
    client.put("/users/u1/config", json={"monthly_allowance": 100, "multiplier": 1.0})
    client.put("/users/u2/config", json={"monthly_allowance": 999, "multiplier": 3.0})
    assert client.get("/users/u1/usage").json()["monthly_allowance"] == 100
    assert client.get("/users/u2/usage").json()["multiplier"] == 3.0
