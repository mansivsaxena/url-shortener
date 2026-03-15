# UvA - Web Services and Cloud-Based Systems

## Group 9 - Assignment 3 (Containers & Kubernetes)

This repository contains:
- `auth_service` for user management, login, JWT issuance, and JWT validation.
- `url_shortener_service` for per-user URL ownership and URL CRUD.
- `nginx` as a single gateway in front of both services.
- `postgres` as the shared persistent database.

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
├── k8s/
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── postgres-pvc.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-service.yaml
│   ├── auth-deployment.yaml
│   ├── auth-service.yaml
│   ├── shortener-deployment.yaml
│   ├── shortener-service.yaml
│   ├── nginx-configmap.yaml
│   ├── nginx-deployment.yaml
│   ├── nginx-service.yaml
│   └── shortener-hpa.yaml
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .env
├── auth_service_run.py
├── url_shortener_service_run.py
├── test_app.py
└── requirements.txt
```

## Assignment 3 Files

For assignment 3.1, the main files are:
- `docker-compose.yml`
- `auth_service/Dockerfile`
- `url_shortener_service/Dockerfile`
- `nginx/nginx.conf`
- `.env`

For assignment 3.2, the main files are:
- `k8s/configmap.yaml`
- `k8s/secret.yaml`
- `k8s/postgres-pvc.yaml`
- `k8s/postgres-deployment.yaml`
- `k8s/postgres-service.yaml`
- `k8s/auth-deployment.yaml`
- `k8s/auth-service.yaml`
- `k8s/shortener-deployment.yaml`
- `k8s/shortener-service.yaml`
- `k8s/nginx-configmap.yaml`
- `k8s/nginx-deployment.yaml`
- `k8s/nginx-service.yaml`
- `k8s/shortener-hpa.yaml`

## Docker Compose + Nginx Gateway

Build and run all services:

```bash
docker compose up --build -d
```

Stop and remove containers:

```bash
docker compose down
```

Remove containers and the Postgres volume:

```bash
docker compose down -v
```

Gateway is exposed on `127.0.0.1:8080`:
- Auth service via `/auth/*`
- URL shortener via `/*`

Persistence is handled through the `pgdata` Docker volume in `docker-compose.yml`, so data survives normal restarts and `docker compose down` unless the volume is removed.

## Kubernetes Deployment

All Kubernetes manifests are in the `k8s/` directory.

The Kubernetes setup uses:
- a `postgres` Deployment + Service + PVC
- an `auth` Deployment + Service
- a `shortener` Deployment + Service
- a `gateway` Deployment + NodePort Service

The gateway is exposed through NodePort `30080`.

The shortener runs with 3 replicas for the replication part of the assignment. The bonus HPA is defined in `k8s/shortener-hpa.yaml`.

## API Summary

Auth service endpoints:
- `POST /auth/users`
- `PUT /auth/users`
- `POST /auth/users/login`
- `GET /auth/users/validate`
- `POST /auth/users/logout`

URL shortener endpoints:
- `GET /` (auth required)
- `POST /` (auth required)
- `DELETE /` (auth required)
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

Shorten a URL:

```bash
curl -X POST http://127.0.0.1:8080/ \
  -H "Authorization: <token>" \
  -H "Content-Type: application/json" \
  -d '{"value":"https://example.com"}'
```

## Testing

With the Docker Compose stack running:

```bash
python3 -m pytest test_app.py -v
```

The tests go through the gateway on `127.0.0.1:8080`.
