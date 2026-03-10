from flask import Blueprint, current_app, jsonify
from auth_service.utils import (
    generate_jwt_token,
    get_json_body,
    now_utc,
    generate_salt,
    hash_password,
    verify_password,
    extract_jwt_from_request,
    validate_token_and_user,
)
from models import User, db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/users", methods=["POST"])
def create_user():
    usernames_from_db = {user.username for user in User.query.all()}
    body = get_json_body()
    if not body:
        return "forbidden", 403

    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        return "forbidden", 403

    if username in usernames_from_db:
        return "duplicate", 409

    salt = generate_salt()
    pw_hash = hash_password(password, salt)
    t = now_utc()

    new_user = User(username=username, salt=salt, pw_hash=pw_hash, created_at=t, updated_at=t)
    db.session.add(new_user)
    db.session.commit()
    return "", 201


@auth_bp.route("/users", methods=["PUT"])
def update_user():
    body = get_json_body()
    if not body:
        return "forbidden", 403

    username = body.get("username")
    old_pw = body.get("old-password")
    new_pw = body.get("new-password")
    if not username or not old_pw or not new_pw:
        return "forbidden", 403

    user = User.query.filter_by(username=username).first()
    if not user:
        return "forbidden", 403

    if not verify_password(user.pw_hash, old_pw, user.salt):
        return "forbidden", 403

    # update password (rotate salt)
    new_salt = generate_salt()
    user.salt = new_salt
    user.pw_hash = hash_password(new_pw, new_salt)
    user.updated_at = now_utc()

    # invalidate the current token; user must log in again
    user.token = None
    db.session.commit()
    
    return "", 200

@auth_bp.route("/users/login", methods=["POST"])
def login_user():
    body = get_json_body()
    if not body:
        return "forbidden", 403

    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        return "forbidden", 403

    user = User.query.filter_by(username=username).first()
    if not user:
        return "forbidden", 403

    if not verify_password(user.pw_hash, password, user.salt):
        return "forbidden", 403

    provided_token = extract_jwt_from_request()
    if provided_token:
        # verify token was signed with correct key and payload contains valid username
        # also check that provided token matches stored token
        payload = validate_token_and_user(
            provided_token,
            current_app.config["JWT_SECRET_KEY"],
            username_in_body=username,
        )
        if payload:
            return jsonify({"token": provided_token}), 200

    # create a fresh token after successful auth
    token = generate_jwt_token(username, current_app.config["JWT_SECRET_KEY"])
    user.token = token
    db.session.commit()
    return jsonify({"token": token}), 200

@auth_bp.route("/users/validate", methods=["GET"])
def validate_user_token():
    # internal endpoint used by url_shortener_service to validate token in requests
    token = extract_jwt_from_request()
    if not token:
        return "forbidden", 403

    payload = validate_token_and_user(token, current_app.config["JWT_SECRET_KEY"])
    if not payload:
        return "forbidden", 403
    
    username = payload.get("sub")
    return jsonify({"username": username}), 200

@auth_bp.route("/users/logout", methods=["POST"])
def logout_user():
    token = extract_jwt_from_request()
    if not token:
        return "forbidden", 403

    payload = validate_token_and_user(token, current_app.config["JWT_SECRET_KEY"])
    if not payload:
        return "forbidden", 403

    username = payload.get("sub")
    user = User.query.filter_by(username=username).first()
    if user:
        user.token = None
        db.session.commit()

    return "", 200
