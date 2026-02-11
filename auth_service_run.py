from auth_service import create_auth_app

app = create_auth_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001, debug=False, use_reloader=False)
