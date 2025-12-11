import pytest
import respx
from httpx import Response
import os
from client import (
    submit_complaint,
    get_complaint_status,
    get_user_complaints,
    _get_service_token,
)


# Mock environment variables for all tests in this module
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    # Patch the module-level variable because it's read at import time
    monkeypatch.setattr("client.BACKEND_URL", "http://test-backend")
    monkeypatch.setenv("BACKEND_SERVICE_TOKEN", "test-token-123")
    # Also reset the client to ensure fresh state
    monkeypatch.setattr("client._client", None)


@pytest.mark.asyncio
async def test_submit_complaint_sends_auth_header():
    """Verify submit_complaint sends the correct Authorization header."""
    async with respx.mock(base_url="http://test-backend") as respx_mock:
        route = respx_mock.post("/api/v1/complaints/submit").mock(
            return_value=Response(
                201, json={"complaint_id": "123", "status": "recieved"}
            )
        )

        await submit_complaint({"test": "data"})

        assert route.called
        request = route.calls.last.request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer test-token-123"


@pytest.mark.asyncio
async def test_get_complaint_status_sends_auth_header():
    """Verify get_complaint_status sends the correct Authorization header."""
    async with respx.mock(base_url="http://test-backend") as respx_mock:
        route = respx_mock.get("/api/v1/complaints/C-1").mock(
            return_value=Response(200, json={"id": "C-1", "status": "resolved"})
        )

        await get_complaint_status("C-1")

        assert route.called
        request = route.calls.last.request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer test-token-123"


@pytest.mark.asyncio
async def test_get_user_complaints_sends_auth_header():
    """Verify get_user_complaints sends the correct Authorization header."""
    async with respx.mock(base_url="http://test-backend") as respx_mock:
        route = respx_mock.get("/api/v1/complaints").mock(
            return_value=Response(200, json={"items": [], "total": 0})
        )

        await get_user_complaints("U-99")

        assert route.called
        request = route.calls.last.request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer test-token-123"


@pytest.mark.asyncio
async def test_service_token_login_flow(monkeypatch):
    """Verify _get_service_token logs in if explicit token is missing but credentials exist."""
    monkeypatch.delenv("BACKEND_SERVICE_TOKEN", raising=False)
    monkeypatch.setenv("BACKEND_SERVICE_EMAIL", "service@bot.local")
    monkeypatch.setenv("BACKEND_SERVICE_PASSWORD", "password")

    async with respx.mock(base_url="http://test-backend") as respx_mock:
        route = respx_mock.post("/auth/login").mock(
            return_value=Response(200, json={"access_token": "logged-in-token"})
        )

        token = await _get_service_token()

        assert token == "logged-in-token"
        assert route.called
        request = route.calls.last.request
        # Check that it sent form data (or json if client changed? Client code sends data=...)
        # httpx post(data=dict) sends form-encoded.
        assert "username=service%40bot.local" in request.read().decode()
