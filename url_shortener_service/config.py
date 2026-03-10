import os
from dotenv import load_dotenv

load_dotenv()

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
    SQLALCHEMY_DATABASE_URI = f"postgresql://{user}:{pw}@localhost:{port}/{db_name}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False