import os
from url_shortener_service import create_app

app = create_app()

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    app.run(host=host, port=8000, debug=False, use_reloader=False)