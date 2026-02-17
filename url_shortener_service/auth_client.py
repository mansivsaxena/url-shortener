import requests
from flask import current_app


def validate_request_token(req):
    auth_header = (req.headers.get("Authorization") or "").strip()
    if not auth_header:
        return False, None

    base_url = current_app.config.get("AUTH_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
    validate_url = f"{base_url}/users/validate"
    timeout = float(current_app.config.get("AUTH_VALIDATE_TIMEOUT_SECONDS", 1.0))

    try:
        response = requests.get(
            validate_url,
            headers={"Authorization": auth_header},
            timeout=timeout,
        )
    except requests.RequestException:
        return False, None

    if response.status_code != 200:
        return False, None

    try:
        payload = response.json()
    except ValueError:
        return False, None

    username = payload.get("username") if isinstance(payload, dict) else None
    if not isinstance(username, str) or not username:
        return False, None

    return True, username
