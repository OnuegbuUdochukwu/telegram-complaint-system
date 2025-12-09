import os
import pytest
from httpx import AsyncClient
from app.main import app
from app.config import get_settings

# Ensure we use test settings
os.environ["BACKEND_SERVICE_TOKEN"] = "test-service-token"
os.environ["STORAGE_PROVIDER"] = "local"

@pytest.mark.asyncio
async def test_submit_complaint_requires_auth():
    """Verify that submitting a complaint without a token fails."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        complaint_data = {
            "telegram_user_id": "12345",
            "hostel": "John",
            "room_number": "A101",
            "category": "plumbing",
            "description": "Pipe burst",
            "severity": "high",
        }
        resp = await client.post("/api/v1/complaints/submit", json=complaint_data)
        assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_submit_complaint_with_service_token():
    """Verify that submitting a complaint with a valid service token succeeds."""
    headers = {"Authorization": "Bearer test-service-token"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        complaint_data = {
            "telegram_user_id": "12345",
            "hostel": "John",
            "room_number": "A101",
            "category": "plumbing",
            "description": "Pipe burst",
            "severity": "high",
        }
        resp = await client.post("/api/v1/complaints/submit", json=complaint_data, headers=headers)
        assert resp.status_code == 201
        assert "complaint_id" in resp.json()

@pytest.mark.asyncio
async def test_bot_list_complaints():
    """Verify that a bot user can list their own complaints without a bearer token (public access via query param)."""
    # First submit a complaint to have something to list
    headers = {"Authorization": "Bearer test-service-token"}
    tg_id = "99999"
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Submit
        complaint_data = {
            "telegram_user_id": tg_id,
            "hostel": "Peter",
            "room_number": "B202",
            "category": "electrical",
            "description": "Lights out",
            "severity": "medium",
        }
        await client.post("/api/v1/complaints/submit", json=complaint_data, headers=headers)
        
        # List as bot (no auth header, but filtering by telegram_user_id)
        resp = await client.get(f"/api/v1/complaints?telegram_user_id={tg_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["items"][0]["telegram_user_id"] == tg_id

@pytest.mark.asyncio
async def test_get_complaint_details():
    """Verify fetching a specific complaint by ID."""
    headers = {"Authorization": "Bearer test-service-token"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Submit first
        complaint_data = {
            "telegram_user_id": "88888",
            "hostel": "Paul",
            "room_number": "C303",
            "category": "other",
            "description": "Window broken",
            "severity": "low",
        }
        resp = await client.post("/api/v1/complaints/submit", json=complaint_data, headers=headers)
        complaint_id = resp.json()["complaint_id"]
        
        # Get details (this currently requires NO auth? or depends on list logic? verify get_complaint implementation)
        # Looking at main.py: get_complaint does NOT have security dependency!
        # It's currently public... which might be OK for MVP if UUIDs are secret, but let's verify.
        resp = await client.get(f"/api/v1/complaints/{complaint_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == complaint_id
