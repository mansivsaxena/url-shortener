import os
from auth_service import create_auth_app

app = create_auth_app()

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    app.run(host=host, port=8001, debug=False, use_reloader=False)