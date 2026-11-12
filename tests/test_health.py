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
    assert b'id="intro-fallback-card"' in response.data
    assert b'id="intro-skip"' in response.data
    assert b'ABRIR CONVITE' not in response.data
    assert b'id="replay-intro"' in response.data
    assert b'type="module"' in response.data


def test_homepage_exposes_oauth_providers_as_unconfigured_without_credentials(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"CONFIGURAR GOOGLE OAUTH" in response.data
    assert b"CONFIGURAR DISCORD OAUTH" in response.data
    assert b'href="/auth/google"' not in response.data
    assert b'href="/auth/discord"' not in response.data


def test_oauth_login_routes_require_provider_credentials(client):
    assert client.get("/auth/google").status_code == 503
    assert client.get("/auth/discord").status_code == 503


def test_logout_clears_session(client):
    with client.session_transaction() as session:
        session["user_id"] = 123
        session["auth_provider"] = "google"
        session["_csrf_token"] = "test-csrf-token"
    with client.session_transaction() as session:
        token = session.get("_csrf_token")
    response = client.post("/auth/logout", data={"csrf_token": token})
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_cinematic_module_has_safe_three_js_fallback(client):
    response = client.get("/static/js/intro.js")
    assert response.status_code == 200
    assert b"await import('https://cdn.jsdelivr.net/npm/three" in response.data
    assert b"clock = new THREE.Clock()" in response.data
    assert b"function clickEnvelope(event)" in response.data
    assert b"function createExplosion()" in response.data
    assert b"envelope.visible = false" in response.data



def test_cinematic_intro_uses_ultimate_bazinga_championship_brand_without_bros(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"ULTIMATE BAZINGA CHAMPIONSHIP" in response.data
    assert b"BROS." not in response.data
    assert b"logo-fire-backdrop" in response.data
    assert b"hub-curtains" in response.data


def test_oauth_landing_preserves_authenticated_entry_screen(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"ENTRAR COMO VISITANTE" in response.data
    assert b"ENTRAR NA ARENA" in response.data
