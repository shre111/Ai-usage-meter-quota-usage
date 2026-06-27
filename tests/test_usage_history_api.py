def _configure(client, user_id, allowance, multiplier=1.0):
    client.put(
        f"/users/{user_id}/config",
        json={"monthly_allowance": allowance, "multiplier": multiplier},
    )


def test_usage_records_listed_after_generation(client):
    _configure(client, "alice", 1000)
    client.post("/users/alice/generate", json={"prompt": "first"})
    client.post("/users/alice/generate", json={"prompt": "second"})
    response = client.get("/users/alice/usage/records")
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 2
    assert all(r["status"] == "success" for r in records)
    assert all("multiplier_at_time" in r for r in records)


def test_usage_records_capture_rejected_and_failed(client):
    _configure(client, "bob", 1000)
    client.post("/users/bob/generate", json={"prompt": "ok"})
    client.post("/users/bob/generate", json={"prompt": "boom [FAIL]"})
    statuses = {r["status"] for r in client.get("/users/bob/usage/records").json()}
    assert "success" in statuses
    assert "failed" in statuses


def test_usage_records_unknown_user_404(client):
    assert client.get("/users/ghost/usage/records").status_code == 404


def test_usage_records_respects_limit(client):
    _configure(client, "carol", 1000)
    for _ in range(3):
        client.post("/users/carol/generate", json={"prompt": "x"})
    records = client.get("/users/carol/usage/records?limit=2").json()
    assert len(records) == 2
