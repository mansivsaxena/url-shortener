# UvA - Web Services and Cloud-Based Systems

## Group 9 - Assignment 3 (Containers & Kubernetes)

Two Flask microservices behind an Nginx reverse proxy, backed by PostgreSQL.
Deployable locally via Docker Compose or to a Kubernetes cluster.

- **Auth service** — user registration, login, JWT issuance, token validation.
- **URL shortener service** — per-user URL CRUD with ownership enforcement.
- **Nginx gateway** — single entry point routing `/auth/*` to auth and `/*` to shortener.

The shortener never sees the JWT secret; it validates tokens by calling `GET /users/validate` on the auth service.

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
│   └── nginx-service.yaml
├── nginx/
│   └── nginx.conf
├── extensions.py
├── models.py
├── docker-compose.yml
├── .env
├── auth_service_run.py
├── url_shortener_service_run.py
├── test_app.py
├── test_bonus.py
└── requirements.txt
```

## Running with Docker Compose

Requires Docker and Docker Compose. No local Postgres install needed — the
database runs as a container with a persistent volume.

```bash
docker compose up --build -d
```

This starts four containers: `db` (Postgres), `auth`, `shortener`, and
`gateway` (Nginx). The gateway listens on `http://127.0.0.1:8080`.

To stop:

```bash
docker compose down          # keeps data
docker compose down -v       # also removes the database volume
```

## Kubernetes Deployment

The `k8s/` directory contains all manifests needed to deploy the stack on a
multi-node cluster. See `k8s-deploy-guide.md` for the full walkthrough
(cluster setup, image distribution, manifest apply order).

Key points:
- Shortener runs with **3 replicas** across worker nodes.
- Postgres uses a PersistentVolumeClaim for data persistence.
- The gateway is exposed via **NodePort 30080**.
- Config and credentials are managed through a ConfigMap and Secret.

## API Summary

**Auth** (`/auth/` via gateway):

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/users` | No | Register |
| PUT | `/users` | Yes | Update password |
| POST | `/users/login` | No | Login, returns JWT |
| GET | `/users/validate` | Yes | Validate token |
| POST | `/users/logout` | Yes | Logout |

**Shortener** (`/` via gateway):

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Yes | List user's URLs |
| POST | `/` | Yes | Shorten a URL |
| DELETE | `/` | Yes | Delete all user's URLs |
| GET | `/<id>` | No | Get URL info + analytics |
| PUT | `/<id>` | Yes | Update URL (owner only) |
| DELETE | `/<id>` | Yes | Delete URL (owner only) |
| POST | `/bulk` | Yes | Shorten multiple URLs |

## Testing

With Docker Compose running:

```bash
python -m pytest test_app.py test_bonus.py -v
```

Both test files point at the gateway (`127.0.0.1:8080`).

## Testing

Run this after both services are running on local ports (`127.0.0.1:8001` and `127.0.0.1:8000`):
```bash
python test_app.py
```

Run the bonus tests through Docker + Nginx gateway:
```bash
python test_bonus.py
```
