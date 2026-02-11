from flask import Flask
from flask.json.provider import DefaultJSONProvider

def create_auth_app():
    app = Flask(__name__)
    app.json_provider_class = DefaultJSONProvider
    app.json_provider_class.sort_keys = False
    
    # JWT secret key for token generation and validation
    app.config['JWT_SECRET_KEY'] = 'dummy-secret-key'
    
    from auth_service.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    return app
