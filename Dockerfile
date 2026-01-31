# =============================================================================
# GenueChat Production Dockerfile -- Multi-stage build
# =============================================================================

# -- Stage 1: Builder --------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -- Stage 2: Production image -----------------------------------------------
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r genuechat && useradd -r -g genuechat -d /app -s /sbin/nologin genuechat

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Ensure the non-root user owns the working directory
RUN chown -R genuechat:genuechat /app

USER genuechat

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/live')" || exit 1

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
