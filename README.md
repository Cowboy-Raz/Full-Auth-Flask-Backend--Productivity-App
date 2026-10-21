# Productivity Notes API

A secure Flask REST API for a personal notes app. Users sign up and log in with
**session-based authentication**. Each user can create, read, update and delete
**their own** notes, and the notes list is paginated. Users can never see or
change anyone else's notes.

The API is built to work with the provided `client-with-sessions` React app.

## Features

- Sign up, log in, log out, and "check session" (stay logged in on page refresh)
- Passwords hashed with bcrypt; plain-text passwords are never stored
- Unique, case-insensitive usernames
- Full CRUD for notes, owned by the logged-in user
- Pagination on `GET /notes` (`?page=` and `?per_page=`)
- Input validation with Marshmallow; errors returned as `{"errors": [...]}`
- Database migrations (Flask-Migrate), seed data (Faker), and a pytest suite (23 tests)

## Tech stack

Python 3.11–3.13 · Flask 2.2 · Flask-RESTful · Flask-SQLAlchemy · Flask-Migrate ·
Flask-Bcrypt · Marshmallow · Faker · SQLite · pytest

## Project structure

```
productivity-notes-api/
├── Pipfile                 # Python dependencies
├── Pipfile.lock            # exact installed versions
├── README.md
├── .gitignore
└── server/
    ├── app.py              # Creates the Flask app and registers all routes
    ├── config.py           # Settings (secret key, database, pagination limits)
    ├── extensions.py       # db, migrate and bcrypt objects
    ├── models.py           # User and Note models
    ├── schemas.py          # Marshmallow validation/serialization schemas
    ├── helpers.py          # login_required decorator and shared helpers
    ├── seed.py             # Fills the database with example data
    ├── conftest.py         # pytest fixtures
    ├── pytest.ini          # pytest settings
    ├── resources/
    │   ├── auth.py         # /signup, /login, /check_session, /logout
    │   └── notes.py        # /notes and /notes/<id>
    ├── migrations/         # Database migration scripts
    └── tests/
        ├── test_auth.py
        └── test_notes.py
```

## Installation

Requires Python 3.11, 3.12 or 3.13 (the pinned Flask 2.2 packages do not run on
Python 3.14) and Pipenv.

```bash
pipenv install            # install dependencies into a virtual environment
pipenv shell              # activate it
cd server
flask db upgrade          # create the database tables from the migrations
python seed.py            # add example users and notes
```

The Pipfile asks for Python 3.12. If you have a different supported version,
use it instead: `pipenv install --python 3.11` (or `3.13`).

## Running the API

From the `server/` folder, with the Pipenv shell active:

```bash
python app.py
```

The API runs at **http://localhost:5555** (port 5555 matches the React
client's proxy). `flask run --port 5555` also works.

**Seeded accounts:** `demo`, `alex`, `jordan`, all with password `password123`.

### Optional: run the provided React client

```bash
cd client-with-sessions
npm install
npm start                 # opens http://localhost:4000
```

If `npm start` fails with `options.allowedHosts[0] should be a non-empty string`,
run `DANGEROUSLY_DISABLE_HOST_CHECK=true npm start` instead (a known
create-react-app proxy issue; safe for local development).

## API endpoints

All request and response bodies are JSON. Errors always look like
`{"errors": ["message", ...]}`.

### Authentication

| Method | Endpoint | Body | Success | Errors |
|---|---|---|---|---|
| POST | `/signup` | `username`, `password`, `password_confirmation` (optional) | **201** `{id, username}`; the user is logged in | 400 not JSON · 409 username taken · 422 invalid input |
| POST | `/login` | `username`, `password` | **200** `{id, username}` | 401 wrong username/password · 422 missing fields |
| GET | `/check_session` | none | **200** `{id, username}` | **401** `{}` when not logged in |
| DELETE | `/logout` | none | **204** (empty) | 401 not logged in |

Signup rules: username 3–50 characters (letters, numbers, `.`, `_`, `-`);
password at least 8 characters.

### Notes (login required)

| Method | Endpoint | Body | Success | Errors |
|---|---|---|---|---|
| GET | `/notes?page=1&per_page=10` | none | **200** paginated list (below) | 400 bad page values · 401 |
| POST | `/notes` | `title`, `content` | **201** the new note | 400 · 401 · 422 invalid input |
| GET | `/notes/<id>` | none | **200** the note | 401 · 404 |
| PATCH | `/notes/<id>` | `title` and/or `content` | **200** the updated note | 400 empty body · 401 · 404 · 422 |
| DELETE | `/notes/<id>` | none | **204** (empty) | 401 · 404 |

- `page` defaults to 1; `per_page` defaults to 10 (maximum 50). Notes are newest first.
- A note owned by another user returns **404**, exactly like a note that doesn't
  exist, so the API never reveals other users' note IDs.
- `user_id` is always taken from the session; sending it in a request body is rejected.

**Note object**

```json
{
  "id": 1,
  "title": "Study Flask",
  "content": "Finish the summative lab",
  "user_id": 1,
  "created_at": "2026-10-21T15:58:40",
  "updated_at": "2026-10-21T15:58:40"
}
```

**`GET /notes` response**

```json
{
  "notes": [ { "id": 15, "title": "...", "content": "...", "user_id": 1, "created_at": "...", "updated_at": "..." } ],
  "page": 1,
  "per_page": 10,
  "total": 15,
  "pages": 2,
  "has_next": true,
  "has_prev": false
}
```

## Testing

From `server/` with the Pipenv shell active:

```bash
pytest
```

The tests use an in-memory database, so they don't touch your data. They cover
signup/login/logout, sessions, validation, CRUD, pagination, and that one user
cannot read, edit or delete another user's notes.

### Manual testing with curl

```bash
# log in and save the session cookie
curl -i -c cookies.txt -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"password123"}' http://localhost:5555/login

# use the cookie for protected routes
curl -i -b cookies.txt "http://localhost:5555/notes?page=1&per_page=5"
curl -i -b cookies.txt -H "Content-Type: application/json" \
  -d '{"title":"New note","content":"Hello"}' http://localhost:5555/notes
curl -i -b cookies.txt -X DELETE http://localhost:5555/logout
```

## Security notes

- The secret key that signs session cookies has a development default. Set
  your own with `export SECRET_KEY="<long random string>"` before running anywhere public.
- Session cookies are `HttpOnly` and `SameSite=Lax`. For HTTPS deployments,
  set `SESSION_COOKIE_SECURE=true`.
- This is a learning project with pinned 2022-era packages; update the
  dependencies and add CSRF protection before any real deployment.
