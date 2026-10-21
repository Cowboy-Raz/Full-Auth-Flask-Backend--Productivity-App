"""Entry point: builds the Flask app and registers every route.

Run from the server/ folder:
    python app.py               (port 5555, debug on)
    flask run --port 5555
"""
from flask import Flask
from flask_restful import Api

from config import Config
from extensions import bcrypt, db, migrate
import models  # noqa: F401  (imported so Flask-Migrate can see the models)
from resources.auth import CheckSession, Login, Logout, Signup
from resources.notes import NoteDetail, NoteList


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.json.sort_keys = False  # keep JSON keys in the order we build them

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)  # batch mode = SQLite-safe ALTERs
    bcrypt.init_app(app)

    api = Api(app)
    api.add_resource(Signup, "/signup", endpoint="signup")
    api.add_resource(Login, "/login", endpoint="login")
    api.add_resource(CheckSession, "/check_session", endpoint="check_session")
    api.add_resource(Logout, "/logout", endpoint="logout")
    api.add_resource(NoteList, "/notes", endpoint="notes")
    api.add_resource(NoteDetail, "/notes/<int:note_id>", endpoint="note_detail")

    @app.get("/")
    def index():
        return {"message": "Productivity Notes API is running."}, 200

    return app


app = create_app()

if __name__ == "__main__":
    # Port 5555 matches the "proxy" setting in the provided React client.
    app.run(port=5555, debug=True)
