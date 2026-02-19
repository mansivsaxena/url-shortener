import os


def _get_float_env(name, default):
    try:
        return float(os.getenv(name, default))
    except (ValueError, TypeError):
        return float(default)


class Config:
    DEBUG = False
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
    AUTH_VALIDATE_TIMEOUT_SECONDS = _get_float_env("AUTH_VALIDATE_TIMEOUT_SECONDS", 1.0)