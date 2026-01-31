# GenueChat -- Workflow Diagrams

Visual reference of every major data flow, process, and lifecycle
within the application.

---

## Page 1: Request Lifecycles

### 1. Chat Request Flow (POST /api/v1/chat/)

```
  Client                    GenueChat API                         Groq Cloud
    |                           |                                     |
    |  POST /api/v1/chat/       |                                     |
    |  Authorization: Bearer <> |                                     |
    |  {"question": "..."}      |                                     |
    |-------------------------->|                                     |
    |                           |                                     |
    |                    +------v------+                               |
    |                    | Middleware   |                               |
    |                    | Stack       |                               |
    |                    |             |                               |
    |                    | 1. Assign   |                               |
    |                    |  X-Request-ID                               |
    |                    |             |                               |
    |                    | 2. Record   |                               |
    |                    |  start time |                               |
    |                    |             |                               |
    |                    | 3. CORS     |                               |
    |                    |  check      |                               |
    |                    +------+------+                               |
    |                           |                                     |
    |                    +------v------+                               |
    |                    | Rate Limiter|                               |
    |                    | (token      |                               |
    |                    |  bucket)    |                               |
    |                    +------+------+                               |
    |                           |                                     |
    |                    +------v------+         (if 429)              |
    |                    | Allowed?    +-------> Rate Limit Error ---->|
    |                    +------+------+         JSON response        |
    |                           | yes                                  |
    |                    +------v------+                               |
    |                    | JWT Verify  |                               |
    |                    | (decode +   |         (if 401)              |
    |                    |  validate)  +-------> Auth Error ---------->|
    |                    +------+------+         JSON response        |
    |                           | valid                                |
    |                    +------v------+                               |
    |                    | Pydantic    |                               |
    |                    | Validation  |         (if 422)              |
    |                    | (ChatRequest+-------> Validation Error ---->|
    |                    |  model)     |         JSON response        |
    |                    +------+------+                               |
    |                           | valid                                |
    |                    +------v------+                               |
    |                    | Sanitize    |                               |
    |                    | Input       |                               |
    |                    | (strip XSS, |                               |
    |                    |  HTML tags) |                               |
    |                    +------+------+                               |
    |                           |                                     |
    |                    +------v------+                               |
    |                    | Conversation|     LLM API Call              |
    |                    | Chain       +----------------------------->|
    |                    | (LangChain) |                              |
    |                    |             |<------- LLM Response --------|
    |                    +------+------+                               |
    |                           |                                     |
    |                    +------v------+                               |
    |                    | Audit Log   |                               |
    |                    | + Prometheus |                               |
    |                    | metrics     |                               |
    |                    +------+------+                               |
    |                           |                                     |
    |  200 OK                   |                                     |
    |  {"answer": "...",        |                                     |
    |   "processing_time_ms":   |                                     |
    |   "model": "llama-3.1.."} |                                     |
    |<--------------------------+                                     |
```

---

### 2. Document Q&A Flow (POST /api/v1/chat/document)

```
  Client                   GenueChat API                    Vector Store
    |                          |                                 |
    |  POST (multipart/form)   |                                 |
    |  file=document.pdf       |                                 |
    |  question="..."          |                                 |
    |------------------------->|                                 |
    |                          |                                 |
    |                   [Auth + Rate Limit + Validate]            |
    |                          |                                 |
    |                   +------v------+                          |
    |                   | Validate    |                          |
    |                   | file is PDF |                          |
    |                   +------+------+                          |
    |                          |                                 |
    |                   +------v------+                          |
    |                   | Save to     |                          |
    |                   | temp file   |                          |
    |                   +------+------+                          |
    |                          |                                 |
    |                   +------v---------+                       |
    |                   | PyPDFLoader    |                       |
    |                   | Extract text   |                       |
    |                   | from all pages |                       |
    |                   +------+---------+                       |
    |                          |                                 |
    |                   +------v---------+                       |
    |                   | Text Splitter  |                       |
    |                   | chunk_size=1000|                       |
    |                   | overlap=200    |                       |
    |                   +------+---------+                       |
    |                          |                                 |
    |                   +------v---------+                       |
    |                   | HuggingFace    |                       |
    |                   | Embeddings     |                       |
    |                   | (encode chunks)|                       |
    |                   +------+---------+                       |
    |                          |                                 |
    |                   +------v---------+  Store vectors        |
    |                   | FAISS.from_    +--------------------->|
    |                   |   documents()  |                      |
    |                   +------+---------+  Retrieve similar    |
    |                          |            chunks for question  |
    |                   +------v---------+<--------------------|
    |                   | Build RAG      |                       |
    |                   | Chain:         |                       |
    |                   |  context +     |                       |
    |                   |  question      |                       |
    |                   |  -> LLM        |                       |
    |                   |  -> parse      |                       |
    |                   +------+---------+                       |
    |                          |                                 |
    |                   [Cleanup temp file]                       |
    |                   [Audit log + metrics]                     |
    |                          |                                 |
    |  200 OK                  |                                 |
    |  {"answer": "...",       |                                 |
    |   "processing_time_ms":} |                                 |
    |<-------------------------+                                 |
```

---

### 3. Authentication Flow

```
  Client                    GenueChat API                    JWT Library
    |                           |                                |
    |  POST /api/v1/auth/token  |                                |
    |  {"username": "x",        |                                |
    |   "password": "y"}        |                                |
    |-------------------------->|                                |
    |                           |                                |
    |                    +------v------+                         |
    |                    | Rate Limit  |                         |
    |                    | Check       |                         |
    |                    +------+------+                         |
    |                           |                                |
    |                    +------v------+                         |
    |                    | Validate    |                         |
    |                    | credentials |                         |
    |                    +------+------+                         |
    |                           |                                |
    |                    +------v------+   Encode                |
    |                    | Create JWT  +------------------------>|
    |                    | Payload:    |   {sub, exp, iat}       |
    |                    |   sub=user  |   Sign with SECRET_KEY  |
    |                    |   exp=now+  |   Algorithm: HS256      |
    |                    |     60min   |<---- token string ------|
    |                    +------+------+                         |
    |                           |                                |
    |                    +------v------+                         |
    |                    | Audit Log:  |                         |
    |                    | token_issued|                         |
    |                    | Prometheus: |                         |
    |                    | auth_events |                         |
    |                    +------+------+                         |
    |                           |                                |
    |  200 OK                   |                                |
    |  {"access_token": "ey..", |                                |
    |   "token_type": "bearer", |                                |
    |   "expires_in": 3600}     |                                |
    |<--------------------------+                                |


  --- Later, using the token: ---

  Client                    GenueChat API
    |                           |
    |  GET /api/v1/auth/me      |
    |  Authorization: Bearer <> |
    |-------------------------->|
    |                           |
    |                    +------v------+
    |                    | Extract     |
    |                    | Bearer token|
    |                    | from header |
    |                    +------+------+
    |                           |
    |                    +------v------+
    |                    | jwt.decode()|
    |                    | Verify sig  |
    |                    | Check exp   |
    |                    +------+------+
    |                           |
    |  200 OK                   |
    |  {"user": "x",           |
    |   "claims": {...}}        |
    |<--------------------------+
```

---

## Page 2: Operational Workflows

### 4. Application Startup / Shutdown Lifecycle

```
  uvicorn starts
       |
       v
  +--------------------+
  | Import app module  |
  | - Load Settings    |
  |   (from .env)      |
  | - Setup logging    |
  |   (JSON formatter) |
  | - Create FastAPI   |
  |   instance         |
  | - Register         |
  |   middleware        |
  | - Register         |
  |   exception        |
  |   handlers         |
  | - Include routers  |
  | - Mount /metrics   |
  +--------+-----------+
           |
           v
  +--------+-----------+
  | Lifespan: STARTUP  |
  |                    |
  | 1. Log "Starting   |
  |    GenueChat v1.0" |
  |                    |
  | 2. Database.       |
  |    connect()       |
  |    - Open Motor    |
  |      client        |
  |    - Ping MongoDB  |
  |    - Log success   |
  |    (or warn if     |
  |     unavailable)   |
  +--------+-----------+
           |
           v
  +--------+-----------+
  | SERVING REQUESTS   |
  | (event loop runs)  |
  +--------+-----------+
           |
    (SIGTERM / SIGINT)
           |
           v
  +--------+-----------+
  | Lifespan: SHUTDOWN |
  |                    |
  | 1. Database.       |
  |    close()         |
  |    - Close Motor   |
  |      client pool   |
  |                    |
  | 2. Log "Shutdown   |
  |    complete"       |
  +--------------------+
```

---

### 5. CI/CD Pipeline Workflow

```
  Developer              GitHub                  CI Runner
     |                     |                        |
     | git push main       |                        |
     | (or open PR)        |                        |
     |------------------->|                        |
     |                     |  Trigger workflow      |
     |                     |---------------------->|
     |                     |                        |
     |                     |              +---------v----------+
     |                     |              | JOB 1: LINT        |
     |                     |              |                    |
     |                     |              | 1. Checkout code   |
     |                     |              | 2. Setup Python    |
     |                     |              |    3.11            |
     |                     |              | 3. Install deps    |
     |                     |              | 4. black --check . |
     |                     |              | 5. flake8 src/     |
     |                     |              |    tests/ app.py   |
     |                     |              | 6. mypy src/       |
     |                     |              | 7. pylint src/     |
     |                     |              |    --fail-under=7  |
     |                     |              +---------+----------+
     |                     |                        |
     |                     |              +---------v----------+
     |                     |              | JOB 2: TEST        |
     |                     |              | (needs: lint)      |
     |                     |              |                    |
     |                     |              | Service: MongoDB 7 |
     |                     |              |                    |
     |                     |              | 1. Checkout code   |
     |                     |              | 2. Setup Python    |
     |                     |              | 3. Install deps    |
     |                     |              | 4. pytest tests/   |
     |                     |              |    --cov=src       |
     |                     |              |    --cov-report=xml|
     |                     |              | 5. Upload coverage |
     |                     |              |    to Codecov      |
     |                     |              +---------+----------+
     |                     |                        |
     |                     |              +---------v----------+
     |                     |              | JOB 3: BUILD       |
     |                     |              | (needs: test)      |
     |                     |              |                    |
     |                     |              | 1. Checkout code   |
     |                     |              | 2. docker build    |
     |                     |              |    -t genuechat:   |
     |                     |              |    <sha>           |
     |                     |              +---------+----------+
     |                     |                        |
     |                     |  Status: pass/fail     |
     |                     |<-----------------------|
     |  PR check result    |                        |
     |<--------------------|                        |
```

---

### 6. Monitoring Data Flow

```
  FastAPI App                Prometheus              Grafana
     |                          |                       |
     | MetricsMiddleware        |                       |
     | records per request:     |                       |
     |  - counter++             |                       |
     |  - histogram.observe()   |                       |
     |  - gauge.inc/dec         |                       |
     |                          |                       |
     | /metrics endpoint        |                       |
     | (OpenMetrics format)     |                       |
     |                          |                       |
     |    Scrape every 15s      |                       |
     |<-------------------------+                       |
     |                          |                       |
     | # genuechat_http_reques..|                       |
     | # genuechat_active_req.. |                       |
     | # genuechat_chat_pred..  |                       |
     |------------------------->|                       |
     |                          |                       |
     |                          |  Store in TSDB        |
     |                          |  (time series DB)     |
     |                          |                       |
     |                          |   PromQL queries      |
     |                          |<----------------------+
     |                          |                       |
     |                          |   Query results       |
     |                          +---------------------->|
     |                          |                       |
     |                          |                +------v------+
     |                          |                | Dashboard   |
     |                          |                | Panels:     |
     |                          |                |  - Request  |
     |                          |                |    rate     |
     |                          |                |  - Latency  |
     |                          |                |    P50/P95  |
     |                          |                |  - Error %  |
     |                          |                |  - Active   |
     |                          |                |    requests |
     |                          |                +-------------+


  FastAPI App                    Structured Logs (stdout)
     |
     | JSONFormatter writes:
     |
     |  {"timestamp": "2024-...",
     |   "level": "INFO",
     |   "logger": "src.routes.chat",
     |   "message": "Chat request processed",
     |   "request_id": "550e8400-...",
     |   "module": "chat",
     |   "function": "chat",
     |   "line": 42}
     |
     |  --> stdout / container logs
     |  --> collected by K8s logging agent
     |  --> forwarded to centralized log aggregator
     |      (ELK, Loki, CloudWatch, etc.)
```

---

### 7. Token-Bucket Rate Limiting Algorithm

```
  Configuration: max_tokens=100, window=60s
  Rate = 100 tokens / 60 seconds = 1.667 tokens/sec

  Time ----->

  Request arrives from IP 10.0.0.1
       |
       v
  +----+----+
  | Bucket  |    tokens=100.0, last_refill=T0
  | for     |
  | 10.0.0.1|
  +---------+
       |
       v
  Calculate refill:
    elapsed = now - last_refill
    new_tokens = min(max_tokens, tokens + elapsed * rate)
       |
       v
  +----+----+
  | tokens  |--- >= 1.0? ---> YES: tokens -= 1, ALLOW request
  | check   |                  NO:  DENY (429 Too Many Requests)
  +---------+

  Example timeline:
  +---------+---------+-----------+--------+----------+
  | Time    | Action  | Tokens    | Refill | Result   |
  |         |         | Before    | Added  |          |
  +---------+---------+-----------+--------+----------+
  | T+0.0s  | Req #1  | 100.0     | 0      | ALLOW    |
  | T+0.0s  | Req #2  | 99.0      | 0      | ALLOW    |
  | ...     | ...     | ...       | ...    | ...      |
  | T+0.0s  | Req#100 | 1.0       | 0      | ALLOW    |
  | T+0.0s  | Req#101 | 0.0       | 0      | DENY 429 |
  | T+0.6s  | Req#102 | 0.0       | +1.0   | ALLOW    |
  | T+1.2s  | Req#103 | 0.0       | +1.0   | ALLOW    |
  +---------+---------+-----------+--------+----------+
```

---

### 8. Exception Handling Flow

```
  Any route handler raises an exception
       |
       v
  +----+------------------+
  | Is it GenueException? |--YES--> Use status_code, message, details
  +----+------------------+         from the exception object
       | NO                              |
       v                                 v
  +----+------------------+    +---------+---------+
  | Is it HTTPException?  |    | Build JSON:       |
  +----+------------------+    | {                 |
       | NO          |YES      |   "error": true,  |
       v             v         |   "status_code":  |
  +----+--------+ Use detail   |     <code>,       |
  | Is it       | + status     |   "message":      |
  | Validation  | code         |     <msg>,        |
  | Error?      |              |   "details":      |
  +----+--------+              |     <details>,    |
       | NO    |YES            |   "request_id":   |
       v       v               |     <id>          |
  +----+----+ Extract          | }                 |
  | Catch-  | validation       +---------+---------+
  | all     | errors                     |
  | 500     | into details               v
  +---------+                    Return JSONResponse
                                 to client
```
