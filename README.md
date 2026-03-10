# UvA - Web Services and Cloud-Based Systems

## Group 9 - Assignment 2 (URL Shortener + Auth Microservice)

This repository contains:
- `auth_service` (`127.0.0.1:8001`) for user management, login, JWT issuance, and JWT validation.
- `url_shortener_service` (`127.0.0.1:8000`) for per-user URL ownership and URL CRUD.
- Optional bonus deployment with Docker Compose + Nginx gateway on a single port (`127.0.0.1:8080`).

The shortener service does not know the JWT secret. It validates tokens by calling auth service `GET /users/validate`.

## Project Structure

```text
url-shortener/
├── auth_service/
│   ├── Dockerfile
│   ├── __init__.py
│   ├── routes.py
│   └── utils.py
├── url_shortener_service/
│   ├── Dockerfile
│   ├── __init__.py
│   ├── config.py
│   ├── routes.py
│   └── utils.py
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── auth_service_run.py
├── url_shortener_service_run.py
├── test_app.py
├── read_from.csv
└── requirements.txt
```
## PostgresSql Setup 
1. Install the Interactive Installer by EDB from https://www.postgresql.org/download/macosx/ (for MacOS)
2. While installing from the wizard, keep the default port as 5432 and remember the Superuser (postgres) password you set (will be used to connect to the DB from our app)
3. Start the Postgres server (either from terminal or from pgAdmin GUI)
4. Create the Database using the below query (you can do this either using the pgAdmin GUI or from your terminal, if you use the GUI make sure this is under the server which was started in the above step)
   ``` CREATE DATABASE "WebService-Assignment-URL-shortener"; ```
5. Modify the .env file with the password that you set for the superuser "postgres"
6. Install Driver which is the bridge between postgres and flask app
```pip install psycopg2-binary flask-sqlalchemy```
7. Now we setup the tables in our DB by running
   ``` python setup_db.py```
8. Now you can start your services and execute APIs to persist in the database. You can check your rows of data using pgAdmin and querying the tables created


## Local Setup (without Docker)

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the services in separate terminals:
```bash
python auth_service_run.py
```
```bash
python url_shortener_service_run.py
```

## Docker Compose + Nginx Gateway (Bonus)

Build and run all services:
```bash
docker compose up --build -d
```

Stop and remove containers:
```bash
docker compose down
```

Gateway is exposed on `127.0.0.1:8080`:
- Auth service via `/auth/*` (e.g., `POST /auth/users/login`)
- URL shortener via `/*` (e.g., `POST /`, `GET /<id>`)

## API Summary

Auth service endpoints:
- `POST /users`
- `PUT /users`
- `POST /users/login`
- `GET /users/validate`
- `POST /users/logout`

URL shortener endpoints:
- `GET /` (auth required)
- `POST /` (auth required)
- `DELETE /` (auth required, deletes current user's mappings)
- `GET /<id>` (public)
- `PUT /<id>` (auth required, owner-only)
- `DELETE /<id>` (auth required, owner-only)
- `POST /bulk` (auth required)

## Quick Gateway Examples

Create user:
```bash
curl -X POST http://127.0.0.1:8080/auth/users \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret"}'
```

Login:
```bash
curl -X POST http://127.0.0.1:8080/auth/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret"}'
```

## Testing

Run this after both services are running on local ports (`127.0.0.1:8001` and `127.0.0.1:8000`):
```bash
python test_app.py
```

Run the bonus tests through Docker + Nginx gateway:
```bash
python test_bonus.py
```
