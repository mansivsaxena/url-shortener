from flask import Flask
from flask.json.provider import DefaultJSONProvider
from extensions import db
from auth_service.config import Config

def create_auth_app():
    app = Flask(__name__)
    app.json_provider_class = DefaultJSONProvider
    app.json_provider_class.sort_keys = False
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        from models import User, URL  # noqa: F401
        db.create_all()
    
    from auth_service.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    return app
