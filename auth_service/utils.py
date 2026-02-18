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
def generate_salt():
    return secrets.token_bytes(SALT_BYTES)

def hash_password(password, salt):
    # PBKDF2-HMAC-SHA256
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERS,
    )

def verify_password(stored_hash, password, salt):
    candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, stored_hash)

def base64_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def base64_decode(encoded_data):
    padding = "=" * (-len(encoded_data) % 4)
    return base64.urlsafe_b64decode(encoded_data + padding)

def generate_signature(key, message):
    return hmac.new(key, message, hashlib.sha256).digest()

# todo - provide sources for hashing alg used and hmac 
def generate_jwt_token(username, secret_key, exp_seconds: int = 100):
    """
    - Create JWT token (header.payload.signature) 
    - Payload:
        - username
        - exp (expiration time)
    - Sign using HMAC-SHA256 with secret_key
    """
    time_issued = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"username": username, "exp": time_issued + int(exp_seconds)}

    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    header_b64 = base64_encode(header_json)
    payload_b64 = base64_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    key = secret_key.encode("utf-8") 
    sig = generate_signature(key, signing_input)
    sig_b64 = base64_encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_jwt_token(token, secret_key):
    """
    - Verify JWT token using the provided secret_key
        - Check structure (3 parts)
        - Verify signature
        - Check expiration
    - Return payload dict on success, None on failure
    """
    if not isinstance(token, str):
        return None
    
    parts = token.split(".")
    if len(parts) != 3:
        return None
    
    header_b64, payload_b64, sig_b64 = parts

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    key = secret_key.encode("utf-8") 

    expected_sig = generate_signature(key, signing_input)
    actual_sig = base64_decode(sig_b64)
    
    if not hmac.compare_digest(expected_sig, actual_sig):
        return None

    payload_json = base64_decode(payload_b64)
    payload = json.loads(payload_json.decode("utf-8"))

    # check expiration
    now = int(time.time())
    exp = int(payload.get("exp", 0))
    if now >= exp:
        return None

    return payload

def extract_jwt_from_request():
    # support "Bearer <token>" and raw token in Authorization header
    auth = request.headers.get("Authorization", "").strip()
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip()
    return auth


def validate_token_and_user(jwt_token, secret_key, users_dict, username_in_body=None):
    """
    - Verify the provided JWT token using secret_key
    - Validate that 
        - the payload contains a valid username
        - the user exists in users_dict
        - the stored token matches the provided token

    - Return the token payload dict on success, None on failure
    """
    payload = verify_jwt_token(jwt_token, secret_key)
    if not payload:
        return None

    username_in_payload = payload.get("username")
    if not username_in_payload:
        return None

    if username_in_body is not None and username_in_payload != username_in_body:
        return None

    user = users_dict.get(username_in_payload)
    if not user:
        return None

    stored = user.get("token")
    if not stored or not hmac.compare_digest(stored, jwt_token):
        return None

    return payload
