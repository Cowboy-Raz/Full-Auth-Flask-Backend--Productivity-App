"""Auth flow tests, mirroring the requests the provided React client makes."""
from extensions import db
from models import User


def test_signup_creates_user_logs_in_and_hashes_password(client, make_user):
    body = make_user("alice")
    assert body == {"id": body["id"], "username": "alice"}

    # Signup logs the user in (the client expects this).
    assert client.get("/check_session").get_json()["username"] == "alice"

    user = db.session.get(User, body["id"])
    assert user._password_hash != "password123"
    assert user.authenticate("password123")
    assert not user.authenticate("wrong-password")


def test_signup_rejects_duplicate_username_case_insensitive(client, make_user):
    make_user("alice")
    response = client.post("/signup", json={"username": "ALICE", "password": "password123"})
    assert response.status_code == 409
    assert response.get_json()["errors"] == ["Username is already taken."]


def test_signup_validation_errors_are_a_list_of_strings(client):
    response = client.post(
        "/signup",
        json={"username": "x", "password": "short", "password_confirmation": "different"},
    )
    assert response.status_code == 422
    errors = response.get_json()["errors"]
    assert isinstance(errors, list) and all(isinstance(e, str) for e in errors)
    assert "Passwords do not match." in errors or len(errors) >= 2


def test_signup_password_confirmation_must_match(client):
    response = client.post(
        "/signup",
        json={"username": "alice", "password": "password123", "password_confirmation": "nope12345"},
    )
    assert response.status_code == 422
    assert "Passwords do not match." in response.get_json()["errors"]


def test_signup_requires_json_body(client):
    response = client.post("/signup", data="not json", content_type="text/plain")
    assert response.status_code == 400


def test_login_success_and_failure(client, make_user, app):
    make_user("alice")
    client.delete("/logout")

    bad = client.post("/login", json={"username": "alice", "password": "wrong-password"})
    assert bad.status_code == 401
    assert bad.get_json() == {"errors": ["Invalid username or password."]}

    unknown = client.post("/login", json={"username": "nobody", "password": "password123"})
    assert unknown.status_code == 401

    good = client.post("/login", json={"username": "Alice", "password": "password123"})
    assert good.status_code == 200
    assert good.get_json()["username"] == "alice"


def test_check_session_when_logged_out(client):
    response = client.get("/check_session")
    assert response.status_code == 401
    assert response.get_json() == {}


def test_logout_ends_session(client, make_user):
    make_user("alice")
    response = client.delete("/logout")
    assert response.status_code == 204
    assert client.get("/check_session").status_code == 401
    # Logging out twice is an error.
    assert client.delete("/logout").status_code == 401


def test_session_persists_across_requests_like_a_page_refresh(client, make_user):
    make_user("alice")
    for _ in range(3):
        assert client.get("/check_session").status_code == 200
