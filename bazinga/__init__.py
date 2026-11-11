from flask import Flask

from config import Config
from .extensions import db, migrate, socketio


def create_app(config_object=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY não configurada. Defina uma chave secreta no arquivo .env."
        )

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(
        app,
        message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"),
    )

    from . import models  # noqa: F401
    from .routes.main import main_bp

    app.register_blueprint(main_bp)

    return app
