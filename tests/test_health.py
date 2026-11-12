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


def test_homepage_includes_accessible_cinematic_intro(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'id="cinematic-intro"' in response.data
    assert b'id="intro-skip"' in response.data
    assert b'id="replay-intro"' in response.data
    assert b'type="module"' in response.data


def test_homepage_exposes_oauth_providers_as_unconfigured_without_credentials(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Configurar Google OAuth" in response.data
    assert b"Configurar Discord OAuth" in response.data
    assert b'href="/auth/google"' not in response.data
    assert b'href="/auth/discord"' not in response.data


def test_oauth_login_routes_require_provider_credentials(client):
    assert client.get("/auth/google").status_code == 503
    assert client.get("/auth/discord").status_code == 503


def test_logout_clears_session(client):
    with client.session_transaction() as session:
        session["user_id"] = 123
        session["auth_provider"] = "google"
    response = client.post("/auth/logout")
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_cinematic_module_has_safe_three_js_fallback(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"await import('https://cdn.jsdelivr.net/npm/three" in response.data
    assert b"new THREE.Clock()" not in response.data
