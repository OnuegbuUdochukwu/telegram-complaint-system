import os
import httpx
import time

BASE_URL = os.getenv("TEST_BACKEND_URL", "http://127.0.0.1:8001")


def _register_and_login(email: str = None, phone: str = None, password: str = "testpass"):
    # Create a porter for testing using the dev /auth/register endpoint
    data = {"full_name": "Test Porter", "password": password}
    if email:
        data["email"] = email
    if phone:
        data["phone"] = phone

    resp = httpx.post(f"{BASE_URL}/auth/register", json=data, timeout=10.0)
    assert resp.status_code == 200, f"Register failed: {resp.status_code} {resp.text}"
    jd = resp.json()
    porter_id = jd.get("id")

    # Login
    login_data = {"username": email or phone, "password": password}
    token_resp = httpx.post(f"{BASE_URL}/auth/login", data=login_data, timeout=10.0)
    assert token_resp.status_code == 200, f"Login failed: {token_resp.status_code} {token_resp.text}"
    token_j = token_resp.json()
    return porter_id, token_j["access_token"]


def test_update_status_success():
    # Register and login a porter using phone
    porter_id, token = _register_and_login(email="porter@example.com")

    # Submit a complaint
    payload = {
        "telegram_user_id": "test-user-2",
        "hostel": "TestHostel",
        "room_number": "T102",
        "category": "electric",
        "description": "Integration test: flickering light",
        "severity": "medium",
    }
    post_resp = httpx.post(f"{BASE_URL}/api/v1/complaints/submit", json=payload, timeout=10.0)
    assert post_resp.status_code == 201, f"POST failed: {post_resp.status_code} {post_resp.text}"
    complaint_id = post_resp.json()["complaint_id"]

    # Update status
    headers = {"Authorization": f"Bearer {token}"}
    patch_resp = httpx.patch(f"{BASE_URL}/api/v1/complaints/{complaint_id}/status", json={"status": "in_progress"}, headers=headers, timeout=10.0)
    assert patch_resp.status_code == 200, f"PATCH failed: {patch_resp.status_code} {patch_resp.text}"
    updated = patch_resp.json()
    assert updated.get("status") == "in_progress"


def test_update_status_invalid_status():
    porter_id, token = _register_and_login(email="porter2@example.com")
    payload = {
        "telegram_user_id": "test-user-3",
        "hostel": "TestHostel",
        "room_number": "T103",
        "category": "cleaning",
        "description": "Integration test: dirty corridor",
        "severity": "low",
    }
    post_resp = httpx.post(f"{BASE_URL}/api/v1/complaints/submit", json=payload, timeout=10.0)
    assert post_resp.status_code == 201
    complaint_id = post_resp.json()["complaint_id"]

    headers = {"Authorization": f"Bearer {token}"}
    bad_resp = httpx.patch(f"{BASE_URL}/api/v1/complaints/{complaint_id}/status", json={"status": "not_a_real_status"}, headers=headers, timeout=10.0)
    assert bad_resp.status_code == 400


def test_update_status_unauthorized():
    payload = {
        "telegram_user_id": "test-user-4",
        "hostel": "TestHostel",
        "room_number": "T104",
        "category": "pest",
        "description": "Integration test: pest sighting",
        "severity": "high",
    }
    post_resp = httpx.post(f"{BASE_URL}/api/v1/complaints/submit", json=payload, timeout=10.0)
    assert post_resp.status_code == 201
    complaint_id = post_resp.json()["complaint_id"]

    # No Authorization header
    noauth = httpx.patch(f"{BASE_URL}/api/v1/complaints/{complaint_id}/status", json={"status": "in_progress"}, timeout=10.0)
    assert noauth.status_code in (401, 403)
