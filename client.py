"""Backend client stubs for the Telegram complaint bot (Phase 1).

This module provides lightweight stubs for backend interactions so the bot
can be tested end-to-end without a real API. If the environment variable
`BACKEND_URL` is set, the stubs will attempt a real HTTP call using
`httpx.AsyncClient` and fall back to deterministic mock responses on error or when
`BACKEND_URL` is not provided.

Public API:
- submit_complaint(data: dict) -> dict
- get_complaint_status(complaint_id: str) -> dict

These are intentionally simple and safe for local development and testing.
"""

from __future__ import annotations

import os
import time
import asyncio
import logging
import random
from typing import Any, Dict, Optional

import httpx
import mimetypes

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL")  # e.g. http://localhost:8000
# Allow an operator/dev to explicitly enable mock fallback even when BACKEND_URL
# is set. This should be OFF in production. Accepts truthy strings: 1/true/yes
_ALLOW_MOCK_ENV = os.getenv("BACKEND_ALLOW_MOCK", "false").lower()
ALLOW_MOCK_FALLBACK = _ALLOW_MOCK_ENV in ("1", "true", "yes")

# HTTP client defaults
_DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
_MAX_RETRIES = 3
_BACKOFF_FACTOR = 0.5

# Reuse a global client for connection pooling when BACKEND_URL is set
_client: Optional[httpx.AsyncClient] = None

def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
    return _client


def _mock_complaint_id() -> str:
  return f"MOCK-{int(time.time())}"


def _is_retryable(exc: Exception, response: Optional[httpx.Response]) -> bool:
  # network errors are retryable; 5xx responses are retryable
  if isinstance(exc, httpx.RequestError):
    return True
  if response is not None and 500 <= response.status_code < 600:
    return True
  return False


async def _attempt_request(method: str, url: str, **kwargs) -> Dict[str, Any]:
  last_exc: Optional[Exception] = None
  for attempt in range(1, _MAX_RETRIES + 1):
    try:
      client = _get_client()
      resp = await client.request(method, url, **kwargs)
      # Treat 4xx as non-retryable client error
      if 400 <= resp.status_code < 500:
        resp.raise_for_status()
      # For 5xx, raise to trigger retry
      if 500 <= resp.status_code < 600:
        resp.raise_for_status()
      return resp.json()
    except Exception as exc:
      last_exc = exc
      # Determine if we should retry
      response = exc.response if hasattr(exc, "response") else None
      if attempt == _MAX_RETRIES or not _is_retryable(exc, response):
        logger.warning("Request to %s failed (attempt %s/%s): %s", url, attempt, _MAX_RETRIES, exc)
        break
      backoff = _BACKOFF_FACTOR * (2 ** (attempt - 1))
      jitter = random.uniform(0, backoff * 0.1)
      sleep_time = backoff + jitter
      logger.info("Retrying %s in %.2fs (attempt %s/%s)", url, sleep_time, attempt + 1, _MAX_RETRIES)
      await asyncio.sleep(sleep_time)

  raise last_exc if last_exc is not None else RuntimeError("Request failed without exception")


async def submit_complaint(data: Dict[str, Any]) -> Dict[str, Any]:
  """Submit complaint to backend with retries and fallback to mock.

  Returns a dict with at least 'status' and 'complaint_id' keys on success.
  """
  if BACKEND_URL:
    url = BACKEND_URL.rstrip("/") + "/api/v1/complaints/submit"
    try:
      token = await _get_service_token()
      headers = {"Authorization": f"Bearer {token}"} if token else {}
      return await _attempt_request("POST", url, json=data, headers=headers)
    except Exception as exc:  # pragma: no cover - network fallback
      logger.warning("Backend POST to %s failed after retries: %s", url, exc)
      # If operator explicitly allows mock fallback (dev only), return a mock
      # ID; otherwise propagate the error so the caller can surface it and
      # avoid creating misleading MOCK- IDs in production workflows.
      if not ALLOW_MOCK_FALLBACK:
        raise
      logger.warning("BACKEND_ALLOW_MOCK is enabled; falling back to mock complaint id")

  # fallback mock response (either BACKEND_URL not set or fallback allowed)
  mock = {"status": "success", "complaint_id": _mock_complaint_id()}
  logger.info("Returning mock submit response: %s", mock)
  return mock


async def get_complaint_status(complaint_id: str) -> Dict[str, Any]:
  """Get complaint status from backend with retries and mock fallback."""
  if BACKEND_URL:
    url = BACKEND_URL.rstrip("/") + f"/api/v1/complaints/{complaint_id}"
    try:
      token = await _get_service_token()
      headers = {"Authorization": f"Bearer {token}"} if token else {}
      return await _attempt_request("GET", url, headers=headers)
    except Exception as exc:  # pragma: no cover - network fallback
      logger.warning("Backend GET %s failed after retries: %s", url, exc)

  # Mock status rotation (simple deterministic behaviour based on timestamp)
  ts = int(time.time())
  statuses = ["reported", "in_progress", "on_hold", "resolved"]
  status = statuses[ts % len(statuses)]
  mock = {"status": status, "complaint_id": complaint_id}
  logger.info("Returning mock status response: %s", mock)
  return mock


async def get_user_complaints(telegram_user_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
  """Get all complaints for a specific user from backend with retries and mock fallback."""
  if BACKEND_URL:
    url = BACKEND_URL.rstrip("/") + f"/api/v1/complaints"
    params = {
      "telegram_user_id": telegram_user_id,
      "page": page,
      "page_size": page_size
    }
    try:
      token = await _get_service_token()
      headers = {"Authorization": f"Bearer {token}"} if token else {}
      return await _attempt_request("GET", url, params=params, headers=headers)
    except Exception as exc:
      logger.warning("Backend GET %s failed after retries: %s", url, exc)

  # Mock response with a few sample complaints
  mock_items = []
  for i in range(3):
    ts = int(time.time()) - i * 3600  # Stagger times
    statuses = ["reported", "in_progress", "resolved"]
    status = statuses[(ts // 100) % len(statuses)]
    mock_items.append({
      "id": f"COMP-{int(time.time())}-{i}",
      "telegram_user_id": telegram_user_id,
      "hostel": ["John", "Joseph", "Paul"][i % 3],
      "room_number": f"A{100 + i}",
  "category": ["plumbing", "electrical", "carpentry"][i % 3],
      "description": f"Sample complaint {i + 1}",
      "severity": "medium",
      "status": status,
      "created_at": f"2024-01-{(1 + i)}T10:00:00Z"
    })
  
  mock = {
    "items": mock_items,
    "total": len(mock_items),
    "page": page,
    "page_size": page_size,
    "total_pages": 1
  }
  logger.info("Returning mock user complaints response: %s", mock)
  return mock


# Small convenience for manual testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo = {"telegram_user_id": "123456", "hostel": "A", "room_number": "A101", "category": "plumbing", "description": "Leaking sink"}
    
    async def main():
        print(await submit_complaint(demo))
        print(await get_complaint_status("MOCK-12345"))
    
    asyncio.run(main())


async def _get_service_token() -> Optional[str]:
  """Return a service token to authorize backend uploads.

  Priority:
  - BACKEND_SERVICE_TOKEN env var (explicit token)
  - BACKEND_SERVICE_EMAIL & BACKEND_SERVICE_PASSWORD: call /auth/login
  """
  token = os.getenv("BACKEND_SERVICE_TOKEN")
  if token:
    return token

  email = os.getenv("BACKEND_SERVICE_EMAIL")
  password = os.getenv("BACKEND_SERVICE_PASSWORD")
  if BACKEND_URL and email and password:
    url = BACKEND_URL.rstrip("/") + "/auth/login"
    try:
      # The backend expects form data (OAuth2PasswordRequestForm), so post as form
      client = _get_client()
      resp = await client.post(url, data={"username": email, "password": password})
      if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token")
      else:
        logger.warning("Service login failed with status %s: %s", resp.status_code, resp.text)
    except Exception as exc:
      logger.warning("Service login error: %s", exc)
  return None


async def upload_photo(complaint_id: str, file_bytes: bytes, filename: str, mime_type: Optional[str] = None) -> Dict[str, Any]:
    """Upload photo bytes using the presigned S3 pipeline."""
    if not BACKEND_URL:
        mock = {
            "id": f"MOCK-PHOTO-{int(time.time())}",
            "complaint_id": complaint_id,
            "file_url": f"/storage/{complaint_id}/{filename}",
            "thumbnail_url": None,
            "file_name": filename,
            "file_size": len(file_bytes),
        }
        logger.info("Returning mock upload_photo response: %s", mock)
        return mock

    token = await _get_service_token()
    if not token:
        raise RuntimeError("Service token required for photo uploads; set BACKEND_SERVICE_TOKEN.")

    mime = mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    headers = {"Authorization": f"Bearer {token}"}
    base = BACKEND_URL.rstrip("/")

    # Step 1: Request presigned URL
    presign_payload = {
        "filename": filename,
        "content_type": mime,
        "content_length": len(file_bytes),
    }
    presign = await _attempt_request(
        "POST",
        f"{base}/api/v1/complaints/{complaint_id}/photos/presign",
        json=presign_payload,
        headers=headers,
    )

    # Step 2: PUT to S3
    method = presign.get("method", "PUT").upper()
    upload_url = presign["url"]
    client = _get_client()
    if method != "PUT":
        raise RuntimeError(f"Unsupported presign method {method}")

    put_headers = {"Content-Type": mime}
    resp = await client.put(upload_url, content=file_bytes, headers=put_headers)
    resp.raise_for_status()

    # Step 3: Confirm upload back to backend
    confirm_payload = {
        "photo_id": presign["photo_id"],
        "s3_key": presign["s3_key"],
        "file_size": len(file_bytes),
        "content_type": mime,
    }
    confirmation = await _attempt_request(
        "POST",
        f"{base}/api/v1/complaints/{complaint_id}/photos/confirm",
        json=confirm_payload,
        headers=headers,
    )
    return confirmation
