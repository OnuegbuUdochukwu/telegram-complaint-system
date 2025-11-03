import httpx
import pytest

BASE = "http://127.0.0.1:8001"

@pytest.fixture
def create_and_token(make_porter):
    """Helper to create a porter and return (id, token)."""
    def _create(email: str, role: str = "porter"):
        return make_porter(email, role=role)

    return _create


def test_admin_assigns_another_porter(admin_token, create_and_token):
    # Create two porters via fixture
    p1_id, p1_token = create_and_token("a1@example.com")
    p2_id, p2_token = create_and_token("a2@example.com")

    # Submit complaint
    payload = {"telegram_user_id": "assign-user", "hostel": "H1", "room_number": "A101", "category": "test", "description": "assign test", "severity": "low"}
    r = httpx.post(f"{BASE}/api/v1/complaints/submit", json=payload)
    assert r.status_code == 201
    cid = r.json()["complaint_id"]

    # Admin assigns p2
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = httpx.patch(f"{BASE}/api/v1/complaints/{cid}/assign", json={"assigned_porter_id": p2_id}, headers=headers)
    assert r.status_code == 200
    assert r.json()["assigned_porter_id"] == p2_id


def test_porter_assigns_self_then_fails_assign_other(create_and_token, admin_token):
    p_id, token = create_and_token("self@example.com")
    other_id, other_token = create_and_token("other@example.com")

    payload = {"telegram_user_id": "assign-user-2", "hostel": "H1", "room_number": "A102", "category": "test", "description": "assign test 2", "severity": "low"}
    r = httpx.post(f"{BASE}/api/v1/complaints/submit", json=payload)
    assert r.status_code == 201
    cid = r.json()["complaint_id"]

    headers = {"Authorization": f"Bearer {token}"}
    # Porter assigns self
    r = httpx.patch(f"{BASE}/api/v1/complaints/{cid}/assign", json={"assigned_porter_id": p_id}, headers=headers)
    assert r.status_code == 200
    assert r.json()["assigned_porter_id"] == p_id

    # Assert audit row exists (admin-only endpoint)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    audit_r = httpx.get(f"{BASE}/api/v1/complaints/{cid}/assignments", headers=admin_headers)
    assert audit_r.status_code == 200
    audits = audit_r.json()
    assert isinstance(audits, list)
    assert len(audits) >= 1
    # The latest audit should match the assignment
    found = any(a["assigned_to"] == p_id and a["complaint_id"] == cid for a in audits)
    assert found, f"Audit row for assignment to {p_id} not found: {audits}"

    # Porter tries to assign someone else -> 403
    r = httpx.patch(f"{BASE}/api/v1/complaints/{cid}/assign", json={"assigned_porter_id": other_id}, headers=headers)
    assert r.status_code == 403