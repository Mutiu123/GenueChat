# Architecture and Workflow Decisions Explained

This document walks through what I included in the PROJECT_ARCHITECTURE.md and
WORKFLOW_DIAGRAMS.md files, why I chose each approach, and how all the pieces
fit together. I wrote this so that anyone picking up this project -- whether a
new team member, a reviewer, or future-me -- can understand the reasoning without
having to reverse-engineer it from code.

---

## What PROJECT_ARCHITECTURE.md Covers

### The System Architecture Overview (Page 1)

I drew this as a top-down layered diagram because that is how the traffic actually
flows: client at the top, infrastructure in the middle, data stores at the bottom.

**Why I structured it this way:**
I find that most people understand systems fastest when they can trace a request
from the outside in. The diagram starts with the client, passes through the
ingress/load balancer layer, enters the Kubernetes cluster, hits the FastAPI
application, and finally reaches the backing services (MongoDB, Groq API,
Prometheus). Each layer is visually nested so you can see the boundaries.

**Why Nginx/Ingress sits outside the application:**
I separated the TLS termination and L7 rate limiting into the ingress layer
because that is standard practice in production Kubernetes. The application still
does its own rate limiting (token-bucket per IP), but the ingress provides a
first line of defence. Defence in depth -- I never rely on a single layer.

### The Internal Component Map (Page 2)

This is the part that I think is most useful for developers. I broke the FastAPI
application into its constituent modules and showed exactly what each one does.

**Middleware Stack -- why this order matters:**
I listed the middleware in execution order: CORS first, then Metrics, then
RequestID. CORS has to be first because if a preflight OPTIONS request fails CORS
validation, we do not want it polluting our metrics or generating request IDs.
MetricsMiddleware wraps the entire request lifecycle so the latency histogram
captures everything including downstream middleware. RequestIDMiddleware is
innermost so it runs earliest on the request path and latest on the response
path, ensuring every log line within the request has the ID available.

**Exception Handlers -- why a layered approach:**
I registered four exception handlers in a specific priority order:
1. `GenueException` -- our custom exceptions with semantic status codes
2. `HTTPException` -- FastAPI's built-in exceptions
3. `RequestValidationError` -- Pydantic validation failures
4. A catch-all `Exception` handler

The reason I did not just use a single catch-all is that each type carries
different information. A GenueException has a `.details` dict that we want to
include in the response. A RequestValidationError has structured field-level
errors. The catch-all exists solely as a safety net -- in production, I never
want a raw Python traceback reaching the client.

**Security Module -- why three separate concerns:**
I split security into JWT authentication, rate limiting, and input sanitization
because they serve different purposes and I wanted each to be independently
testable:

- **JWT (HS256 with PyJWT):** I chose HS256 over RS256 because this is a
  single-service application. HS256 is simpler -- one shared secret. If I were
  building a microservices mesh where multiple services need to verify tokens
  independently without sharing secrets, I would switch to RS256 with a public
  key. But for GenueChat, HS256 keeps the configuration minimal.

- **Token-bucket rate limiter:** I chose token-bucket over sliding-window or
  fixed-window because it handles bursts more gracefully. A fixed-window counter
  can allow 2x the limit at the window boundary (100 requests at T-1s plus 100
  at T+1s). Token-bucket smooths this out naturally. The implementation is
  in-memory, which is appropriate for single-instance or sticky-session
  deployments. For a multi-instance setup behind a load balancer without sticky
  sessions, I would move this to Redis.

- **Input sanitization:** I do two things: HTML/XSS stripping and MongoDB
  injection prevention. The HTML sanitization removes `<script>` tags, strips
  all HTML elements, and escapes special characters. The MongoDB sanitization
  removes `$` and `{}` characters that could be used in operator injection
  attacks. I kept these as simple regex-based functions rather than pulling in a
  heavy library because the input is plain text questions, not rich content.

**LLM Core -- why the dual-path design:**
The `handle_chat_async` function routes to either the ConversationChain (for
general chat) or the RAG pipeline (for document Q&A). I kept both paths because
they serve fundamentally different use cases:

- The ConversationChain maintains a memory buffer, so multi-turn conversations
  feel natural. It does not need document context.
- The RAG pipeline loads a document, chunks it, embeds it into FAISS, retrieves
  relevant passages, and sends them to the LLM as context. It is stateless --
  each document upload creates a fresh vector store.

I wrapped both in `asyncio.run_in_executor()` because LangChain's chains are
synchronous. Running them directly in an async route handler would block the
event loop. The executor offloads them to a thread pool so FastAPI can continue
serving other requests concurrently.

**Database -- why singleton + Motor:**
I used the singleton pattern for the MongoDB client because connection pooling
works best when there is exactly one pool shared across the application. Creating
multiple `AsyncIOMotorClient` instances would create multiple pools, wasting
connections. The singleton ensures every part of the application uses the same
pool (min 10, max 50 connections).

I chose Motor (the async MongoDB driver) over PyMongo because the application is
async-first with FastAPI. Using synchronous PyMongo would require wrapping every
database call in `run_in_executor()`, which adds overhead and complexity. Motor
speaks natively to the asyncio event loop.

The configurable timeouts (5000ms for both server selection and connection) are
there because I have seen production systems hang indefinitely when MongoDB
becomes unreachable. A 5-second timeout is long enough for normal operations but
short enough to fail fast during outages.

**Configuration -- why lru_cache:**
The `get_settings()` function is decorated with `@lru_cache()` so the Settings
object is instantiated exactly once. Without this, every call would re-read the
.env file and re-validate all fields. In a FastAPI application where settings are
accessed on every request (for CORS checks, rate limit values, etc.), this
caching is essential for performance.

I used `pydantic-settings` (Pydantic v2's BaseSettings) because it gives me
automatic type coercion from environment strings, validation, and documentation
in one place. The `Environment` enum constrains the ENVIRONMENT variable to
exactly three valid values, preventing typos from causing subtle bugs.

### Infrastructure Diagrams

**Docker Compose -- why four services:**
I included four services because they represent the minimum viable production
monitoring stack:
1. The application itself
2. MongoDB (the data layer)
3. Prometheus (metrics collection)
4. Grafana (visualisation)

I could have left out Prometheus and Grafana, but then developers running
locally would not be able to see their metrics. Having the full observability
stack in Docker Compose means what you see locally is close to what runs in
production.

**Kubernetes layout -- why these five resources:**
- **Deployment:** The core workload. Two replicas give basic availability.
- **Service:** ClusterIP because the application is accessed via Ingress, not
  directly from outside the cluster.
- **HPA:** Auto-scales between 2 and 10 pods. I chose CPU 70% and memory 80%
  as triggers because LLM inference is CPU-bound, and embedding generation can
  spike memory usage.
- **NetworkPolicy:** I restricted ingress to only the ingress controller and
  egress to only MongoDB (27017) and HTTPS (443, for the Groq API). This
  follows the principle of least privilege at the network level.
- **Ingress:** TLS termination and external routing. I used the nginx ingress
  class because it is the most widely deployed. The rate-limit annotation
  provides cluster-edge rate limiting on top of the application-level limiter.

---

## What WORKFLOW_DIAGRAMS.md Covers

### Chat Request Flow (Diagram 1)

I drew this as a sequence-style diagram showing every step a chat request passes
through. The reason I included every intermediate step (middleware, rate limiter,
JWT verify, Pydantic validate, sanitize, LLM call, audit log) is that when
something goes wrong in production, you need to know exactly where in the chain
the failure occurred. This diagram serves as a debugging map.

The arrows showing error responses (429, 401, 422) branch off at each validation
step. I drew them explicitly because understanding where and why requests get
rejected is just as important as understanding the happy path.

### Document Q&A Flow (Diagram 2)

This diagram is more detailed than the chat flow because the RAG pipeline has
more moving parts. I showed the complete chain: PDF loading, text splitting,
embedding, FAISS indexing, retrieval, and LLM generation.

**Why I included the specific parameters (chunk_size=1000, overlap=200):**
These numbers are important for understanding retrieval quality. The 1000-character
chunk size balances between too-small chunks (which lose context) and too-large
chunks (which dilute relevance). The 200-character overlap ensures that
information at chunk boundaries is not lost. I called these out explicitly so
anyone tuning retrieval quality knows where to start.

### Authentication Flow (Diagram 3)

I split this into two sub-flows: token generation and token usage. The generation
flow shows the rate limiting check, credential validation, JWT creation, and
audit logging. The usage flow shows token extraction and verification.

**Why I showed the JWT payload fields (sub, exp, iat):**
These three claims are the minimum for a functional JWT. `sub` (subject)
identifies the user, `exp` (expiration) prevents indefinite token validity, and
`iat` (issued at) helps with token rotation auditing. I included HS256 and
SECRET_KEY references so it is clear what needs to be consistent across
deployment instances.

### Application Lifecycle (Diagram 4)

I drew the startup/shutdown sequence because it is critical for understanding
deployment behaviour. The key insight is that the application will start and
serve requests even if MongoDB is unavailable -- it logs a warning but does not
crash. I made this decision because a chat application that works without a
database (just without persistence) is more useful than one that refuses to start.

The shutdown sequence ensures the database connection pool is drained cleanly.
In Kubernetes, this matters because a pod receiving SIGTERM has a grace period
(default 30 seconds) to finish in-flight requests and close connections. If I
did not close the Motor client, those connections would be abandoned and MongoDB
would have to wait for them to timeout.

### CI/CD Pipeline (Diagram 5)

I drew the three-job pipeline (lint, test, build) with explicit dependency arrows
because the execution order matters:
1. **Lint first** because it is fast and catches style issues before wasting
   compute on tests.
2. **Test second** because it needs lint to pass (no point testing malformed code).
3. **Build third** because it verifies the Docker image compiles, but only if the
   code is correct and tested.

The MongoDB service container in the test job deserves a note: I included it so
integration tests that touch the database can run in CI without mocking. However,
the current test suite uses mocks for the database, so the service container is
there for when someone adds database-level integration tests in the future.

### Monitoring Data Flow (Diagram 6)

I showed two parallel flows: metrics and logs. The metrics path goes from the
application to Prometheus (via scraping) to Grafana (via PromQL queries). The
logging path goes from the application to stdout, which in a containerized
environment gets picked up by the container runtime's logging driver.

**Why I did not include a specific log aggregator:**
I kept the logging output as structured JSON to stdout because the choice of log
aggregator (ELK, Loki, CloudWatch, Datadog) depends on the deployment
environment. By writing structured JSON to stdout, the application is compatible
with any aggregator. The diagram shows this as an open-ended arrow to
"centralized log aggregator" to make the integration point clear without
prescribing a specific tool.

### Rate Limiting Algorithm (Diagram 7)

I included a worked example with a timeline table because token-bucket is often
misunderstood. The table shows exactly what happens when 101 requests arrive
simultaneously (100 allowed, 1 denied) and how the bucket refills over time. This
is the kind of reference I wish I had when debugging rate limiting issues in
production.

### Exception Handling Flow (Diagram 8)

I drew this as a decision tree because that is literally how the FastAPI exception
handler resolution works. It checks exception types in registration order and
dispatches to the first matching handler. The key design decision I wanted to
highlight is that every path ends with the same structured JSON format. Whether
the client gets a 401, 422, or 500, the response body shape is identical. This
makes it straightforward for API consumers to implement a single error-handling
path in their code.

---

## Design Principles Behind These Choices

**1. Defence in depth:**
I never rely on a single layer for security. Rate limiting happens at the ingress
AND the application. Input validation happens via Pydantic AND sanitization.
Authentication checks happen in middleware AND route dependencies.

**2. Fail fast, fail gracefully:**
Timeouts are configured everywhere (database, JWT expiration). The application
starts even if MongoDB is down. Error responses are structured and informative
without leaking implementation details.

**3. Observable by default:**
Every request gets a unique ID. Every operation is metered with Prometheus. Every
log line is structured JSON. Audit events are recorded for compliance. I did not
make monitoring optional -- it is baked into the middleware stack so developers
cannot accidentally skip it.

**4. Simple until proven otherwise:**
I used in-memory rate limiting instead of Redis. I used HS256 instead of RS256.
I used FAISS instead of a managed vector database. Each of these can be upgraded
when the scale demands it, but starting simple reduces operational complexity and
debugging surface area.

**5. Configuration over code:**
Every behaviour that might change between environments is controlled by
environment variables. CORS origins, rate limits, database pool sizes, logging
levels, feature flags (like Prometheus enable/disable) -- all configurable
without code changes or redeployment.
