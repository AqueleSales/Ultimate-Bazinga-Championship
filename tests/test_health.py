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
    assert b"aria-label=\"Ultimate Bazinga Championship\"" in response.data
    assert b"BROS." not in response.data
    assert b"logo-fire-backdrop" in response.data
    assert b"hub-curtains" in response.data


def test_oauth_landing_preserves_authenticated_entry_screen(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"id=\"guest-entry\"" not in response.data


def test_oauth_provider_buttons_are_enabled_when_credentials_are_present():
    from bazinga import create_app
    from bazinga.extensions import db

    class OAuthTestConfig:
        TESTING = True
        SECRET_KEY = "test-secret-key"
        SQLALCHEMY_DATABASE_URI = "sqlite://"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SQLALCHEMY_ENGINE_OPTIONS = {}
        GOOGLE_CLIENT_ID = "google-test-client"
        GOOGLE_CLIENT_SECRET = "google-test-secret"
        DISCORD_CLIENT_ID = "discord-test-client"
        DISCORD_CLIENT_SECRET = "discord-test-secret"

    application = create_app(OAuthTestConfig)
    with application.app_context():
        db.create_all()
        response = application.test_client().get("/")
        assert response.status_code == 200
        assert b'href="/auth/google"' in response.data
        assert b'href="/auth/discord"' in response.data
        db.session.remove()
        db.drop_all()


def test_oauth_login_routes_return_provider_specific_setup_message_when_unconfigured(client):
    google = client.get("/auth/google")
    discord = client.get("/auth/discord")
    assert google.status_code == 503
    assert b"Google" in google.data
    assert discord.status_code == 503
    assert b"Discord" in discord.data


def test_module_pages_require_authentication(client):
    for path in ("/competitions", "/matches", "/ranking", "/achievements", "/community"):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/?screen=auth")


def test_authenticated_user_can_open_each_module_page(app, client):
    from bazinga.models import User

    with app.app_context():
        user = User(name="Competidor de Teste", email="competidor@example.test")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as session:
        session["user_id"] = user_id

    for path, heading in (
        ("/competitions", b"CAMPEONATOS"),
        ("/matches", b"PARTIDAS"),
        ("/ranking", b"RANKING"),
        ("/achievements", b"CONQUISTAS"),
        ("/community", b"COMUNIDADE"),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert heading in response.data


def test_logout_returns_to_login_screen_without_replaying_intro(client):
    with client.session_transaction() as session:
        session["user_id"] = 123
        session["_csrf_token"] = "test-token"
    response = client.post("/auth/logout", data={"csrf_token": "test-token"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/?screen=auth")
