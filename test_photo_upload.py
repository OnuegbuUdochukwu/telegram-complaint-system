#!/usr/bin/env python3
"""Test script to simulate bot complaint submission and photo upload."""

import asyncio
import httpx
import os
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SERVICE_TOKEN = os.getenv("BACKEND_SERVICE_TOKEN", "dev-service-token-12345")

async def test_complaint_and_photo_upload():
    """Submit a complaint and test photo upload."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Submit a complaint
        print("=" * 60)
        print("Step 1: Submitting test complaint...")
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
        
        try:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/complaints/submit",
                json=complaint_payload,
                headers=headers,
            )
            print(f"  Response status: {resp.status_code}")
            
            if resp.status_code not in (200, 201):
                print(f"  Error: {resp.text}")
                return False
            
            data = resp.json()
            complaint_id = data.get("id") or data.get("complaint_id")
            print(f"  Complaint ID: {complaint_id}")
            
        except Exception as e:
            print(f"  Error submitting complaint: {e}")
            return False
        
        # Step 2: Request presigned upload URL
        print("\n" + "=" * 60)
        print("Step 2: Requesting presigned upload URL...")
        
        presign_payload = {
            "filename": "test_image.jpg",
            "content_type": "image/jpeg",
            "content_length": 1024,  # 1KB dummy size
        }
        
        try:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/complaints/{complaint_id}/photos/presign",
                json=presign_payload,
                headers=headers,
            )
            print(f"  Response status: {resp.status_code}")
            
            if resp.status_code not in (200, 201):
                print(f"  Error: {resp.text}")
                return False
            
            presign_data = resp.json()
            print(f"  Upload ID: {presign_data.get('upload_id')}")
            print(f"  Photo ID: {presign_data.get('photo_id')}")
            print(f"  S3 Key: {presign_data.get('s3_key')}")
            print(f"  Upload URL: {presign_data.get('url', 'N/A')[:80]}...")
            print(f"  Method: {presign_data.get('method')}")
            
        except Exception as e:
            print(f"  Error requesting presign: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n" + "=" * 60)
        print("SUCCESS! Photo presign endpoint works correctly.")
        print("=" * 60)
        return True


if __name__ == "__main__":
    result = asyncio.run(test_complaint_and_photo_upload())
    exit(0 if result else 1)
