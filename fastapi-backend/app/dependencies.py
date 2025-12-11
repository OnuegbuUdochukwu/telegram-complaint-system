"""Common FastAPI dependencies."""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session
from . import auth
from .models import Porter
from .upload_metrics import UPLOAD_AUTH_FAILURES
from .config import get_settings


async def get_authenticated_user_or_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Porter:
    """
    Accepts either a porter JWT bearer token or the opaque BACKEND_SERVICE_TOKEN.

    Returns a Porter-like object on success; raises HTTPException(401) otherwise.
    """

    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        UPLOAD_AUTH_FAILURES.inc()
        raise HTTPException(status_code=401, detail="Not authenticated", headers={"X-Auth-Reason": "Missing bearer token"})

    token = auth_header.split(None, 1)[1]
    token = token.strip().strip("'\"")

    svc_token = get_settings().service_token
    if svc_token and token == svc_token:
        synthetic = Porter(id="service-token", full_name="service-token", role="service")
        return synthetic

    try:
        payload = auth.decode_access_token(token)
    except HTTPException:
        UPLOAD_AUTH_FAILURES.inc()
        raise

    porter = await session.get(Porter, payload.sub)
    if not porter:
        UPLOAD_AUTH_FAILURES.inc()
        raise HTTPException(status_code=401, detail="Invalid token subject")

    return porter


__all__ = ["get_authenticated_user_or_service"]

