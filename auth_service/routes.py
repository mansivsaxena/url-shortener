from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

users = {}

@auth_bp.route("/users", methods=["POST"])
def create_user():
    return "", 201

@auth_bp.route("/users", methods=["PUT"])
def update_user():
    return "", 200

@auth_bp.route("/users/login", methods=["POST"])
def login_user():
    return "", 200
