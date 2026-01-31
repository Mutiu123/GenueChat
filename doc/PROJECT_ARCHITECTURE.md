# GenueChat -- Project Architecture

A visual reference of the entire system design, component relationships,
and infrastructure layout.

---

## Page 1: System Architecture Overview

```
+=====================================================================+
|                     GENUECHAT SYSTEM ARCHITECTURE                    |
+=====================================================================+

  CLIENT LAYER                        EXTERNAL SERVICES
  ============                        =================
  +------------------+                +-----------------+
  | Web Browser      |                | Groq Cloud API  |
  | (Swagger UI /    |                | (Llama 3.1 8B)  |
  | Frontend App)    |                +--------+--------+
  +--------+---------+                         |
           |                                   |
           | HTTPS + JWT Bearer                | gRPC / HTTPS
           |                                   |
  =========|===================================|==================
  |        v          INFRASTRUCTURE           |                 |
  |  +------------+                            |                 |
  |  | Nginx /    |    TLS Termination         |                 |
  |  | Ingress    +--- Rate Limiting (L7)      |                 |
  |  | Controller |    Load Balancing           |                 |
  |  +-----+------+                            |                 |
  |        |                                   |                 |
  |  ======|===================================|===========      |
  |  |     v     KUBERNETES CLUSTER            |          |      |
  |  |  +------------------------------------------+     |      |
  |  |  |         GENUECHAT POD (x2-10)        |   |     |      |
  |  |  |  +------------------------------------+  |     |      |
  |  |  |  |        FASTAPI APPLICATION         |  |     |      |
  |  |  |  |                                    |  |     |      |
  |  |  |  |  +----------+  +-----------+       |  |     |      |
  |  |  |  |  |MIDDLEWARE|  | EXCEPTION |       |  |     |      |
  |  |  |  |  |  STACK   |  | HANDLERS  |       |  |     |      |
  |  |  |  |  +----+-----+  +-----+-----+      |  |     |      |
  |  |  |  |       |              |             |  |     |      |
  |  |  |  |  +----v--------------v------+      |  |     |      |
  |  |  |  |  |       API ROUTES         |      |  |     |      |
  |  |  |  |  |                          |      |  |     |      |
  |  |  |  |  | /auth  /chat  /health    |      |  |     |      |
  |  |  |  |  +----+------+-------+------+      |  |     |      |
  |  |  |  |       |      |       |             |  |     |      |
  |  |  |  |       v      v       v             |  |     |      |
  |  |  |  |  +--------+ +----+ +-------+       |  |     |      |
  |  |  |  |  |Security| |LLM | |Health |       |  |     |      |
  |  |  |  |  | Module | |Core| |Checks |       |  |     |      |
  |  |  |  |  +---+----+ +-+--+ +---+---+       |  |     |      |
  |  |  |  |      |        |        |            |  |     |      |
  |  |  |  +------------------------------------+  |     |      |
  |  |  |         |        |        |              |     |      |
  |  |  +------------------------------------------+     |      |
  |  |            |        |        |                     |      |
  |  |  +---------v--+ +---v----+  +v-----------+        |      |
  |  |  |  MongoDB   | |  Groq  |  | Prometheus |        |      |
  |  |  | (Audit +   | |  API --+--+ (Metrics)  |        |      |
  |  |  |  Sessions) | | (LLM)  |  +-----+------+        |      |
  |  |  +------------+ +--------+        |               |      |
  |  |                                   |               |      |
  |  |                           +-------v-------+       |      |
  |  |                           |   Grafana     |       |      |
  |  |                           | (Dashboards)  |       |      |
  |  |                           +---------------+       |      |
  |  |                                                   |      |
  |  ====================================================      |
  |                                                             |
  ===============================================================
```

---

## Page 2: Internal Application Component Map

```
+=====================================================================+
|               FASTAPI APPLICATION -- COMPONENT MAP                   |
+=====================================================================+

  app.py (Entry Point)
    |
    |-- Lifespan Manager ---------> Database.connect() / .close()
    |
    |-- setup_middleware(app) ----+
    |                            |
    |   +------------------------v-----------------------------------+
    |   |                   MIDDLEWARE STACK                          |
    |   |  (Executed top-to-bottom on request, bottom-to-top reply)  |
    |   |                                                            |
    |   |  1. CORSMiddleware                                         |
    |   |     - Validates Origin header against allowlist             |
    |   |     - Handles preflight OPTIONS requests                   |
    |   |                                                            |
    |   |  2. MetricsMiddleware                                      |
    |   |     - Increments genuechat_http_requests_total              |
    |   |     - Observes genuechat_http_request_duration_seconds      |
    |   |     - Tracks genuechat_active_requests gauge                |
    |   |                                                            |
    |   |  3. RequestIDMiddleware                                     |
    |   |     - Generates UUID4 or reads X-Request-ID header         |
    |   |     - Attaches to request.state.request_id                 |
    |   |     - Returns X-Request-ID in response header              |
    |   +------------------------------------------------------------+
    |
    |-- register_exception_handlers(app) --+
    |                                      |
    |   +----------------------------------v-------------------------+
    |   |                EXCEPTION HANDLERS                          |
    |   |                                                            |
    |   |  GenueException ---------> Structured JSON (custom code)   |
    |   |  HTTPException ----------> Structured JSON (HTTP code)     |
    |   |  RequestValidationError -> Structured JSON (422)           |
    |   |  Exception (catch-all) --> Structured JSON (500)           |
    |   +------------------------------------------------------------+
    |
    |-- Route Registration
    |
    +-- /api/v1/health/* ---------> health.py
    |     |-- GET /health            Full check (API + DB)
    |     |-- GET /health/live       Liveness probe (K8s)
    |     |-- GET /health/ready      Readiness probe (K8s)
    |     |-- GET /status            App metadata
    |
    +-- /api/v1/auth/* -----------> auth.py
    |     |-- POST /token            [rate-limited] Generate JWT
    |     |-- GET  /me               [JWT required] User claims
    |
    +-- /api/v1/chat/* -----------> chat.py
    |     |-- POST /                 [JWT + rate-limited] Chat
    |     |-- POST /document         [JWT + rate-limited] Doc Q&A
    |
    +-- /metrics -----------------> prometheus_client ASGI app
    |
    +-- GET / --------------------> Root info endpoint


  +-------------------------------------------------------------------+
  |                SECURITY MODULE (security.py)                       |
  |                                                                    |
  |  +------------------+  +---------------------+  +---------------+  |
  |  | JWT Auth         |  | Token-Bucket Rate   |  | Sanitization  |  |
  |  |                  |  | Limiter             |  |               |  |
  |  | create_access_   |  |                     |  | sanitize_     |  |
  |  |   token()        |  | Per-IP buckets      |  |   input()     |  |
  |  | verify_token()   |  | Configurable:       |  |   - Strip     |  |
  |  | get_current_     |  |   max_tokens=100    |  |     <script>  |  |
  |  |   user()         |  |   window=60s        |  |   - Strip     |  |
  |  |                  |  |                     |  |     HTML tags  |  |
  |  | Algorithm: HS256 |  | allow(ip) -> bool   |  |   - Escape    |  |
  |  | Signing: SECRET_ |  |                     |  |     entities  |  |
  |  |   KEY env var    |  |                     |  |               |  |
  |  +------------------+  +---------------------+  | sanitize_     |  |
  |                                                  |   for_db()    |  |
  |                                                  |   - Strip $   |  |
  |                                                  |   - Strip {}  |  |
  |                                                  +---------------+  |
  +-------------------------------------------------------------------+


  +-------------------------------------------------------------------+
  |                 LLM CORE (llm.py)                                  |
  |                                                                    |
  |                    handle_chat_async(question)                      |
  |                           |                                        |
  |              +------------+-------------+                          |
  |              |                          |                          |
  |        (no file)                  (file uploaded)                   |
  |              |                          |                          |
  |              v                          v                          |
  |    ConversationChain           rag_chain_async(file, q)            |
  |    +------------------+        +----------------------------+      |
  |    | LLM: ChatGroq    |        | 1. PyPDFLoader(file)       |      |
  |    | Memory: Buffer   |        | 2. RecursiveCharText       |      |
  |    | Prompt: template |        |    Splitter(1000/200)      |      |
  |    +------------------+        | 3. HuggingFace Embeddings  |      |
  |                                | 4. FAISS Vector Store      |      |
  |                                | 5. Retriever -> Context    |      |
  |                                | 6. ChatGroq -> Answer      |      |
  |                                +----------------------------+      |
  +-------------------------------------------------------------------+


  +-------------------------------------------------------------------+
  |              MONITORING & OBSERVABILITY (monitoring.py)             |
  |                                                                    |
  |  Structured JSON Logging          Prometheus Metrics (11 types)    |
  |  +----------------------+         +----------------------------+   |
  |  | JSONFormatter        |         | COUNTERS:                  |   |
  |  |  - timestamp (UTC)   |         |   http_requests_total      |   |
  |  |  - level             |         |   chat_predictions_total   |   |
  |  |  - logger name       |         |   document_uploads_total   |   |
  |  |  - message           |         |   db_operations_total      |   |
  |  |  - module/function   |         |   auth_events_total        |   |
  |  |  - line number       |         |   errors_total             |   |
  |  |  - request_id        |         |                            |   |
  |  |  - exception (if any)|         | HISTOGRAMS:                |   |
  |  +----------------------+         |   request_duration_seconds  |   |
  |                                   |   prediction_duration_secs  |   |
  |  Audit Logger                     |   document_processing_secs  |   |
  |  +----------------------+         |                            |   |
  |  | log_audit_event()    |         | GAUGE:                     |   |
  |  | log_prediction_      |         |   active_requests          |   |
  |  |   audit()            |         |                            |   |
  |  +----------------------+         | INFO:                      |   |
  |                                   |   app_info (version, env)  |   |
  |                                   +----------------------------+   |
  +-------------------------------------------------------------------+


  +-------------------------------------------------------------------+
  |                 DATABASE (database.py)                              |
  |                                                                    |
  |  Singleton Pattern           Motor (Async MongoDB Driver)          |
  |  +--------------------+      +-------------------------------+     |
  |  | Database.__new__() |----->| AsyncIOMotorClient            |     |
  |  | One instance only  |      |   minPoolSize: 10             |     |
  |  +--------------------+      |   maxPoolSize: 50             |     |
  |                              |   serverSelectionTimeout: 5s  |     |
  |  Methods:                    |   connectTimeout: 5s          |     |
  |    connect()                 +-------------------------------+     |
  |    close()                                                         |
  |    health_check() -> bool                                          |
  |    .db -> AsyncIOMotorDatabase                                     |
  |    .client -> AsyncIOMotorClient                                   |
  +-------------------------------------------------------------------+


  +-------------------------------------------------------------------+
  |                 CONFIGURATION (config.py)                           |
  |                                                                    |
  |  +-------------------+     +----------------------------------+    |
  |  | Environment Enum  |     | Settings (BaseSettings)          |    |
  |  |   DEVELOPMENT     |     |   Loaded from .env file          |    |
  |  |   STAGING         |     |   Cached via @lru_cache          |    |
  |  |   PRODUCTION      |     |   26 typed config variables      |    |
  |  +-------------------+     |                                  |    |
  |                            |   Properties:                    |    |
  |                            |     .cors_origins_list -> List   |    |
  |                            |     .is_production -> bool       |    |
  |                            |     .is_development -> bool      |    |
  |                            +----------------------------------+    |
  +-------------------------------------------------------------------+
```

---

## Infrastructure Topology (Docker Compose)

```
  docker-compose.yml
  ==================

  +---------------------------------------------------------------+
  |                    Docker Network (bridge)                     |
  |                                                                |
  |  +-----------+    +-----------+    +--------+    +---------+   |
  |  |   app     |    |  mongodb  |    | prome- |    | grafana |   |
  |  | (FastAPI) |    | (Mongo 7) |    | theus  |    |         |   |
  |  |           |    |           |    |        |    |         |   |
  |  | Port 8000 |--->| Port 27017|    |Port 9090    |Port 3000|   |
  |  |           |    |           |    |   |    |    |    |    |   |
  |  | /metrics -+----|-----------|----+-> |    |    |    |    |   |
  |  +-----------+    +-----------+    +---+----+    +----+----+   |
  |       |                                |              |        |
  +-------|-----------Volumes--------------|--------------|--------+
          |                                |              |
     .:/app (dev)                  prometheus.yml     grafana_data
                                                    provisioning/
```

---

## Kubernetes Resource Layout

```
  Namespace: genuechat
  =====================

  +-- Ingress (genuechat-ingress)
  |     TLS: genuechat.example.com
  |     Rate limit: 100 req/s
  |     |
  |     v
  +-- Service (genuechat) -- ClusterIP :80 -> :8000
  |     |
  |     v
  +-- Deployment (genuechat)
  |     Replicas: 2 (managed by HPA)
  |     Container: genuechat:latest
  |     Resources: 250m-1 CPU, 256-512Mi RAM
  |     Probes:
  |       liveness:  GET /api/v1/health/live  (every 15s)
  |       readiness: GET /api/v1/health/ready (every 10s)
  |     Security: runAsNonRoot, runAsUser 1000
  |
  +-- HPA (genuechat-hpa)
  |     Min: 2, Max: 10
  |     Scale on: CPU > 70%, Memory > 80%
  |
  +-- NetworkPolicy (genuechat-netpol)
        Ingress: only from ingress pods on port 8000
        Egress:  MongoDB (27017), HTTPS (443)
```
