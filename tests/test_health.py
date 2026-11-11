def test_health_endpoint_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {
        "status": "ok",
        "service": "ultimate-bazinga-championship",
    }


def test_homepage_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Ultimate Bazinga" in response.data
