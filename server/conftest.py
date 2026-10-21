"""Pytest fixtures. Living in server/ also puts server/ on the import path for the tests."""
import pytest

from app import create_app
from config import TestConfig
from extensions import db


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(client):
    """Sign up (and therefore log in) a user on the given test client."""

    def _make_user(username="alice", password="password123", test_client=None):
        c = test_client or client
        response = c.post(
            "/signup",
            json={"username": username, "password": password, "password_confirmation": password},
        )
        assert response.status_code == 201, response.get_json()
        return response.get_json()

    return _make_user
