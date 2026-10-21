"""CRUD endpoints for the Note resource.

Every route requires login, and every query is filtered by the logged-in user's
id, so users can only ever see or change their own notes. A note that belongs
to someone else returns 404, the same as one that doesn't exist, so the API
never confirms that another user's note ID is real.
"""
from flask import current_app, g, request
from flask_restful import Resource
from marshmallow import ValidationError

from extensions import db
from helpers import flatten_errors, get_json_body, login_required
from models import Note
from schemas import note_schema, notes_schema


def _get_owned_note_or_none(note_id):
    return Note.query.filter_by(id=note_id, user_id=g.current_user.id).first()


NOT_FOUND = {"errors": ["Note not found."]}, 404


class NoteList(Resource):
    method_decorators = [login_required]

    def get(self):
        """GET /notes?page=1&per_page=10 -> one page of the user's notes, newest first."""
        max_per_page = current_app.config["MAX_PER_PAGE"]
        try:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", current_app.config["DEFAULT_PER_PAGE"]))
        except ValueError:
            return {"errors": ["page and per_page must be whole numbers."]}, 400
        if page < 1 or not 1 <= per_page <= max_per_page:
            return {"errors": [f"page must be 1 or more; per_page must be 1-{max_per_page}."]}, 400

        pagination = (
            Note.query.filter_by(user_id=g.current_user.id)
            .order_by(Note.created_at.desc(), Note.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return {
            "notes": notes_schema.dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }, 200

    def post(self):
        """POST /notes -> create a note owned by the logged-in user."""
        data = get_json_body()
        if data is None:
            return {"errors": ["Request body must be a JSON object."]}, 400
        try:
            valid = note_schema.load(data)
        except ValidationError as err:
            return {"errors": flatten_errors(err.messages)}, 422

        # The owner always comes from the session, never from the request body.
        note = Note(**valid, user_id=g.current_user.id)
        db.session.add(note)
        db.session.commit()
        return note_schema.dump(note), 201


class NoteDetail(Resource):
    method_decorators = [login_required]

    def get(self, note_id):
        note = _get_owned_note_or_none(note_id)
        if note is None:
            return NOT_FOUND
        return note_schema.dump(note), 200

    def patch(self, note_id):
        note = _get_owned_note_or_none(note_id)
        if note is None:
            return NOT_FOUND

        data = get_json_body()
        if not data:
            return {"errors": ["Send a JSON object with a title and/or content to update."]}, 400
        try:
            # partial=True: only the fields sent are required and validated.
            valid = note_schema.load(data, partial=True)
        except ValidationError as err:
            return {"errors": flatten_errors(err.messages)}, 422

        for field, value in valid.items():
            setattr(note, field, value)
        db.session.commit()
        return note_schema.dump(note), 200

    def delete(self, note_id):
        note = _get_owned_note_or_none(note_id)
        if note is None:
            return NOT_FOUND
        db.session.delete(note)
        db.session.commit()
        return {}, 204
