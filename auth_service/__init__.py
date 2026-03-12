import os
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from extensions import db

def create_auth_app():
    app = Flask(__name__)
    app.json_provider_class = DefaultJSONProvider
    app.json_provider_class.sort_keys = False
    
    # secret key to sign JWT tokens - read from environment, never hardcoded
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    
    user = os.getenv('DB_USER')
    pw = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{user}:{pw}@{host}:{port}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from models import User, URL  # noqa: F401
        db.create_all()
    
    from auth_service.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    return app
