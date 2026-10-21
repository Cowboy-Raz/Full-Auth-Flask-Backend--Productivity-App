"""Marshmallow schemas: validate incoming JSON and shape outgoing JSON.

Unknown fields are rejected (marshmallow's default), so a client can't sneak in
fields like `user_id` or `id` to take over someone else's record.
"""
from marshmallow import Schema, ValidationError, fields, pre_load, validate, validates_schema


def _max_72_bytes(value):
    # bcrypt only uses the first 72 bytes of a password; reject longer ones.
    if len(value.encode("utf-8")) > 72:
        raise ValidationError("Password must be 72 bytes or fewer.")


class UserSchema(Schema):
    """Public view of a user. The password hash is never included."""

    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)


class SignupSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50, error="Username must be 3-50 characters."),
            validate.Regexp(
                r"^[A-Za-z0-9_.-]+$",
                error="Username may only contain letters, numbers, '.', '_' and '-'.",
            ),
        ],
    )
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, error="Password must be at least 8 characters."),
            _max_72_bytes,
        ],
    )
    # Sent by the provided React client. Optional so Postman tests can skip it.
    password_confirmation = fields.Str()

    @pre_load
    def normalize_username(self, data, **kwargs):
        # Usernames are case-insensitive: "Raz" and "raz" are the same account.
        if isinstance(data.get("username"), str):
            data = {**data, "username": data["username"].strip().lower()}
        return data

    @validates_schema
    def passwords_match(self, data, **kwargs):
        confirmation = data.get("password_confirmation")
        if confirmation is not None and confirmation != data.get("password"):
            raise ValidationError("Passwords do not match.", "password_confirmation")


class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

    @pre_load
    def normalize_username(self, data, **kwargs):
        if isinstance(data.get("username"), str):
            data = {**data, "username": data["username"].strip().lower()}
        return data


class NoteSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100, error="Title must be 1-100 characters."),
    )
    content = fields.Str(
        required=True,
        validate=validate.Length(min=1, error="Content cannot be empty."),
    )
    user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @pre_load
    def strip_title(self, data, **kwargs):
        if isinstance(data.get("title"), str):
            data = {**data, "title": data["title"].strip()}
        return data


user_schema = UserSchema()
signup_schema = SignupSchema()
login_schema = LoginSchema()
note_schema = NoteSchema()
notes_schema = NoteSchema(many=True)
