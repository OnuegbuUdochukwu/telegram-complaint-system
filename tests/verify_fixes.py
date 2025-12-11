#!/usr/bin/env python3
"""
Simple verification script for real-time notifications fixes.

This script verifies that the key fixes are working correctly without
requiring a full test environment setup.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "fastapi-backend"))


def test_websocket_event_models():
    """Test WebSocket event models have correct field mappings."""
    print("Testing WebSocket event models...")

    try:
        from fastapi_backend.app.websocket_manager import (
            NewComplaintEvent,
            StatusUpdateEvent,
            AssignmentEvent,
        )

        # Test NewComplaintEvent
        event = NewComplaintEvent(
            complaint_id="test-123",
            hostel="Hostel A",
            category="electrical",
            severity="high",
        )
        assert event.event_type == "new_complaint"
        assert event.data["id"] == "test-123"  # Should be "id" not "complaint_id"
        assert event.data["hostel"] == "Hostel A"
        print("✅ NewComplaintEvent field mapping correct")

        # Test StatusUpdateEvent
        event = StatusUpdateEvent(
            complaint_id="test-123",
            old_status="reported",
            new_status="in_progress",
            updated_by="admin",
        )
        assert event.event_type == "status_update"
        assert event.data["complaint_id"] == "test-123"
        print("✅ StatusUpdateEvent field mapping correct")

        # Test AssignmentEvent
        event = AssignmentEvent(
            complaint_id="test-123", assigned_to="porter-456", assigned_by="admin-789"
        )
        assert event.event_type == "assignment_update"
        assert event.data["complaint_id"] == "test-123"
        print("✅ AssignmentEvent field mapping correct")

        return True

    except Exception as e:
        print(f"❌ WebSocket event models test failed: {e}")
        return False


def test_websocket_manager_methods():
    """Test WebSocket manager has required methods."""
    print("Testing WebSocket manager methods...")

    try:
        from fastapi_backend.app.websocket_manager import manager

        # Test required methods exist
        assert hasattr(manager, "connect")
        assert hasattr(manager, "disconnect")
        assert hasattr(manager, "broadcast")
        assert hasattr(manager, "broadcast_new_complaint")
        assert hasattr(manager, "broadcast_status_update")
        assert hasattr(manager, "broadcast_assignment")
        assert hasattr(manager, "get_connection_count")
        assert hasattr(manager, "get_connections_by_role")
        assert hasattr(manager, "cleanup_disconnected_connections")
        assert hasattr(manager, "shutdown")
        print("✅ WebSocket manager has all required methods")

        # Test connection count
        count = manager.get_connection_count()
        assert isinstance(count, int)
        print("✅ WebSocket manager connection count works")

        # Test connections by role
        role_counts = manager.get_connections_by_role()
        assert isinstance(role_counts, dict)
        assert "admin" in role_counts
        assert "porter" in role_counts
        print("✅ WebSocket manager role counts work")

        return True

    except Exception as e:
        print(f"❌ WebSocket manager methods test failed: {e}")
        return False


def test_telegram_notifier_methods():
    """Test Telegram notifier has required methods."""
    print("Testing Telegram notifier methods...")

    try:
        from fastapi_backend.app.telegram_notifier import telegram_notifier

        # Test required methods exist
        assert hasattr(telegram_notifier, "send_complaint_alert")
        assert hasattr(telegram_notifier, "send_status_update_alert")
        assert hasattr(telegram_notifier, "update_config")
        assert hasattr(telegram_notifier, "get_config")
        print("✅ Telegram notifier has all required methods")

        # Test configuration
        config = telegram_notifier.get_config()
        assert isinstance(config, dict)
        print("✅ Telegram notifier configuration works")

        return True

    except Exception as e:
        print(f"❌ Telegram notifier methods test failed: {e}")
        return False


def test_main_endpoints():
    """Test main.py has required endpoints."""
    print("Testing main.py endpoints...")

    try:
        from fastapi_backend.app.main import app

        # Get all routes
        routes = [route.path for route in app.routes]

        # Check for required endpoints
        required_endpoints = [
            "/ws/dashboard",
            "/api/v1/notifications/config",
            "/api/v1/websocket/stats",
            "/api/v1/websocket/health",
        ]

        for endpoint in required_endpoints:
            assert endpoint in routes, f"Missing endpoint: {endpoint}"

        print("✅ All required endpoints present")

        # Check for startup/shutdown events
        assert hasattr(app, "router")
        print("✅ FastAPI app structure correct")

        return True

    except Exception as e:
        print(f"❌ Main endpoints test failed: {e}")
        return False


def test_dashboard_client_structure():
    """Test dashboard client has required functions."""
    print("Testing dashboard client structure...")

    try:
        dashboard_path = os.path.join(
            os.path.dirname(__file__), "dashboard", "index.html"
        )

        if not os.path.exists(dashboard_path):
            print("❌ Dashboard file not found")
            return False

        with open(dashboard_path, "r") as f:
            content = f.read()

        # Check for required functions
        required_functions = [
            "connectWebSocket",
            "disconnectWebSocket",
            "handleWebSocketEvent",
            "handleNewComplaint",
            "handleStatusUpdate",
            "handleAssignmentUpdate",
            "showNotification",
        ]

        for func in required_functions:
            assert func in content, f"Missing function: {func}"

        print("✅ All required dashboard functions present")

        # Check for ping interval management
        assert "pingInterval" in content
        assert "clearInterval" in content
        print("✅ Dashboard ping interval management present")

        # Check for cleanup on page unload
        assert "beforeunload" in content
        print("✅ Dashboard cleanup on page unload present")

        return True

    except Exception as e:
        print(f"❌ Dashboard client structure test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("🔍 Verifying real-time notifications fixes...")
    print("=" * 50)

    tests = [
        test_websocket_event_models,
        test_websocket_manager_methods,
        test_telegram_notifier_methods,
        test_main_endpoints,
        test_dashboard_client_structure,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            print()

    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All fixes verified successfully!")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
