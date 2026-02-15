import json
import hashlib
import hmac
import secrets
import base64
import time
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

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _base64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)

# todo - provide sources for hashing alg used and hmac 
def generate_jwt_token(username, secret_key, exp_seconds: int = 3600):
    """
        Creating JWT (header.payload.signature) using HMAC-SHA256
        Payload:
        - username
        - iat (issued at)
        - exp (expiration time)
    """
    iat = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"username": username, "iat": iat, "exp": iat + int(exp_seconds)}

    header_b = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_b = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    header_b64 = _base64url_encode(header_b)
    payload_b64 = _base64url_encode(payload_b)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    key = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
    sig = hmac.new(key, signing_input, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_jwt_token(token, secret_key):
    """
        Verifying JWT using the provided secret_key
    """
    if not isinstance(token, str):
        return None
    
    parts = token.split(".")
    if len(parts) != 3:
        return None
    
    header_b64, payload_b64, sig_b64 = parts
    try:
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        key = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
        expected_sig = hmac.new(key, signing_input, hashlib.sha256).digest()
        actual_sig = _base64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_json = _base64url_decode(payload_b64)
        payload = json.loads(payload_json.decode("utf-8"))

        # check expiration
        now = int(time.time())
        exp = int(payload.get("exp", 0))
        if now >= exp:
            return None

        return payload
    except Exception:
        return None

def extract_jwt_from_request():
    # support "Bearer <token>" and raw token in Authorization header
    auth = request.headers.get("Authorization", "").strip()
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip()
    return auth
