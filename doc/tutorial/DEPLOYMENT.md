# Deployment Guide

Step-by-step procedures for deploying GenueChat across different environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Monitoring Setup](#monitoring-setup)
8. [Production Checklist](#production-checklist)
9. [Rollback Procedure](#rollback-procedure)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Tool             | Minimum Version | Purpose                        |
|------------------|-----------------|--------------------------------|
| Python           | 3.11            | Application runtime            |
| Docker           | 24.0            | Container builds               |
| Docker Compose   | 2.24            | Local multi-service orchestration |
| kubectl          | 1.28            | Kubernetes cluster management  |
| Helm (optional)  | 3.14            | Kubernetes package management  |
| MongoDB          | 7.0             | Application database           |

---

## Environment Configuration

All configuration is driven by environment variables. See `.env.example` for the
complete list.

### Critical Production Variables

```
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-random-value-at-least-32-chars>
GROQ_API_KEY=<your-groq-api-key>
MONGODB_URL=mongodb://<user>:<password>@<host>:27017/<db>?authSource=admin
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=WARNING
```

Generate a strong secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## Local Development

```bash
# 1. Clone and configure
git clone https://github.com/Mutiu123/GenueChat.git
cd GenueChat
cp .env.example .env
# Edit .env with local values

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 4. Start MongoDB
docker compose up -d mongodb

# 5. Run the application
uvicorn app:app --reload --port 8000

# 6. Verify
curl http://localhost:8000/api/v1/health
```

---

## Docker Deployment

### Development (with hot-reload)

```bash
docker compose up --build
```

Services started:
- GenueChat API: http://localhost:8000
- MongoDB: localhost:27017
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

### Production (standalone)

```bash
# Build production image
docker build -t genuechat:1.0.0 .

# Run
docker run -d \
  --name genuechat \
  -p 8000:8000 \
  --env-file .env \
  genuechat:1.0.0
```

The production Dockerfile:
- Uses multi-stage build to minimise image size
- Runs as non-root user `genuechat`
- Includes a HEALTHCHECK directive
- Runs 4 uvicorn workers by default

---

## Kubernetes Deployment

### 1. Create namespace

```bash
kubectl create namespace genuechat
```

### 2. Create secrets

```bash
kubectl create secret generic genuechat-secrets \
  --namespace genuechat \
  --from-literal=SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
  --from-literal=GROQ_API_KEY="your-key" \
  --from-literal=MONGODB_URL="mongodb://mongo:27017/genuechat"
```

### 3. Create config map

```bash
kubectl create configmap genuechat-config \
  --namespace genuechat \
  --from-literal=ENVIRONMENT=production \
  --from-literal=LOG_LEVEL=WARNING \
  --from-literal=CORS_ORIGINS=https://genuechat.example.com
```

### 4. Apply manifests

```bash
kubectl apply -f k8s/deployment.yaml -n genuechat
```

This creates:
- Deployment (2 replicas, autoscaling 2-10)
- ClusterIP Service
- HorizontalPodAutoscaler
- NetworkPolicy
- Ingress

### 5. Verify

```bash
kubectl get pods -n genuechat
kubectl logs -f deployment/genuechat -n genuechat
curl https://genuechat.example.com/api/v1/health
```

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and
pull request to `main`:

1. **Lint** -- Black, Flake8, MyPy, Pylint
2. **Test** -- pytest with coverage against a MongoDB service container
3. **Build** -- Docker image build verification

To enable automatic deployment, extend the workflow with a deploy job that pushes
the image to your container registry and updates the Kubernetes deployment.

---

## Monitoring Setup

### Prometheus

Metrics are exposed at `/metrics` in OpenMetrics format. The Docker Compose stack
includes a pre-configured Prometheus instance scraping the app.

Key metrics:
- `genuechat_http_requests_total` -- request count by method, endpoint, status
- `genuechat_http_request_duration_seconds` -- latency histogram
- `genuechat_chat_predictions_total` -- LLM prediction count
- `genuechat_active_requests` -- in-flight request gauge
- `genuechat_errors_total` -- error count by type

### Grafana

Grafana is available at http://localhost:3000 (admin/admin) with Prometheus
pre-configured as the default datasource.

Create dashboards using the metrics listed above.

---

## Production Checklist

Before going live, verify:

- [ ] ENVIRONMENT=production
- [ ] DEBUG=false
- [ ] SECRET_KEY is a strong, unique random value
- [ ] CORS_ORIGINS restricted to your domain only
- [ ] MONGODB_URL uses authentication
- [ ] TLS termination configured (via Ingress or load balancer)
- [ ] Log level set to WARNING or ERROR
- [ ] Docs endpoints disabled (automatic in production mode)
- [ ] Health checks responding correctly
- [ ] Prometheus scraping metrics
- [ ] Resource limits set in Kubernetes
- [ ] Network policies applied
- [ ] Backup strategy for MongoDB in place

---

## Rollback Procedure

### Docker

```bash
# Stop current container
docker stop genuechat

# Start previous version
docker run -d --name genuechat -p 8000:8000 --env-file .env genuechat:<previous-tag>
```

### Kubernetes

```bash
# View rollout history
kubectl rollout history deployment/genuechat -n genuechat

# Roll back to previous revision
kubectl rollout undo deployment/genuechat -n genuechat

# Roll back to specific revision
kubectl rollout undo deployment/genuechat -n genuechat --to-revision=2
```

---

## Troubleshooting

### Application does not start

1. Check environment variables are set: `env | grep GENUE`
2. Verify MongoDB is reachable: `mongosh <MONGODB_URL> --eval "db.runCommand({ping:1})"`
3. Check logs: `docker logs genuechat` or `kubectl logs deployment/genuechat`

### Health check returns "degraded"

The `/api/v1/health` endpoint reports "degraded" when the database check fails.
Verify MongoDB connectivity and credentials.

### Rate limit errors (429)

The default rate limit is 100 requests per 60 seconds per IP. Adjust
`RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` in your environment.

### JWT token errors (401)

- Ensure the `SECRET_KEY` is consistent across all application instances.
- Check token expiration with `JWT_EXPIRATION_MINUTES`.
- Verify the Authorization header format: `Bearer <token>`.
