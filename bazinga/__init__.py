import secrets

from flask import Flask, session

from config import Config
from .extensions import db, migrate, oauth, socketio


def create_app(config_object=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY não configurada. Defina uma chave secreta no arquivo .env."
        )

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=app.config.get("SESSION_COOKIE_SECURE", False),
        PERMANENT_SESSION_LIFETIME=app.config.get("PERMANENT_SESSION_LIFETIME"),
    )

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"))

    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    oauth.register(
        name="discord",
        client_id=app.config.get("DISCORD_CLIENT_ID"),
        client_secret=app.config.get("DISCORD_CLIENT_SECRET"),
        authorize_url="https://discord.com/oauth2/authorize",
        access_token_url="https://discord.com/api/oauth2/token",
        api_base_url="https://discord.com/api/",
        client_kwargs={"scope": "identify email"},
    )

    from . import models  # noqa: F401
    from .routes.auth import auth_bp
    from .routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # The project currently has no Alembic migration history. Create missing
    # tables for local development and first deployment; create_all never alters
    # existing tables. Future schema changes should use Flask-Migrate migrations.
    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_auth_state():
        from .models import User

        user_id = session.get("user_id")
        user = db.session.get(User, user_id) if user_id else None
        return {
            "current_user": user if user and user.is_active else None,
            "google_oauth_enabled": bool(app.config.get("GOOGLE_CLIENT_ID") and app.config.get("GOOGLE_CLIENT_SECRET")),
            "discord_oauth_enabled": bool(app.config.get("DISCORD_CLIENT_ID") and app.config.get("DISCORD_CLIENT_SECRET")),
            "csrf_token": session.setdefault("_csrf_token", secrets.token_urlsafe(32)),
        }

    return app
