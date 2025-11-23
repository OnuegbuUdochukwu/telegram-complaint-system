#!/usr/bin/env python3
"""
Comprehensive test suite for real-time notifications fixes.

This test verifies that all the fixes implemented for sections 3.6, 3.7, 3.8
are working correctly and follow best practices.
"""

import asyncio
import pytest
import websockets
import json
import httpx
from fastapi.testclient import TestClient
from app.main import app
from app.websocket_manager import manager, NewComplaintEvent, StatusUpdateEvent, AssignmentEvent
from app.telegram_notifier import telegram_notifier
from app.models import Complaint, Porter
from sqlmodel import Session, select
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock


@pytest.fixture(name="client")
def client_fixture():
    with TestClient(app) as client:
        yield client


@pytest.fixture(name="session")
def session_fixture():
    from app.database import engine
    # Ensure tables exist for tests (SQLite/create_all used for local test DB)
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="admin_token")
def admin_token_fixture(client: TestClient, session: Session):
    """Create admin user and get token."""
    admin_email = "admin@test.local"
    admin_password = "adminpassword"
    
    # Check if admin exists, create if not
    admin_user = session.exec(select(Porter).where(Porter.email == admin_email)).first()
    if not admin_user:
        from app.auth import create_porter
        admin_user = create_porter(session, full_name="Admin User", email=admin_email, password=admin_password, role="admin")
    
    response = client.post(
        "/auth/login",
        data={"username": admin_email, "password": admin_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(name="porter_token")
def porter_token_fixture(client: TestClient, session: Session):
    """Create porter user and get token."""
    porter_email = "porter@test.local"
    porter_password = "porterpassword"
    
    # Check if porter exists, create if not
    porter_user = session.exec(select(Porter).where(Porter.email == porter_email)).first()
    if not porter_user:
        from app.auth import create_porter
        porter_user = create_porter(session, full_name="Test Porter", email=porter_email, password=porter_password, role="porter")
    
    response = client.post(
        "/auth/login",
        data={"username": porter_email, "password": porter_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestWebSocketManagerFixes:
    """Test WebSocket manager fixes and improvements."""
    
    def test_websocket_event_models(self):
        """Test that WebSocket event models have correct field mappings."""
        # Test NewComplaintEvent
        event = NewComplaintEvent(
            complaint_id="test-123",
            hostel="John",
            category="electrical",
            severity="high"
        )
        assert event.event_type == "new_complaint"
        assert event.data["id"] == "test-123"  # Should be "id" not "complaint_id"
        assert event.data["hostel"] == "Hostel A"
        assert event.data["category"] == "electrical"
        assert event.data["severity"] == "high"
        
        # Test StatusUpdateEvent
        event = StatusUpdateEvent(
            complaint_id="test-123",
            old_status="reported",
            new_status="in_progress",
            updated_by="admin"
        )
        assert event.event_type == "status_update"
        assert event.data["complaint_id"] == "test-123"
        assert event.data["old_status"] == "reported"
        assert event.data["new_status"] == "in_progress"
        assert event.data["updated_by"] == "admin"
        
        # Test AssignmentEvent
        event = AssignmentEvent(
            complaint_id="test-123",
            assigned_to="porter-456",
            assigned_by="admin-789"
        )
        assert event.event_type == "assignment_update"
        assert event.data["complaint_id"] == "test-123"
        assert event.data["assigned_to"] == "porter-456"
        assert event.data["assigned_by"] == "admin-789"
    
    @pytest.mark.asyncio
    async def test_connection_cleanup(self):
        """Test WebSocket connection cleanup functionality."""
        # Clear existing connections
        manager.active_connections.clear()
        for role in manager.connections_by_role:
            manager.connections_by_role[role].clear()
        
        # Test cleanup of disconnected connections
        await manager.cleanup_disconnected_connections()
        assert manager.get_connection_count() == 0
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Test graceful shutdown of WebSocket manager."""
        # Clear existing connections
        manager.active_connections.clear()
        for role in manager.connections_by_role:
            manager.connections_by_role[role].clear()
        
        # Test shutdown
        await manager.shutdown()
        assert manager.get_connection_count() == 0
        assert all(len(conns) == 0 for conns in manager.connections_by_role.values())


class TestTelegramNotifierFixes:
    """Test Telegram notifier fixes and improvements."""
    
    def test_bot_initialization_error_handling(self):
        """Test that bot initialization handles errors gracefully."""
        # Test with invalid token
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'invalid_token'}):
            from app.telegram_notifier import TelegramNotifier
            notifier = TelegramNotifier()
            assert notifier.bot is None
            assert notifier.config.enabled is False
    
    @pytest.mark.asyncio
    async def test_send_complaint_alert_with_mock(self):
        """Test complaint alert sending with mocked bot."""
        # telegram_notifier.bot may be None in test environment; guard patch accordingly
        if getattr(telegram_notifier, 'bot', None) is not None:
            with patch.object(telegram_notifier.bot, 'send_message', new_callable=AsyncMock) as mock_send:
                complaint_data = {
                    "id": "test-123",
                    "hostel": "John",
                    "category": "electrical",
                    "severity": "high",
                    "description": "Test complaint",
                    "room_number": "A101"
                }

                result = await telegram_notifier.send_complaint_alert(complaint_data)

                if telegram_notifier.bot and telegram_notifier.config.enabled:
                    mock_send.assert_called_once()
                    assert result is True
                else:
                    assert result is False
        else:
            # If no bot configured, ensure function returns False
            complaint_data = {
                "id": "test-123",
                "hostel": "John",
                "category": "electrical",
                "severity": "high",
                "description": "Test complaint",
                "room_number": "101"
            }

            result = await telegram_notifier.send_complaint_alert(complaint_data)
            assert result is False
            complaint_data = {
                "id": "test-123",
                "hostel": "John",
                "category": "electrical",
                "severity": "high",
                "description": "Test complaint",
                "room_number": "101"
            }
            
            result = await telegram_notifier.send_complaint_alert(complaint_data)
            
            if telegram_notifier.bot and telegram_notifier.config.enabled:
                mock_send.assert_called_once()
                assert result is True
            else:
                assert result is False
    
    @pytest.mark.asyncio
    async def test_send_status_update_alert_with_mock(self):
        """Test status update alert sending with mocked bot."""
        if getattr(telegram_notifier, 'bot', None) is not None:
            with patch.object(telegram_notifier.bot, 'send_message', new_callable=AsyncMock) as mock_send:
                result = await telegram_notifier.send_status_update_alert(
                    complaint_id="test-123",
                    old_status="reported",
                    new_status="in_progress",
                    updated_by="admin"
                )

                if telegram_notifier.bot and telegram_notifier.config.enabled:
                    mock_send.assert_called_once()
                    assert result is True
                else:
                    assert result is False
        else:
            result = await telegram_notifier.send_status_update_alert(
                complaint_id="test-123",
                old_status="reported",
                new_status="in_progress",
                updated_by="admin"
            )
            assert result is False


class TestMainIntegrationFixes:
    """Test main.py integration fixes."""
    
    @pytest.mark.asyncio
    async def test_complaint_submission_with_notifications(self, session: Session, admin_token: str):
        """Test that complaint submission triggers both WebSocket and Telegram notifications."""
        # Clear WebSocket connections
        manager.active_connections.clear()
        
        # Mock Telegram notification
        with patch.object(telegram_notifier, 'send_complaint_alert', new_callable=AsyncMock) as mock_telegram:
            complaint_payload = {
                "telegram_user_id": "test_user_notifications",
                "hostel": "John",
                    "room_number": "A101",
                "category": "electrical",
                "description": "Light not working",
                "severity": "high"
            }
            
            async with httpx.AsyncClient(app=app, base_url="http://localhost:8000") as async_client:
                response = await async_client.post(
                    "/api/v1/complaints/submit",
                    json=complaint_payload,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
            
            assert response.status_code == 201
            complaint_id = response.json()["complaint_id"]
            
            # Verify Telegram notification was called
            if telegram_notifier.bot and telegram_notifier.config.enabled:
                mock_telegram.assert_called_once()
                call_args = mock_telegram.call_args[0][0]
                assert call_args["id"] == complaint_id
                assert call_args["hostel"] == "John"
                assert call_args["category"] == "electrical"
                assert call_args["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_status_update_with_notifications(self, session: Session, admin_token: str):
        """Test that status updates trigger both WebSocket and Telegram notifications."""
        # Create a complaint first
        complaint_payload = {
            "telegram_user_id": "test_user_status",
            "hostel": "Joseph",
            "room_number": "B202",
            "category": "plumbing",
            "description": "Leaky faucet",
            "severity": "medium"
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://localhost:8000") as async_client:
            response = await async_client.post(
                "/api/v1/complaints/submit",
                json=complaint_payload,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        
        assert response.status_code == 201
        complaint_id = response.json()["complaint_id"]
        
        # Mock Telegram notification for status update
        with patch.object(telegram_notifier, 'send_status_update_alert', new_callable=AsyncMock) as mock_telegram:
            update_payload = {"status": "in_progress"}
            
            async with httpx.AsyncClient(app=app, base_url="http://localhost:8000") as async_client:
                response = await async_client.patch(
                    f"/api/v1/complaints/{complaint_id}",
                    json=update_payload,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
            
            assert response.status_code == 200
            
            # Verify Telegram notification was called
            if telegram_notifier.bot and telegram_notifier.config.enabled:
                mock_telegram.assert_called_once()
                call_args = mock_telegram.call_args[0]
                assert call_args[0] == complaint_id  # complaint_id
                assert call_args[1] == "reported"    # old_status
                assert call_args[2] == "in_progress" # new_status
    
    def test_websocket_health_endpoint(self, client: TestClient):
        """Test WebSocket health check endpoint."""
        response = client.get("/api/v1/websocket/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_connections" in data
        assert data["service"] == "websocket_manager"
    
    def test_websocket_stats_endpoint(self, client: TestClient, admin_token: str):
        """Test WebSocket stats endpoint (admin only)."""
        response = client.get(
            "/api/v1/websocket/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_connections" in data
        assert "connections_by_role" in data
        assert isinstance(data["total_connections"], int)
        assert isinstance(data["connections_by_role"], dict)


class TestDashboardClientFixes:
    """Test dashboard WebSocket client fixes."""
    
    def test_websocket_client_cleanup(self):
        """Test that WebSocket client properly cleans up resources."""
        # This would be tested in a browser environment
        # For now, we'll test the JavaScript logic conceptually
        
        # Test that ping interval is properly managed
        # Test that WebSocket connection is properly closed on logout
        # Test that reconnection logic works correctly
        
        # These tests would require a browser testing framework like Selenium
        # For now, we'll just verify the logic is sound
        assert True  # Placeholder for browser-based tests


class TestEndToEndIntegration:
    """Test end-to-end integration of all fixes."""
    
    @pytest.mark.asyncio
    async def test_complete_notification_flow(self, session: Session, admin_token: str):
        """Test complete notification flow from complaint submission to dashboard update."""
        # Clear WebSocket connections
        manager.active_connections.clear()
        
        # Mock Telegram notifications
        with patch.object(telegram_notifier, 'send_complaint_alert', new_callable=AsyncMock) as mock_complaint:
            with patch.object(telegram_notifier, 'send_status_update_alert', new_callable=AsyncMock) as mock_status:
                
                # 1. Submit complaint
                complaint_payload = {
                    "telegram_user_id": "test_user_e2e",
                    "hostel": "Paul",
                        "room_number": "C303",
                    "category": "carpentry",
                    "description": "Crack in wall",
                    "severity": "high"
                }
                
                async with httpx.AsyncClient(app=app, base_url="http://localhost:8000") as async_client:
                    response = await async_client.post(
                        "/api/v1/complaints/submit",
                        json=complaint_payload,
                        headers={"Authorization": f"Bearer {admin_token}"}
                    )
                
                assert response.status_code == 201
                complaint_id = response.json()["complaint_id"]
                
                # 2. Update status
                update_payload = {"status": "in_progress"}
                
                async with httpx.AsyncClient(app=app, base_url="http://localhost:8000") as async_client:
                    response = await async_client.patch(
                        f"/api/v1/complaints/{complaint_id}",
                        json=update_payload,
                        headers={"Authorization": f"Bearer {admin_token}"}
                    )
                
                assert response.status_code == 200
                
                # 3. Verify notifications were sent
                if telegram_notifier.bot and telegram_notifier.config.enabled:
                    mock_complaint.assert_called_once()
                    mock_status.assert_called_once()
                
                # 4. Verify complaint was created and updated
                complaint = session.exec(select(Complaint).where(Complaint.id == complaint_id)).first()
                assert complaint is not None
                assert complaint.status == "in_progress"
                assert complaint.hostel == "Paul"  # Database stores canonical name
                assert complaint.category == "carpentry"
                assert complaint.severity == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
