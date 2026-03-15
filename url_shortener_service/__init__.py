import os
import uuid
from flask import Flask, request as _req
from url_shortener_service.config import Config
from flask.json.provider import DefaultJSONProvider
from extensions import db
from url_shortener_service.routes import main_bp

def create_app():
    app = Flask(__name__)
    app.json_provider_class = DefaultJSONProvider
    app.json_provider_class.sort_keys = False
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(main_bp)

    @app.after_request
    def _trace(response):
        rid = _req.headers.get("X-Request-ID") or str(uuid.uuid4())
        response.headers["X-Request-ID"] = rid
        response.headers["X-Served-By"] = os.environ.get("HOSTNAME", "localhost")
        return response

    return app
