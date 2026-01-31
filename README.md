# GenueChat

Enterprise-grade RAG chatbot API built with FastAPI, LangChain, and Groq.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Getting Started](#getting-started)
7. [Configuration](#configuration)
8. [API Reference](#api-reference)
9. [Authentication](#authentication)
10. [Document Q&A](#document-qa)
11. [Monitoring and Observability](#monitoring-and-observability)
12. [Testing](#testing)
13. [Docker Deployment](#docker-deployment)
14. [Kubernetes Deployment](#kubernetes-deployment)
15. [CI/CD Pipeline](#cicd-pipeline)
16. [Security](#security)
17. [Contributing](#contributing)
18. [License](#license)

---

## Overview

GenueChat is an AI-powered chatbot application that implements Retrieval-Augmented
Generation (RAG). It allows users to:

- Ask general questions and receive context-aware responses from an LLM
- Upload PDF documents and ask questions grounded in the document content
- Interact through a secure, authenticated REST API

The application is built for production use with JWT authentication, rate limiting,
Prometheus metrics, structured logging, MongoDB persistence, and container-ready
deployment configurations for Docker and Kubernetes.

---

## Architecture

```
                        +-------------------+
                        |   Load Balancer   |
                        |  (Ingress / ALB)  |
                        +---------+---------+
                                  |
                        +---------v---------+
                        |    FastAPI App     |
                        |  (uvicorn workers) |
                        +---------+---------+
                                  |
              +-------------------+-------------------+
              |                   |                   |
    +---------v------+  +---------v------+  +---------v------+
    |  Auth Module   |  |  Chat Routes   |  | Health Routes  |
    | (JWT tokens)   |  | (LLM + RAG)   |  | (probes)       |
    +----------------+  +-------+--------+  +----------------+
                                |
                    +-----------+-----------+
                    |                       |
          +---------v------+     +---------v------+
          | Conversation   |     | RAG Pipeline   |
          | Chain (Groq)   |     | (PDF + FAISS)  |
          +----------------+     +----------------+
                    |
          +---------v------+
          |    MongoDB     |
          | (audit logs)   |
          +----------------+
```

### Request Flow

1. Client sends request with JWT Bearer token
2. Middleware assigns a unique X-Request-ID
3. Rate limiter checks per-IP token bucket
4. Input validation via Pydantic models
5. Input sanitization strips dangerous content
6. Route handler processes the request
7. Response returned with structured JSON format
8. Prometheus metrics and audit logs recorded

---

## System Demo

![The System Demo1](https://github.com/Mutiu123/GenueChat/blob/main/demo/Screenshot%202024-08-22%20at%2021.20.37.png)

![The System Demo2](https://github.com/Mutiu123/GenueChat/blob/main/demo/Screenshot%202024-08-22%20at%2021.22.44.png)

![The System Demo3](https://github.com/Mutiu123/GenueChat/blob/main/demo/Screenshot%202024-08-22%20at%2021.35.33.png)

---

## Features

### Security
- JWT token-based authentication with configurable expiration
- Token-bucket rate limiting per client IP
- Pydantic v2 input validation on all endpoints
- CORS with configurable origin allowlist
- Environment-based secret management
- HTML and NoSQL injection sanitization
- Global exception handling with proper HTTP status codes
- Non-root Docker container execution

### Monitoring
- Prometheus metrics (11 metric types: counters, histograms, gauges, info)
- Structured JSON logging with custom formatter
- Unique request ID tracking (X-Request-ID header)
- Latency histograms for HTTP requests and LLM predictions
- Health check endpoints (full, liveness, readiness)
- Audit logging for predictions and auth events
- Grafana integration with provisioned datasources

### API
- FastAPI with async/await support
- OpenAPI/Swagger documentation (auto-disabled in production)
- Pydantic v2 models for all request/response schemas
- Structured error responses with request IDs
- Versioned API routes (/api/v1/...)

### Database
- MongoDB async client via Motor
- Connection pooling (configurable min 10, max 50)
- Singleton pattern for connection sharing
- Health checks with configurable timeouts
- Graceful connection closure on shutdown

### Deployment
- Multi-stage production Dockerfile
- Development Dockerfile with hot-reload
- Docker Compose (app, MongoDB, Prometheus, Grafana)
- Kubernetes manifests (Deployment, Service, HPA, NetworkPolicy, Ingress)
- GitHub Actions CI/CD pipeline

---

## Tech Stack

| Category       | Technology                                      |
|----------------|-------------------------------------------------|
| Framework      | FastAPI, Uvicorn                                |
| LLM            | Groq (Llama 3.1 8B), LangChain                 |
| Embeddings     | HuggingFace Sentence Transformers               |
| Vector Store   | FAISS                                           |
| Database       | MongoDB (Motor async driver)                    |
| Authentication | PyJWT                                           |
| Validation     | Pydantic v2                                     |
| Monitoring     | Prometheus, Grafana                             |
| Containerization| Docker, Docker Compose                         |
| Orchestration  | Kubernetes                                      |
| CI/CD          | GitHub Actions                                  |
| Testing        | Pytest                                          |
| Linting        | Black, Flake8, MyPy, Pylint                    |

---

## Project Structure

```
GenueChat/
|-- app.py                          # FastAPI application entry point
|-- setup.py                        # Package configuration
|-- requirements.txt                # Production dependencies
|-- requirements-dev.txt            # Development/test dependencies
|-- pyproject.toml                  # Tool configuration (black, pytest, mypy)
|-- .env.example                    # Environment variable template
|-- .pre-commit-config.yaml         # Pre-commit hook definitions
|-- Dockerfile                      # Production multi-stage build
|-- Dockerfile.dev                  # Development with hot-reload
|-- docker-compose.yml              # Full-stack local development
|-- Procfile                        # Heroku/PaaS deployment
|-- src/
|   |-- __init__.py
|   |-- config.py                   # Centralized settings with lru_cache
|   |-- database.py                 # MongoDB singleton connection manager
|   |-- exceptions.py               # Custom exceptions and global handlers
|   |-- llm.py                      # LLM conversation chain and RAG pipeline
|   |-- middleware.py                # Request ID, metrics, CORS middleware
|   |-- monitoring.py               # Prometheus metrics and structured logging
|   |-- prompts.py                  # Prompt templates
|   |-- schemas.py                  # Pydantic v2 request/response models
|   |-- security.py                 # JWT, rate limiter, sanitization
|   |-- routes/
|       |-- __init__.py
|       |-- auth.py                 # Token generation and user info
|       |-- chat.py                 # Chat and document Q&A endpoints
|       |-- health.py               # Health, liveness, readiness, status
|-- tests/
|   |-- __init__.py
|   |-- conftest.py                 # Shared fixtures
|   |-- test_api.py                 # Integration tests
|   |-- test_config.py              # Configuration tests
|   |-- test_exceptions.py          # Exception tests
|   |-- test_monitoring.py          # Logging/metrics tests
|   |-- test_schemas.py             # Pydantic model tests
|   |-- test_security.py            # JWT/rate limiter/sanitization tests
|-- k8s/
|   |-- deployment.yaml             # K8s Deployment, Service, HPA, NetworkPolicy, Ingress
|-- monitoring/
|   |-- prometheus.yml              # Prometheus scrape config
|   |-- grafana/
|       |-- provisioning/
|           |-- datasources/
|           |   |-- prometheus.yml  # Grafana datasource provisioning
|           |-- dashboards/
|               |-- dashboards.yml  # Grafana dashboard provisioning
|-- .github/
|   |-- workflows/
|       |-- ci.yml                  # Lint, test, build pipeline
|-- doc/
|   |-- PROJECT_ARCHITECTURE.md     # Visual architecture diagrams
|   |-- WORKFLOW_DIAGRAMS.md        # Request flows and lifecycle diagrams
|   |-- ARCHITECTURE_EXPLAINED.md   # Design decisions explained
|   |-- tutorial/
|       |-- CONTRIBUTING.md         # Development workflow guide
|       |-- DEPLOYMENT.md           # Deployment step-by-step
|       |-- PRODUCTION_READY.md     # Production readiness checklist
|-- demo/                           # Screenshot assets
|-- research/                       # Jupyter experiment notebooks
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (recommended)
- A Groq API key (get one at https://console.groq.com)

### Quick Start with Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/Mutiu123/GenueChat.git
cd GenueChat

# 2. Configure environment
cp .env.example .env
# Edit .env -- set at least GROQ_API_KEY and SECRET_KEY

# 3. Start all services
docker compose up --build

# 4. Verify
curl http://localhost:8000/api/v1/health
```

### Quick Start without Docker

```bash
# 1. Clone and configure
git clone https://github.com/Mutiu123/GenueChat.git
cd GenueChat
cp .env.example .env

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start MongoDB (required)
# Ensure MongoDB is running on localhost:27017

# 5. Run the application
python app.py

# 6. Open API docs
# Navigate to http://localhost:8000/docs
```

---

## Configuration

All settings are managed through environment variables. The application uses a
type-safe `Settings` class with `lru_cache` for performance.

### Environment Variables

| Variable                   | Default                | Description                            |
|----------------------------|------------------------|----------------------------------------|
| APP_NAME                   | GenueChat              | Application name                       |
| APP_VERSION                | 1.0.0                  | Application version                    |
| ENVIRONMENT                | development            | development, staging, or production    |
| DEBUG                      | false                  | Enable debug mode                      |
| HOST                       | 0.0.0.0                | Bind address                           |
| PORT                       | 8000                   | Bind port                              |
| LOG_LEVEL                  | INFO                   | Logging level                          |
| SECRET_KEY                 | (change in production) | JWT signing key                        |
| JWT_ALGORITHM              | HS256                  | JWT algorithm                          |
| JWT_EXPIRATION_MINUTES     | 60                     | Token lifetime                         |
| CORS_ORIGINS               | http://localhost:3000   | Comma-separated allowed origins        |
| RATE_LIMIT_REQUESTS        | 100                    | Max requests per window                |
| RATE_LIMIT_WINDOW_SECONDS  | 60                     | Rate limit window                      |
| MONGODB_URL                | mongodb://localhost:27017 | MongoDB connection string           |
| MONGODB_DATABASE           | genuechat              | Database name                          |
| MONGODB_MIN_POOL_SIZE      | 10                     | Minimum connection pool size           |
| MONGODB_MAX_POOL_SIZE      | 50                     | Maximum connection pool size           |
| MONGODB_TIMEOUT_MS         | 5000                   | Connection timeout                     |
| GROQ_API_KEY               |                        | Groq API key for LLM access            |
| LLM_MODEL_NAME             | llama-3.1-8b-instant   | LLM model identifier                  |
| LLM_TEMPERATURE            | 0.0                    | LLM temperature                        |
| PROMETHEUS_ENABLED         | true                   | Enable Prometheus metrics              |
| METRICS_PREFIX             | genuechat              | Metrics name prefix                    |

### Environment-Specific Behaviour

| Behaviour                | Development | Staging | Production |
|--------------------------|-------------|---------|------------|
| Swagger UI (/docs)       | Enabled     | Enabled | Disabled   |
| ReDoc (/redoc)           | Enabled     | Enabled | Disabled   |
| Hot-reload               | Enabled     | Off     | Off        |
| Access logs              | Enabled     | Enabled | Disabled   |
| Debug mode               | Available   | Off     | Off        |

---

## API Reference

### Root

| Method | Path | Description         |
|--------|------|---------------------|
| GET    | /    | Application info    |

### Health (prefix: /api/v1)

| Method | Path            | Description                  |
|--------|-----------------|------------------------------|
| GET    | /health         | Full health check            |
| GET    | /health/live    | Liveness probe               |
| GET    | /health/ready   | Readiness probe              |
| GET    | /status         | Application status metadata  |

### Authentication (prefix: /api/v1/auth)

| Method | Path   | Description         | Auth Required |
|--------|--------|---------------------|---------------|
| POST   | /token | Generate JWT token  | No            |
| GET    | /me    | Current user info   | Yes           |

### Chat (prefix: /api/v1/chat)

| Method | Path      | Description              | Auth Required |
|--------|-----------|--------------------------|---------------|
| POST   | /         | Send a chat message      | Yes           |
| POST   | /document | Document Q&A with upload | Yes           |

### Metrics

| Method | Path     | Description              |
|--------|----------|--------------------------|
| GET    | /metrics | Prometheus metrics       |

### Interactive Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Authentication

GenueChat uses JWT Bearer token authentication.

### 1. Obtain a token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2. Use the token

```bash
curl http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{"question": "What is retrieval-augmented generation?"}'
```

---

## Document Q&A

Upload a PDF and ask questions about its contents:

```bash
curl -X POST http://localhost:8000/api/v1/chat/document \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/document.pdf" \
  -F "question=What are the key findings?"
```

Response:
```json
{
  "answer": "The key findings are...",
  "source_chunks": 0,
  "session_id": null,
  "processing_time_ms": 2340.12,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

The RAG pipeline:
1. Extracts text from the PDF using PyPDFLoader
2. Splits into 1000-character chunks with 200-character overlap
3. Generates embeddings via HuggingFace Sentence Transformers
4. Stores in a FAISS vector index
5. Retrieves relevant chunks for the question
6. Sends context and question to the LLM for answer generation

---

## Monitoring and Observability

### Structured Logging

All logs are emitted as JSON with the following fields:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "src.routes.chat",
  "message": "Chat request processed",
  "module": "chat",
  "function": "chat",
  "line": 42,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Prometheus Metrics

Available at `/metrics`. Key metrics:

| Metric                                        | Type      | Description                     |
|-----------------------------------------------|-----------|---------------------------------|
| genuechat_http_requests_total                  | Counter   | Total HTTP requests             |
| genuechat_http_request_duration_seconds        | Histogram | Request latency                 |
| genuechat_active_requests                      | Gauge     | In-flight requests              |
| genuechat_chat_predictions_total               | Counter   | LLM predictions made            |
| genuechat_chat_prediction_duration_seconds     | Histogram | LLM prediction latency          |
| genuechat_document_uploads_total               | Counter   | Document uploads                |
| genuechat_document_processing_seconds          | Histogram | Document processing time        |
| genuechat_db_operations_total                  | Counter   | Database operations             |
| genuechat_auth_events_total                    | Counter   | Authentication events           |
| genuechat_errors_total                         | Counter   | Errors by type                  |
| genuechat_app_info                             | Info      | Application version/environment |

### Grafana

The Docker Compose stack includes Grafana pre-configured with Prometheus as the
default datasource. Access at http://localhost:3000 (admin/admin).

### Request Tracing

Every request receives a unique `X-Request-ID` header. Pass your own via the
request header or let the system generate one. This ID appears in:
- Response headers
- Structured log entries
- Error responses
- Audit log records

---

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test module
pytest tests/test_security.py -v

# Run specific test class
pytest tests/test_schemas.py::TestChatRequest -v
```

### Test Modules

| Module               | Tests | Scope                                    |
|----------------------|-------|------------------------------------------|
| test_config.py       | 7     | Settings, environment, caching           |
| test_exceptions.py   | 8     | All custom exception classes             |
| test_schemas.py      | 10    | Pydantic models validation               |
| test_security.py     | 9     | JWT, rate limiting, input sanitization   |
| test_monitoring.py   | 3     | JSON formatter, audit logging            |
| test_api.py          | 9     | Integration tests for all API endpoints  |
| **Total**            | **46**|                                          |

Coverage target: 80%+

---

## Docker Deployment

### Development

```bash
docker compose up --build
```

Starts: app (hot-reload), MongoDB, Prometheus, Grafana

### Production

```bash
docker build -t genuechat:1.0.0 .
docker run -d -p 8000:8000 --env-file .env genuechat:1.0.0
```

Production image features:
- Multi-stage build for minimal image size
- Non-root user execution
- Built-in health check
- 4 uvicorn workers

---

## Kubernetes Deployment

```bash
# Create namespace and secrets
kubectl create namespace genuechat
kubectl create secret generic genuechat-secrets -n genuechat \
  --from-literal=SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
  --from-literal=GROQ_API_KEY="your-key" \
  --from-literal=MONGODB_URL="mongodb://mongo:27017/genuechat"

# Apply manifests
kubectl apply -f k8s/deployment.yaml -n genuechat
```

Resources created:
- **Deployment** -- 2 replicas with resource limits and health probes
- **Service** -- ClusterIP on port 80 forwarding to 8000
- **HPA** -- Auto-scales 2 to 10 pods based on CPU/memory
- **NetworkPolicy** -- Restricts ingress/egress traffic
- **Ingress** -- TLS-terminated external access

See [DEPLOYMENT.md](DEPLOYMENT.md) for the complete step-by-step guide.

---

## CI/CD Pipeline

GitHub Actions workflow runs on every push and PR to `main`:

1. **Lint** -- Black, Flake8, MyPy, Pylint
2. **Test** -- pytest with MongoDB service container and coverage upload
3. **Build** -- Docker image build verification

See [.github/workflows/ci.yml](.github/workflows/ci.yml).

---

## Security

### Implemented Controls

| Control                    | Implementation                              |
|----------------------------|---------------------------------------------|
| Authentication             | JWT Bearer tokens via PyJWT                 |
| Rate Limiting              | Token-bucket algorithm, per-IP              |
| Input Validation           | Pydantic v2 models with field constraints   |
| CORS                       | Configurable origin allowlist               |
| Secret Management          | Environment variables, no hardcoded secrets |
| Injection Prevention       | HTML sanitization, NoSQL character stripping|
| Error Handling             | Global handlers, no stack traces in responses|
| Container Security         | Non-root user, minimal base image           |

### Security Headers

The API returns:
- `X-Request-ID` for tracing
- CORS headers per configuration
- No server version disclosure

---

## Business Impact

GenueChat provides value through:

- **Customer Service Automation** -- Handles complex queries with document-grounded
  responses, reducing support ticket volume
- **Knowledge Management** -- Enables teams to query PDF documents using natural
  language, making institutional knowledge accessible
- **Operational Efficiency** -- API-first design integrates with existing systems
  and workflows
- **Scalability** -- Kubernetes-native deployment scales from single-instance to
  enterprise-grade clusters
- **Compliance Readiness** -- Audit logging, structured monitoring, and security
  controls support regulatory requirements

---


## Documentation

All documentation lives in the `doc/` directory.

### Architecture and Design

- [PROJECT_ARCHITECTURE.md](doc/PROJECT_ARCHITECTURE.md) -- Visual system architecture diagrams, component maps, infrastructure topology
- [WORKFLOW_DIAGRAMS.md](doc/WORKFLOW_DIAGRAMS.md) -- Request flows, lifecycle diagrams, CI/CD pipeline, algorithm walkthroughs
- [ARCHITECTURE_EXPLAINED.md](doc/ARCHITECTURE_EXPLAINED.md) -- Detailed explanation of every design decision with justifications
- [PROJECT_STAR.md](doc/PROJECT_STAR.md) -- STAR method project description (Situation, Task, Action, Result)

### Tutorials and Guides

- [CONTRIBUTING.md](doc/tutorial/CONTRIBUTING.md) -- Development workflow and coding standards
- [DEPLOYMENT.md](doc/tutorial/DEPLOYMENT.md) -- Step-by-step deployment procedures
- [PRODUCTION_READY.md](doc/tutorial/PRODUCTION_READY.md) -- Production readiness checklist

---

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

---

## Author

**Mutiu Adegboye** -- adegboyemutiu@gmail.com
