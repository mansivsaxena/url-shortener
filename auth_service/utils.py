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
