import os
import httpx
import pytest

BASE = os.getenv("TEST_BACKEND_URL", "http://127.0.0.1:8001")


@pytest.mark.asyncio
async def test_dashboard_login_and_list_complaints(admin_token, make_porter):
    """Create an admin via fixture, then perform the login flow and call the protected dashboard endpoint.

    This test covers the end-to-end dashboard login flow using the real /auth/login
    form endpoint (OAuth2PasswordRequestForm) and then accesses the admin-only
    GET /api/v1/complaints endpoint using the returned Bearer token.
    """
    # Ensure an admin exists (conftest's admin_token fixture creates one)
    # We will exercise the actual /auth/login endpoint using httpx to POST form data.

    # Create a second admin user to exercise login-by-credentials (email + password)
    # make_porter returns (id, token) but also persists the porter with password 'testpass'
    admin_email = "dashboard-admin@example.com"
    admin_id, _ = await make_porter(admin_email, role="admin")

    # Now perform a login using the OAuth2 password form encoding
    data = {
        "username": admin_email,
        "password": "testpass",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{BASE}/auth/login", data=data)
        assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
        jd = resp.json()
        assert "access_token" in jd, f"Missing access_token in login response: {jd}"
        token = jd["access_token"]

        # Use the returned token to call the protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        list_resp = await client.get(f"{BASE}/api/v1/complaints", headers=headers)

        # The dashboard endpoint returns a PaginatedComplaints model; even if no complaints exist
        # the request should succeed for admin (200) and return JSON with keys including 'items' and 'total'
        assert (
            list_resp.status_code == 200
        ), f"Dashboard list failed: {list_resp.status_code} {list_resp.text}"
        j = list_resp.json()
        assert isinstance(j, dict)
        assert "items" in j and "total" in j
