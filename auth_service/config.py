import os


class Config:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    user = os.getenv("DB_USER")
    pw = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT")
    host = os.getenv("DB_HOST", "localhost")
    SQLALCHEMY_DATABASE_URI = f"postgresql://{user}:{pw}@{host}:{port}/{db_name}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
