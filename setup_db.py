from url_shortener_service import create_app 
from url_shortener_service.extensions import db

app = create_app()

def initialize():
    with app.app_context():
        print("Configuring database...")
        db.drop_all() 
        db.create_all() 
        print("Database initialized successfully.")

if __name__ == "__main__":
    initialize()