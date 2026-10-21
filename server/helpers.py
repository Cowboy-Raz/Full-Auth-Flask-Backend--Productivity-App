"""Shared helpers for authentication and request handling."""
from functools import wraps

from flask import g, request, session

from extensions import db
from models import User


def get_current_user():
    """Return the logged-in User, or None.

    If the session points at a user that no longer exists, the stale session is cleared.
    """
    user_id = session.get("user_id")
    if user_id is None:
        return None
    user = db.session.get(User, user_id)
    if user is None:
        session.clear()
    return user


def login_required(func):
    """Reject the request with 401 unless a user is logged in.

    The logged-in user is stored on `g.current_user` for the resource to use.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return {"errors": ["You must be logged in to do that."]}, 401
        g.current_user = user
        return func(*args, **kwargs)

    return wrapper


def get_json_body():
    """Return the request's JSON object, or None if the body isn't a JSON object."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def flatten_errors(messages):
    """Turn marshmallow's {"field": ["msg"]} errors into a flat list of strings.

    The provided React client renders `errors` as a list of strings.
    """
    flat = []
    for field, field_messages in messages.items():
        if isinstance(field_messages, dict):
            flat.extend(flatten_errors(field_messages))
            continue
        for message in field_messages:
            # Our custom messages already name the field ("Title must be...");
            # marshmallow's generic ones ("Unknown field.") get a "field: " prefix.
            if field == "_schema" or field.split("_")[0] in message.lower():
                flat.append(message)
            else:
                flat.append(f"{field}: {message}")
    return flat
