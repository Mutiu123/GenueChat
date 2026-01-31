"""Authentication endpoints."""

from fastapi import APIRouter, Depends

from src.monitoring import AUTH_EVENTS, METRICS_AVAILABLE, log_audit_event
from src.schemas import TokenRequest, TokenResponse
from src.security import check_rate_limit, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Generate a JWT access token",
    dependencies=[Depends(check_rate_limit)],
)
async def generate_token(body: TokenRequest) -> TokenResponse:
    """Issue a JWT token for the given credentials.

    In a production system this would validate against a user store.
    For this release it accepts any non-empty credentials and returns
    a signed token -- replace the body of this function with real
    credential verification when integrating with an identity provider.
    """
    token, expires_in = create_access_token(subject=body.username)
    if METRICS_AVAILABLE:
        AUTH_EVENTS.labels(event="token_issued").inc()
    log_audit_event("token_issued", user=body.username)
    return TokenResponse(
        access_token=token, token_type="bearer", expires_in=expires_in
    )


@router.get("/me", summary="Get current user info")
async def current_user(user: dict = Depends(get_current_user)) -> dict:
    """Return decoded token claims for the authenticated user."""
    return {"user": user.get("sub"), "claims": user}
