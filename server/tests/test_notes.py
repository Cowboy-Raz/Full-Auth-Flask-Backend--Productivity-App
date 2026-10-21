"""Note CRUD, pagination, and ownership tests."""
import pytest


def create_note(client, title="Study", content="Review Flask sessions"):
    response = client.post("/notes", json={"title": title, "content": content})
    assert response.status_code == 201, response.get_json()
    return response.get_json()


@pytest.mark.parametrize(
    "method, url",
    [
        ("get", "/notes"),
        ("post", "/notes"),
        ("get", "/notes/1"),
        ("patch", "/notes/1"),
        ("delete", "/notes/1"),
    ],
)
def test_note_routes_require_login(client, method, url):
    response = getattr(client, method)(url, json={})
    assert response.status_code == 401
    assert response.get_json() == {"errors": ["You must be logged in to do that."]}


def test_full_crud(client, make_user):
    user = make_user("alice")

    note = create_note(client)
    assert note["title"] == "Study"
    assert note["user_id"] == user["id"]

    assert client.get(f"/notes/{note['id']}").get_json()["content"] == "Review Flask sessions"

    updated = client.patch(f"/notes/{note['id']}", json={"title": "  Study more  "})
    assert updated.status_code == 200
    assert updated.get_json()["title"] == "Study more"
    assert updated.get_json()["content"] == "Review Flask sessions"

    assert client.delete(f"/notes/{note['id']}").status_code == 204
    assert client.get(f"/notes/{note['id']}").status_code == 404


def test_create_validation(client, make_user):
    make_user("alice")
    assert client.post("/notes", json={"title": "", "content": "x"}).status_code == 422
    assert client.post("/notes", json={"title": "Only a title"}).status_code == 422
    assert client.post("/notes", json={"title": "x" * 101, "content": "x"}).status_code == 422
    # Clients may not choose the owner.
    response = client.post("/notes", json={"title": "Hi", "content": "x", "user_id": 99})
    assert response.status_code == 422


def test_patch_validation(client, make_user):
    make_user("alice")
    note = create_note(client)
    assert client.patch(f"/notes/{note['id']}", json={}).status_code == 400
    assert client.patch(f"/notes/{note['id']}", json={"title": ""}).status_code == 422
    assert client.patch(f"/notes/{note['id']}", json={"user_id": 2}).status_code == 422


def test_pagination(client, make_user):
    make_user("alice")
    for i in range(12):
        create_note(client, title=f"Note {i}")

    first = client.get("/notes?page=1&per_page=5").get_json()
    assert len(first["notes"]) == 5
    assert first["total"] == 12
    assert first["pages"] == 3
    assert first["has_next"] is True and first["has_prev"] is False

    last = client.get("/notes?page=3&per_page=5").get_json()
    assert len(last["notes"]) == 2
    assert last["has_next"] is False

    # Defaults: page 1, 10 per page
    default = client.get("/notes").get_json()
    assert default["page"] == 1 and default["per_page"] == 10 and len(default["notes"]) == 10

    # Past the last page: empty list, not an error
    assert client.get("/notes?page=99").get_json()["notes"] == []


@pytest.mark.parametrize("query", ["page=0", "per_page=0", "per_page=51", "page=abc"])
def test_pagination_rejects_bad_values(client, make_user, query):
    make_user("alice")
    assert client.get(f"/notes?{query}").status_code == 400


def test_users_cannot_touch_each_others_notes(app, make_user):
    alice = app.test_client()
    bob = app.test_client()
    make_user("alice", test_client=alice)
    make_user("bob", test_client=bob)

    note = create_note(alice, title="Private", content="Alice only")
    note_url = f"/notes/{note['id']}"

    assert bob.get("/notes").get_json()["total"] == 0
    assert bob.get(note_url).status_code == 404
    assert bob.patch(note_url, json={"content": "hacked"}).status_code == 404
    assert bob.delete(note_url).status_code == 404

    # Alice's note is unchanged.
    assert alice.get(note_url).get_json()["content"] == "Alice only"
