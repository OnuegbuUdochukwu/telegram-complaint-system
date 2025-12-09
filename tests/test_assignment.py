import httpx
import pytest

BASE = "http://127.0.0.1:8001"

@pytest.fixture
def create_and_token(make_porter):
    """Helper to create a porter and return (id, token)."""
    def _create(email: str, role: str = "porter"):
        return make_porter(email, role=role)

    return _create


@pytest.mark.asyncio
async def test_admin_assigns_another_porter(admin_token, create_and_token):
    # Create two porters via fixture (fix: await the async factory)
    p1_id, p1_token = await create_and_token("a1@example.com")
    p2_id, p2_token = await create_and_token("a2@example.com")

    # Submit complaint
    payload = {"telegram_user_id": "assign-user", "hostel": "H1", "room_number": "A101", "category": "test", "description": "assign test", "severity": "low"}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"{BASE}/api/v1/complaints/submit", json=payload)
        assert r.status_code == 201
        cid = r.json()["complaint_id"]

        # Admin assigns p2
        headers = {"Authorization": f"Bearer {admin_token}"}
        r = await client.patch(f"{BASE}/api/v1/complaints/{cid}/assign", json={"assigned_porter_id": p2_id}, headers=headers)
        assert r.status_code == 200
        assert r.json()["assigned_porter_id"] == p2_id


@pytest.mark.asyncio
async def test_porter_assigns_self_then_fails_assign_other(create_and_token, admin_token):
    # Fix await
    p_id, token = await create_and_token("self@example.com")
    other_id, other_token = await create_and_token("other@example.com")

    payload = {"telegram_user_id": "assign-user-2", "hostel": "H1", "room_number": "A102", "category": "test", "description": "assign test 2", "severity": "low"}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"{BASE}/api/v1/complaints/submit", json=payload)
        assert r.status_code == 201
        cid = r.json()["complaint_id"]

        headers = {"Authorization": f"Bearer {token}"}
        # Porter assigns self
        r = await client.patch(f"{BASE}/api/v1/complaints/{cid}/assign", json={"assigned_porter_id": p_id}, headers=headers)
        assert r.status_code == 200
        assert r.json()["assigned_porter_id"] == p_id

        # Assert audit row exists (admin-only endpoint)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        audit_r = await client.get(f"{BASE}/api/v1/complaints/{cid}/assignments", headers=admin_headers)
        assert audit_r.status_code == 200
        audits = audit_r.json()
        assert isinstance(audits, list)
        assert len(audits) >= 1
        # The latest audit should match the assignment
        found = any(a["assigned_to"] == p_id and a["complaint_id"] == cid for a in audits)
        assert found, f"Audit row for assignment to {p_id} not found: {audits}"

        # Porter tries to assign someone else -> 403
        r = await client.patch(f"{BASE}/api/v1/complaints/{cid}/assign", json={"assigned_porter_id": other_id}, headers=headers)
        assert r.status_code == 403