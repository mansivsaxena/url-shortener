from flask import Flask
from flask.json.provider import DefaultJSONProvider
from extensions import db
from auth_service.config import Config
from auth_service.routes import auth_bp

def create_auth_app():
    app = Flask(__name__)
    app.json_provider_class = DefaultJSONProvider
    app.json_provider_class.sort_keys = False
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()
    
    app.register_blueprint(auth_bp)
    
    return app
