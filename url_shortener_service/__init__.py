from flask import Flask
from url_shortener_service.config import Config
from flask.json.provider import DefaultJSONProvider
from extensions import db

def create_app():
    app = Flask(__name__)
    app.json_provider_class = DefaultJSONProvider
    app.json_provider_class.sort_keys = False
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        from models import User, URL  # noqa: F401
        db.create_all()
    
    from url_shortener_service.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
