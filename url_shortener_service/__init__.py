from flask import Flask
from url_shortener_service.config import Config
from flask.json.provider import DefaultJSONProvider
from url_shortener_service.extensions import db

def create_app():
    app = Flask(__name__)
    app.json_provider_class = DefaultJSONProvider
    app.json_provider_class.sort_keys = False
    app.config.from_object(Config)

    db.init_app(app)
    
    from url_shortener_service.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
