#!/usr/bin/env python3
"""Create admin account via API."""
import requests
import json

BACKEND_URL = "http://localhost:8001"

# Register admin
payload = {
    "full_name": "Manual Test Admin",
    "email": "admin@test.local",
    "password": "admin123",
    "role": "admin"
}

try:
    response = requests.post(f"{BACKEND_URL}/auth/register", json=payload)
    if response.status_code == 200:
        print("✅ Admin account created successfully!")
        print(f"   Email: admin@test.local")
        print(f"   Password: admin123")
        print(f"   Response: {response.json()}")
    else:
        print(f"⚠️  Response: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
