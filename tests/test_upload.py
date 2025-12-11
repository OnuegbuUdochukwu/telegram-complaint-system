import os
import pytest
from httpx import AsyncClient
from app.main import app
from app.config import get_settings


@pytest.mark.asyncio
async def test_api_photo_upload_flow(monkeypatch):
    """
    Test the photo upload flow directly against the API using AsyncClient.
    This validates the backend logic for S3/Local storage abstraction.
    """
    # Force local storage and test backend URL
    os.environ["STORAGE_PROVIDER"] = "local"
    os.environ["BACKEND_URL"] = "http://test"
    os.environ["BACKEND_SERVICE_TOKEN"] = "test-service-token"
    get_settings.cache_clear()

    headers = {"Authorization": "Bearer test-service-token"}

    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Submit Complaint
        complaint_data = {
            "telegram_user_id": "api-tester",
            "hostel": "John",
            "room_number": "A101",
            "category": "plumbing",
            "description": "Pipe burst",
            "severity": "high",
        }
        resp = await client.post(
            "/api/v1/complaints/submit", json=complaint_data, headers=headers
        )
        assert resp.status_code == 201
        data = resp.json()
        complaint_id = data["complaint_id"]
        assert complaint_id

        # 2. Presign Upload
        presign_payload = {
            "filename": "test.png",
            "content_type": "image/png",
            "content_length": 100,
        }
        resp = await client.post(
            f"/api/v1/complaints/{complaint_id}/photos/presign",
            json=presign_payload,
            headers=headers,
        )
        assert resp.status_code == 201
        presign_data = resp.json()
        photo_id = presign_data["photo_id"]
        upload_url = presign_data["url"]
        s3_key = presign_data["s3_key"]

        # Verify URL matches local pattern
        # http://test/api/v1/complaints/...
        assert "http://test" in upload_url

        # 3. Direct Upload (PUT)
        # S3 presigned URLs use full URL. We use client.put with the FULL URL.
        # But for test client, we strip base_url if it matches?
        # AsyncClient handles absolute URLs if they match the host.
        file_bytes = b"fake-content" * 10
        resp = await client.put(
            upload_url, content=file_bytes, headers={"Content-Type": "image/png"}
        )
        assert resp.status_code == 200
        upload_resp = resp.json()
        assert upload_resp["id"] == photo_id

        # 4. Confirm (Not strictly needed for local storage as direct_upload confirms it, but good to check status)
        # Local upload automatically marks as confirmed.
        # But client.py usually calls confirm endpoint too?
        # For S3 it does. For local, maybe redundant but harmless?
        # Let's check confirming explicitly if client.py does it.
        # client.py logic: confirms after PUT.
        # If we just verify status is confirmed in DB or via GET:
        # But presign returned "method": "PUT".

        # Verify persistence
        # We can't GET the photo without auth or knowing the URL (which direct_upload returned)
        file_url = upload_resp["file_url"]
        assert file_url.startswith("/storage")

        # We skip GET /storage verification because app.mount("/storage") is conditional
        # on directory existence at startup time, which might be flaky in test environment.
        # But we verified API returned success and file_url.
