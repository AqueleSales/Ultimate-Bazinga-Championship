import pytest

from bazinga import create_app
from bazinga.extensions import db


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    GOOGLE_CLIENT_ID = None
    GOOGLE_CLIENT_SECRET = None
    DISCORD_CLIENT_ID = None
    DISCORD_CLIENT_SECRET = None


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
