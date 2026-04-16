def test_create_session(client):
    response = client.post("/session", json={"user_name": "Tester"})
    assert response.status_code == 200
    assert "session_id" in response.json()
