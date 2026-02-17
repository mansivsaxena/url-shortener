# UvA - Web Services and Cloud-Based Systems

## Group 9 - Assignment 2 (URL Shortener + Auth Microservice)

This repository contains two REST services:
- `auth_service` on `127.0.0.1:8001` for users, login, JWT issuing, and JWT validation.
- `url_shortener_service` on `127.0.0.1:8000` for URL management with per-user ownership.

The URL shortener does not know the JWT secret. It validates tokens by calling the auth service endpoint `GET /users/validate`.

## Directories

```text
url-shortener/
├── auth_service/
│   ├── __init__.py
│   ├── routes.py
│   └── utils.py
├── url_shortener_service/
│   ├── __init__.py
│   ├── auth_client.py
│   ├── config.py
│   ├── routes.py
│   └── utils.py
├── auth_service_run.py
├── url_shortener_service_run.py
├── test_app.py
├── test_1_marking_mk2.py
├── test_2_bonus.py
├── read_from.csv
└── requirements.txt
```

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Starting The Services

Terminal 1:

```bash
source .venv/bin/activate
python auth_service_run.py
```

Terminal 2:

```bash
source .venv/bin/activate
python url_shortener_service_run.py
```

## API Summary

Auth service:
- `POST /users`
- `PUT /users`
- `POST /users/login`
- `GET /users/validate`

URL shortener service:
- `GET /` (auth required)
- `POST /` (auth required)
- `DELETE /` (auth required, deletes current user's mappings)
- `GET /<id>` (public redirect endpoint)
- `PUT /<id>` (auth required, owner-only)
- `DELETE /<id>` (auth required, owner-only)
- `POST /bulk` (auth required)

## Testing

Legacy Assignment 1 tests (reference only):

```bash
python test_1_marking_mk2.py
```

These tests send unauthenticated management requests, so they are not expected to pass in the Assignment 2 version.

Assignment 2 tests:

```bash
python test_app.py
```

Note: The provided `test_2_bonus.py` file is from Assignment 1 and sends unauthenticated requests. In Assignment 2, management endpoints require Authorization.
