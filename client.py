"""Backend client stubs for the Telegram complaint bot (Phase 1).

This module provides lightweight stubs for backend interactions so the bot
can be tested end-to-end without a real API. If the environment variable
`BACKEND_URL` is set, the stubs will attempt a real HTTP call using
`requests` and fall back to deterministic mock responses on error or when
`BACKEND_URL` is not provided.

Public API:
- submit_complaint(data: dict) -> dict
- get_complaint_status(complaint_id: str) -> dict

These are intentionally simple and safe for local development and testing.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL")  # e.g. http://localhost:8000


def _mock_complaint_id() -> str:
    """Generate a short deterministic mock complaint id."""
    return f"MOCK-{int(time.time())}"


def submit_complaint(data: Dict[str, Any]) -> Dict[str, Any]:
    """Submit a complaint payload to the backend.

    Behaviour:
    - If BACKEND_URL is set, attempt a POST to {BACKEND_URL}/complaints and return
      the parsed JSON response on success. On network/error, fall back to a
      mock response and log the error.
    - If BACKEND_URL is not set, return a deterministic mock success payload.

    The mock response format:
      {"status": "success", "complaint_id": "MOCK-<unix_ts>"}

    Note: This function intentionally keeps the interface small and synchronous
    to be easy to call from the bot handlers. Replace or extend with async
    behaviour if your real backend requires it.
    """
    if BACKEND_URL:
        url = BACKEND_URL.rstrip("/") + "/complaints"
        try:
            resp = requests.post(url, json=data, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # pragma: no cover - network fallback
            logger.warning("Backend POST to %s failed, falling back to mock response: %s", url, exc)

    # Mock response
    mock = {"status": "success", "complaint_id": _mock_complaint_id()}
    logger.info("Returning mock submit response: %s", mock)
    return mock


def get_complaint_status(complaint_id: str) -> Dict[str, Any]:
    """Retrieve a complaint status.

    Behaviour:
    - If BACKEND_URL is set, attempt a GET to {BACKEND_URL}/complaints/{id}
      and return the parsed JSON response on success. On network/error, fall
      back to a mock response and log the error.
    - If BACKEND_URL is not set, return a deterministic mock status.

    Mock response format:
      {"status": "Resolved", "complaint_id": complaint_id}
    """
    if BACKEND_URL:
        url = BACKEND_URL.rstrip("/") + f"/complaints/{complaint_id}"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # pragma: no cover - network fallback
            logger.warning("Backend GET %s failed, falling back to mock response: %s", url, exc)

    # Mock status rotation (simple deterministic behaviour based on timestamp)
    ts = int(time.time())
    statuses = ["reported", "in_progress", "on_hold", "resolved"]
    status = statuses[ts % len(statuses)]
    mock = {"status": status, "complaint_id": complaint_id}
    logger.info("Returning mock status response: %s", mock)
    return mock


# Small convenience for manual testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo = {"telegram_user_id": "123456", "hostel": "A", "room_number": "A101", "category": "plumbing", "description": "Leaking sink"}
    print(submit_complaint(demo))
    print(get_complaint_status("MOCK-12345"))
