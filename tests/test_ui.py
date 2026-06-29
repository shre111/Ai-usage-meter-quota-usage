def test_ui_is_served(client):
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "AI Usage Metering" in response.text
