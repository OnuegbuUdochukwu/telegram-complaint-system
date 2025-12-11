import os
import httpx


BASE_URL = os.getenv("TEST_BACKEND_URL", "http://127.0.0.1:8001")


def test_submit_and_get_complaint():
    """Integration test: submit a complaint and read it back from the API.

    This test assumes a FastAPI server is running and reachable at
    TEST_BACKEND_URL or http://127.0.0.1:8001. It posts a minimal complaint
    payload (omitting `wing`) and asserts that the API returns 201 and
    a complaint id, then fetches the complaint and validates some fields.
    """
    payload = {
        "telegram_user_id": "test-user-1",
        "hostel": "John",
        "room_number": "A101",
        "category": "plumbing",
        "description": "Integration test: leaking pipe",
        "severity": "low",
    }

    # POST the complaint
    post_resp = httpx.post(
        f"{BASE_URL}/api/v1/complaints/submit", json=payload, timeout=10.0
    )
    assert (
        post_resp.status_code == 201
    ), f"POST failed: {post_resp.status_code} {post_resp.text}"
    jd = post_resp.json()
    assert "complaint_id" in jd, f"Missing complaint_id in response: {jd}"
    complaint_id = jd["complaint_id"]

    # GET the complaint back
    get_resp = httpx.get(f"{BASE_URL}/api/v1/complaints/{complaint_id}", timeout=10.0)
    assert (
        get_resp.status_code == 200
    ), f"GET failed: {get_resp.status_code} {get_resp.text}"
    item = get_resp.json()

    # Validate core fields
    assert item.get("id") == complaint_id or item.get("complaint_id") == complaint_id
    assert item.get("telegram_user_id") == payload["telegram_user_id"]
    assert item.get("room_number") == payload["room_number"]
    assert item.get("category") == payload["category"]
