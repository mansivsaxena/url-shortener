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
    
    user = os.getenv('DB_USER')
    pw = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    port = os.getenv('DB_PORT')
    host = os.getenv('DB_HOST', 'localhost')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{user}:{pw}@{host}:{port}/{db_name}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 2, "max_overflow": 3}