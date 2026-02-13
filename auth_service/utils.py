import json
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from flask import request

PBKDF2_ITERS = 120_000
SALT_BYTES = 16

def now_utc():
    return datetime.now(timezone.utc)

def get_json_body():
    body = request.get_json(silent=True)
    if isinstance(body, dict):
        return body

    req_body = (request.data or b"").strip()
    if not req_body:
        return None
    try:
        parsed = json.loads(req_body.decode("utf-8"))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None

# password hashing
def generate_salt() -> bytes:
    return secrets.token_bytes(SALT_BYTES)

def hash_password(password: str, salt: bytes) -> bytes:
    # PBKDF2-HMAC-SHA256
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERS,
    )

def verify_password(stored_hash: bytes, password: str, salt: bytes) -> bool:
    candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, stored_hash)

#todo- jwt tings
def generate_jwt_token(username, secret_key):
    # placeholder 
    return f"token-{username}"

def verify_jwt_token(token, secret_key):
    return False

def extract_jwt_from_request():
    # support "Bearer <token>" and raw token in Authorization header
    auth = request.headers.get("Authorization", "").strip()
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip()
    return auth
