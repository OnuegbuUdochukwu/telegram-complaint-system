#!/usr/bin/env python3
"""Smoke-test complaint submission and photo presign flow."""

import asyncio
import os

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SERVICE_TOKEN = os.getenv("BACKEND_SERVICE_TOKEN", "dev-service-token-12345")


async def run_smoke_test() -> bool:
    async with httpx.AsyncClient(timeout=30.0) as client:
        complaint_payload = {
            "telegram_user_id": "test_user_12345",
            "hostel": "TestHostel",
            "wing": "A",
            "room_number": "A101",
            "category": "electrical",
            "description": "Test complaint for photo upload verification",
            "severity": "low",
        }
        headers = {"Authorization": f"Bearer {SERVICE_TOKEN}"}

        submit_resp = await client.post(
            f"{BACKEND_URL}/api/v1/complaints/submit",
            json=complaint_payload,
            headers=headers,
        )
        if submit_resp.status_code not in (200, 201):
            print(submit_resp.text)
            return False

        complaint_data = submit_resp.json()
        complaint_id = complaint_data.get("id") or complaint_data.get("complaint_id")

        presign_resp = await client.post(
            f"{BACKEND_URL}/api/v1/complaints/{complaint_id}/photos/presign",
            json={
                "filename": "test_image.jpg",
                "content_type": "image/jpeg",
                "content_length": 1024,
            },
            headers=headers,
        )
        if presign_resp.status_code not in (200, 201):
            print(presign_resp.text)
            return False

        print("Photo presign flow OK")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_smoke_test())
    raise SystemExit(0 if success else 1)
