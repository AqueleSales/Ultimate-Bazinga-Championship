import os
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "bazinga-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": NullPool,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False