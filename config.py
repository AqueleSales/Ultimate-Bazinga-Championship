import os

from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # SQLite is used only as a convenient local fallback.
    # Set DATABASE_URL to the Neon PostgreSQL connection string for shared data.
    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///bazinga_local.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Keep connection health checks for long-running PostgreSQL deployments.
    # SQLite uses its own default engine options.
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"pool_pre_ping": True, "pool_recycle": 300}
        if database_url and database_url.startswith("postgresql://")
        else {}
    )

    SOCKETIO_MESSAGE_QUEUE = os.getenv("SOCKETIO_MESSAGE_QUEUE") or None
