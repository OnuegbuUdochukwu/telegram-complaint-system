import os
import httpx
import pytest

BASE = os.getenv("TEST_BACKEND_URL", "http://127.0.0.1:8001")


def _register_and_login(email: str):
    data = {"full_name": "Test Porter", "password": "testpass", "email": email}
    resp = httpx.post(f"{BASE}/auth/register", json=data, timeout=10.0)
    assert resp.status_code == 200
    porter_id = resp.json().get("id")

    login_data = {"username": email, "password": "testpass"}
    token_resp = httpx.post(f"{BASE}/auth/login", data=login_data, timeout=10.0)
    assert token_resp.status_code == 200
    token_json = token_resp.json()
    token = token_json.get("access_token")
    # Prefer the id returned with the token (token subject) if present
    login_id = token_json.get("id")
    # If ALLOW_DEV_REGISTER is enabled, prefer calling the dev-token endpoint
    # which returns a deterministic token and id.
    if os.environ.get("ALLOW_DEV_REGISTER") in ("1", "true", "True"):
        r = httpx.post(f"{BASE}/auth/dev-token", json={"email": email}, timeout=5.0)
        if r.status_code == 200:
            dj = r.json()
            return dj.get("id"), dj.get("access_token")

    return (login_id or porter_id), token


def _get_admin_token():
    # Try env or helper script
    t = os.environ.get("TEST_ADMIN_TOKEN")
    if t:
        return t
    # First try registering admin via HTTP (dev mode). This requires the server to be started with ALLOW_DEV_REGISTER=1
    admin_email = os.environ.get("TEST_ADMIN_EMAIL", "admin@example.com")
    admin_password = os.environ.get("TEST_ADMIN_PASSWORD", "adminpass")
    try:
        r = httpx.post(f"{BASE}/auth/register", json={"full_name": "Admin", "email": admin_email, "password": admin_password}, timeout=5.0)
        if r.status_code == 200:
            # Login to get token
            lr = httpx.post(f"{BASE}/auth/login", data={"username": admin_email, "password": admin_password}, timeout=5.0)
            if lr.status_code == 200:
                return lr.json().get("access_token")
    except Exception:
        pass

    # Fallback: run helper script if present
    script = os.path.join(os.getcwd(), "fastapi-backend", "scripts", "get_admin_token.py")
    if os.path.exists(script):
        import subprocess
        out = subprocess.check_output(["python", script, "--email", admin_email, "--password", admin_password], text=True)
        for line in out.splitlines():
            if line.strip().startswith("ey"):
                return line.strip()
    pytest.skip("No admin token available")


def test_admin_assigns_another_porter():
    admin_token = _get_admin_token()
    # Create two porters
    p1_id, p1_token = _register_and_login("a1@example.com")
    p2_id, p2_token = _register_and_login("a2@example.com")

    # Submit complaint
    payload = {"telegram_user_id": "assign-user", "hostel": "H1", "room_number": "R1", "category": "test", "description": "assign test", "severity": "low"}
    r = httpx.post(f"{BASE}/api/v1/complaints/submit", json=payload)
    assert r.status_code == 201
    cid = r.json()["complaint_id"]

    # Admin assigns p2
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = httpx.patch(f"{BASE}/api/v1/complaints/{cid}/assign", json={"assigned_porter_id": p2_id}, headers=headers)
    assert r.status_code == 200
    assert r.json()["assigned_porter_id"] == p2_id


def test_porter_assigns_self_then_fails_assign_other():
    p_id, token = _register_and_login("self@example.com")
    other_id, other_token = _register_and_login("other@example.com")

    payload = {"telegram_user_id": "assign-user-2", "hostel": "H1", "room_number": "R2", "category": "test", "description": "assign test 2", "severity": "low"}
    r = httpx.post(f"{BASE}/api/v1/complaints/submit", json=payload)
    assert r.status_code == 201
    cid = r.json()["complaint_id"]

    headers = {"Authorization": f"Bearer {token}"}
    # Porter assigns self
    r = httpx.patch(f"{BASE}/api/v1/complaints/{cid}/assign", json={"assigned_porter_id": p_id}, headers=headers)
    assert r.status_code == 200
    assert r.json()["assigned_porter_id"] == p_id

    # Porter tries to assign someone else -> 403
    r = httpx.patch(f"{BASE}/api/v1/complaints/{cid}/assign", json={"assigned_porter_id": other_id}, headers=headers)
    assert r.status_code == 403