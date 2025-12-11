import os
import time
import json
import pytest
from httpx import Client

from fastapi import status as http_status


BASE = "http://127.0.0.1:8001"


def get_admin_token():
    # try to get admin token via helper script endpoint if available
    # fallback: environment variable TEST_ADMIN_TOKEN
    token = os.environ.get("TEST_ADMIN_TOKEN")
    if token:
        return token

    # try seeding admin via script if present
    try:
        import subprocess

        script = os.path.join(
            os.getcwd(), "fastapi-backend", "scripts", "get_admin_token.py"
        )
        if os.path.exists(script):
            out = subprocess.check_output(["python", script], text=True)
            # script prints token line as JSON or token on last line
            for line in out.splitlines():
                if line.strip().startswith("ey"):
                    return line.strip()
    except Exception:
        pass

    pytest.skip("No admin token available")


def test_admin_can_list_and_close_complaint():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # list complaints (should be accessible)
    r = Client().get(f"{BASE}/api/v1/complaints", headers=headers)
    assert r.status_code in (200, 204)

    # submit a complaint to close
    data = {"description": "RBAC test", "room_number": "A101", "hostel_id": 1}
    r = Client().post(f"{BASE}/api/v1/complaints/submit", json=data)
    assert r.status_code == 201
    comp = r.json()
    comp_id = comp["id"] if isinstance(comp, dict) and "id" in comp else comp

    # admin closes complaint
    r = Client().patch(
        f"{BASE}/api/v1/complaints/{comp_id}/status",
        json={"status": "closed"},
        headers=headers,
    )
    assert r.status_code == 200


def test_porter_cannot_close_complaint():
    # create a porter via seed if available or use TEST_PORTER_TOKEN
    porter_token = os.environ.get("TEST_PORTER_TOKEN")
    if not porter_token:
        pytest.skip("No porter token provided")

    headers = {"Authorization": f"Bearer {porter_token}"}

    # submit complaint
    data = {"description": "RBAC porter test", "room_number": "B202", "hostel_id": 1}
    r = Client().post(f"{BASE}/api/v1/complaints/submit", json=data)
    assert r.status_code == 201
    comp = r.json()
    comp_id = comp.get("id") if isinstance(comp, dict) else comp

    # porter attempts to close -> should be forbidden (403)
    r = Client().patch(
        f"{BASE}/api/v1/complaints/{comp_id}/status",
        json={"status": "closed"},
        headers=headers,
    )
    assert r.status_code == 403
