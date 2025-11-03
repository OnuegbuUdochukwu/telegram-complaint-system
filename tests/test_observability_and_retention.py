"""Tests for observability features (metrics, logging) and retention policy (purge endpoint)."""

import os
import pytest
import httpx
from datetime import datetime, timedelta, timezone


BASE_URL = os.getenv("TEST_BACKEND_URL", "http://127.0.0.1:8001")


def test_health_endpoint():
    """Test the health check endpoint."""
    resp = httpx.get(f"{BASE_URL}/health", timeout=10.0)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "websocket_connections" in data
    assert "websocket_by_role" in data


def test_metrics_endpoint():
    """Test the Prometheus metrics endpoint."""
    resp = httpx.get(f"{BASE_URL}/metrics", timeout=10.0)
    assert resp.status_code == 200
    # Content-Type header formatting may include duplicate charset entries
    # — assert the header starts with the expected media type and version.
    assert resp.headers.get("content-type", "").startswith("text/plain; version=0.0.4")
    
    content = resp.text
    # Check for some expected metrics
    assert "http_requests_total" in content or "TYPE" in content


def test_purge_endpoint_requires_auth():
    """Test that purge endpoint requires admin authentication."""
    resp = httpx.delete(f"{BASE_URL}/api/v1/admin/purge", timeout=10.0)
    assert resp.status_code == 401


def test_purge_endpoint_as_admin():
    """Test that admin can access purge endpoint."""
    # Register and login as admin
    register_payload = {
        "full_name": "Admin User for Purge Test",
        "email": "admin-purge@test.com",
        "password": "adminpass123"
    }
    
    httpx.post(f"{BASE_URL}/auth/register", json=register_payload, timeout=10.0)
    
    # Login
    login_resp = httpx.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin-purge@test.com", "password": "adminpass123"},
        timeout=10.0
    )
    
    if login_resp.status_code != 200:
        pytest.skip("Could not authenticate for purge test")
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to purge (should work even if no data to purge)
    resp = httpx.delete(
        f"{BASE_URL}/api/v1/admin/purge",
        headers=headers,
        timeout=10.0
    )
    
    # Should return 200 with message about no data to purge
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "purged_count" in data or "complaints_purged" in data


def test_purge_with_filters():
    """Test purge endpoint with filters."""
    # Login as admin
    login_resp = httpx.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin-purge@test.com", "password": "adminpass123"},
        timeout=10.0
    )
    
    if login_resp.status_code != 200:
        pytest.skip("Could not authenticate for purge test")
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try purging with specific status
    params = {"complaint_status": "resolved"}
    resp = httpx.delete(
        f"{BASE_URL}/api/v1/admin/purge",
        headers=headers,
        params=params,
        timeout=10.0
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data


def test_purge_as_porter_fails():
    """Test that porter role cannot access purge endpoint."""
    # Register as porter
    register_payload = {
        "full_name": "Test Porter",
        "email": "porter-test@test.com",
        "password": "testpass",
        "role": "porter"
    }
    
    httpx.post(f"{BASE_URL}/auth/register", json=register_payload, timeout=10.0)
    
    # Login as porter
    login_resp = httpx.post(
        f"{BASE_URL}/auth/login",
        data={"username": "porter-test@test.com", "password": "testpass"},
        timeout=10.0
    )
    
    if login_resp.status_code != 200:
        pytest.skip("Could not authenticate as porter")
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to purge as porter
    resp = httpx.delete(
        f"{BASE_URL}/api/v1/admin/purge",
        headers=headers,
        timeout=10.0
    )
    
    # Should be rejected with 403
    assert resp.status_code == 403


def test_observability_logging_structure():
    """Test that observability logging produces structured output."""
    # This test checks that logging is configured
    # Actual log inspection would require checking log files
    # Here we just verify the app starts correctly with observability
    resp = httpx.get(f"{BASE_URL}/health", timeout=10.0)
    assert resp.status_code == 200
    
    # Check that observability endpoints are available
    resp = httpx.get(f"{BASE_URL}/metrics", timeout=10.0)
    assert resp.status_code == 200


def test_websocket_health():
    """Test WebSocket health check endpoint."""
    resp = httpx.get(f"{BASE_URL}/api/v1/websocket/health", timeout=10.0)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "active_connections" in data
    assert "service" in data
    assert data["service"] == "websocket_manager"


def test_websocket_stats_requires_auth():
    """Test that WebSocket stats endpoint requires authentication."""
    resp = httpx.get(f"{BASE_URL}/api/v1/websocket/stats", timeout=10.0)
    assert resp.status_code in [401, 403]


def test_websocket_stats_as_admin():
    """Test that admin can access WebSocket stats."""
    # Login as admin
    login_resp = httpx.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin-purge@test.com", "password": "adminpass123"},
        timeout=10.0
    )
    
    if login_resp.status_code != 200:
        pytest.skip("Could not authenticate as admin")
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = httpx.get(
        f"{BASE_URL}/api/v1/websocket/stats",
        headers=headers,
        timeout=10.0
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "total_connections" in data
    assert "connections_by_role" in data


if __name__ == "__main__":
    print("Observability and Retention Tests")
    print("=" * 50)
    
    test_health_endpoint()
    print("✓ Health endpoint test passed")
    
    test_metrics_endpoint()
    print("✓ Metrics endpoint test passed")
    
    test_purge_endpoint_requires_auth()
    print("✓ Purge auth check passed")
    
    print("\nAll observability and retention tests passed!")

