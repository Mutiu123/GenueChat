"""Health check and status endpoints."""

import time

from fastapi import APIRouter

from src.config import get_settings
from src.database import get_database
from src.schemas import HealthResponse

router = APIRouter(tags=["Health"])
settings = get_settings()
_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Full health check including database",
)
async def health_check() -> HealthResponse:
    """Check API and database health."""
    checks = {"api": "healthy"}
    db = get_database()
    try:
        if await db.health_check():
            checks["database"] = "healthy"
        else:
            checks["database"] = "unhealthy"
    except Exception:
        checks["database"] = "unavailable"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    return HealthResponse(
        status=overall,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT.value,
        uptime_seconds=round(time.time() - _start_time, 2),
        checks=checks,
    )


@router.get("/health/live", summary="Liveness probe")
async def liveness() -> dict:
    """Lightweight liveness probe for Kubernetes."""
    return {"status": "alive"}


@router.get("/health/ready", summary="Readiness probe")
async def readiness() -> dict:
    """Readiness probe -- checks database connectivity."""
    db = get_database()
    try:
        ok = await db.health_check()
    except Exception:
        ok = False
    if not ok:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "not ready"})
    return {"status": "ready"}


@router.get("/status", summary="Application status")
async def status() -> dict:
    """Return basic application status metadata."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
        "uptime_seconds": round(time.time() - _start_time, 2),
    }
