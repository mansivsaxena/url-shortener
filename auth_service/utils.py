import json
from flask import request

def bad_request():
    return "error", 400

def get_json_body():
    body = request.get_json(silent=True)
    if body is not None:
        return body
    req_body = (request.data or b"").strip()
    if not req_body:
        return None
    try:
        return json.loads(req_body.decode("utf-8"))
    except Exception:
        return None

def hash_password(password):
    return ""

def verify_password(hash, password):
    return False

def generate_jwt_token(username, secret_key):
    return ""

def verify_jwt_token(token, secret_key):
    return False

def extract_jwt_from_request():
    return ""
