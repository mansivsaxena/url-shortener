# UvA - Web Services and Cloud-Based Systems

## Group 9 - Assignment 3 (Containers & Kubernetes)

This repository contains:
- `auth_service` for user management, login, JWT issuance, and JWT validation.
- `url_shortener_service` for per-user URL ownership and URL CRUD.
- `nginx` as a single gateway in front of both services.
- `postgres` as the shared persistent database.

The bonus features in this iteration include Nginx rate limiting on the Docker Compose gateway, a Horizontal Pod Autoscaler for the Kubernetes shortener deployment, and request tracing with X-Request-ID and X-Served-By response headers.

## Project Structure

```text
url-shortener/
├── auth_service/
│   ├── Dockerfile
│   ├── __init__.py
│   ├── config.py
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
├── extensions.py
├── models.py
├── read_from.csv
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

Both parts use the shared application code in `auth_service/`, `url_shortener_service/`, `models.py`, `extensions.py`, `auth_service_run.py`, `url_shortener_service_run.py`, and `requirements.txt`.

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

Gateway is exposed on port `8080` (for example `http://127.0.0.1:8080` locally):
- Auth service via `/auth/*`
- URL shortener via `/*`

Persistence is handled through the `pgdata` Docker volume in `docker-compose.yml`, so data survives normal restarts and `docker compose down` unless the volume is removed.

The Docker Compose gateway also applies nginx rate limiting (`5r/s`, burst `10`) and returns `429` when the limit is exceeded.

## Kubernetes Deployment

All Kubernetes manifests are in `k8s/`. The setup deploys `postgres` (with `k8s/postgres-pvc.yaml` for persistence), `auth`, `shortener`, and an nginx `gateway` exposed through NodePort `30080`. The shortener runs with 3 replicas; the bonus HPA is defined in `k8s/shortener-hpa.yaml`.

Build the service images used by the Kubernetes Deployments:

```bash
docker build -t auth:latest -f auth_service/Dockerfile .
docker build -t shortener:latest -f url_shortener_service/Dockerfile .
```

The manifests use `imagePullPolicy: Never`, so these images must be available on the Kubernetes worker nodes before deployment.

Deploy or remove everything:

```bash
kubectl apply -f k8s/
kubectl delete -f k8s/
```

After deployment, the gateway is reachable at `http://<node-ip>:30080`.

Notes:
- The Kubernetes gateway does not include the Compose nginx rate-limiting rules.
- The HPA assumes a metrics API such as `metrics-server` is available.

## API Summary

Auth service endpoints:
- `POST /auth/users`
- `PUT /auth/users`
- `POST /auth/users/login`
- `GET /auth/users/validate` (internal validation endpoint used by the shortener)
- `POST /auth/users/logout` (extra endpoint)
- `GET /auth/healthz`
- `GET /auth/readyz`

URL shortener endpoints:
- `GET /` (auth required)
- `POST /` (auth required; accepts optional `custom_id` and `expires_at`)
- `DELETE /` (auth required)
- `GET /<id>` (public; returns the stored long URL and analytics with status `301`)
- `PUT /<id>` (auth required, owner-only)
- `DELETE /<id>` (auth required, owner-only)
- `POST /bulk` (auth required, extra endpoint)
- `GET /healthz`
- `GET /readyz`

Additional URL shortener features:
- `POST /` accepts optional `custom_id` and `expires_at`
- `GET /<id>` returns click analytics
- responses from the shortener include `X-Request-ID` and `X-Served-By` headers for request tracing

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
