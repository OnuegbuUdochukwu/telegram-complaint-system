import os
import httpx


BASE_URL = os.getenv("TEST_BACKEND_URL", "http://127.0.0.1:8001")


def test_missing_required_field_returns_422():
    # Omit telegram_user_id which is required
    payload = {
        "hostel": "Mary",
        "room_number": "E101",
        "category": "electrical",
        "description": "Missing telegram_user_id",
        "severity": "low",
    }

    resp = httpx.post(
        f"{BASE_URL}/api/v1/complaints/submit",
        json=payload,
        headers={"Authorization": "Bearer test-service-token"},
        timeout=10.0,
    )
    assert resp.status_code == 422
    j = resp.json()
    assert any(
        "telegram_user_id" in str(item.get("loc", [])) for item in j.get("detail", [])
    )


def test_invalid_field_type_returns_422():
    # room_number should be a string; supply an integer to trigger validation error
    payload = {
        "telegram_user_id": "edge-user",
        "hostel": "Mary",
        "room_number": 12345,
        "category": "pest",
        "description": "Invalid room number type",
        "severity": "medium",
    }

    resp = httpx.post(
        f"{BASE_URL}/api/v1/complaints/submit",
        json=payload,
        headers={"Authorization": "Bearer test-service-token"},
        timeout=10.0,
    )
    assert resp.status_code == 422


def test_dashboard_requires_basic_auth_and_allows_with_credentials():
    # Without credentials: should be challenged (401)
    resp = httpx.get(f"{BASE_URL}/api/v1/complaints", timeout=10.0)
    assert resp.status_code == 401

    # With basic auth credentials: placeholder guard accepts any credentials, so expect 200
    auth = ("admin", "password")
    resp2 = httpx.get(f"{BASE_URL}/api/v1/complaints", auth=auth, timeout=10.0)
    assert resp2.status_code == 200
