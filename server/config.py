"""Application configuration.

Values can be overridden with environment variables so secrets never have to
live in the code that gets pushed to GitHub.
"""
import os


class Config:
    # Signs the session cookie. Set a real value with `export SECRET_KEY=...`
    # anywhere other than your own machine.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key-change-me")

    # A relative SQLite path is stored in Flask's instance/ folder (server/instance/app.db).
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session cookie hardening: JavaScript can't read it, and it isn't sent on
    # cross-site POSTs.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

    # Pagination limits for GET /notes
    DEFAULT_PER_PAGE = 10
    MAX_PER_PAGE = 50


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite://"  # in-memory database, wiped after each test
