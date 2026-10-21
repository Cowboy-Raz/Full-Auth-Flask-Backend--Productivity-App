"""Session-based authentication endpoints.

Routes and response shapes match the provided `client-with-sessions` React app:
  POST /signup, POST /login, GET /check_session, DELETE /logout
Success responses return the user as {"id": ..., "username": ...}.
Error responses return {"errors": ["message", ...]}.
"""
from flask import session
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from extensions import db
from helpers import flatten_errors, get_current_user, get_json_body
from models import User
from schemas import login_schema, signup_schema, user_schema


def _start_session(user):
    # Clear first so an old session ID can't be reused after login.
    session.clear()
    session["user_id"] = user.id


class Signup(Resource):
    def post(self):
        data = get_json_body()
        if data is None:
            return {"errors": ["Request body must be a JSON object."]}, 400

        try:
            valid = signup_schema.load(data)
        except ValidationError as err:
            return {"errors": flatten_errors(err.messages)}, 422

        if User.query.filter_by(username=valid["username"]).first():
            return {"errors": ["Username is already taken."]}, 409

        user = User(username=valid["username"])
        user.password = valid["password"]
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            # Another request created the same username at the same moment.
            db.session.rollback()
            return {"errors": ["Username is already taken."]}, 409

        # The client expects signup to log the new user in.
        _start_session(user)
        return user_schema.dump(user), 201


class Login(Resource):
    def post(self):
        data = get_json_body()
        if data is None:
            return {"errors": ["Request body must be a JSON object."]}, 400

        try:
            valid = login_schema.load(data)
        except ValidationError as err:
            return {"errors": flatten_errors(err.messages)}, 422

        user = User.query.filter_by(username=valid["username"]).first()
        # Same message for unknown user and wrong password, so attackers can't
        # find out which usernames exist.
        if user is None or not user.authenticate(valid["password"]):
            return {"errors": ["Invalid username or password."]}, 401

        _start_session(user)
        return user_schema.dump(user), 200


class CheckSession(Resource):
    def get(self):
        user = get_current_user()
        if user is None:
            return {}, 401
        return user_schema.dump(user), 200


class Logout(Resource):
    def delete(self):
        if get_current_user() is None:
            return {"errors": ["You are not logged in."]}, 401
        session.clear()
        return {}, 204
