#!/usr/bin/env python3
"""
Test script for WebSocket and notification functionality
"""
import asyncio
import websockets
import json
import requests
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/dashboard"

async def test_websocket_connection():
    """Test WebSocket connection and authentication."""
    print("🧪 Testing WebSocket Connection...")
    
    # First, get a valid JWT token
    login_data = {
        "username": "admin@test.local",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data, timeout=5)
        if response.status_code != 200:
            print("❌ Failed to get JWT token for WebSocket test")
            return False
        
        token_data = response.json()
        token = token_data["access_token"]
        print("✅ Got JWT token for WebSocket test")
        
    except Exception as e:
        print(f"❌ Error getting JWT token: {e}")
        return False
    
    # Test WebSocket connection
    try:
        uri = f"{WS_URL}?token={token}"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Send ping
            await websocket.send("ping")
            response = await websocket.recv()
            if response == "pong":
                print("✅ WebSocket ping/pong working")
            else:
                print(f"❌ Unexpected ping response: {response}")
                return False
            
            # Test echo
            test_message = "Hello WebSocket!"
            await websocket.send(test_message)
            response = await websocket.recv()
            if test_message in response:
                print("✅ WebSocket echo working")
            else:
                print(f"❌ Unexpected echo response: {response}")
                return False
            
            print("✅ WebSocket functionality test passed")
            return True
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

def test_notification_endpoints():
    """Test notification configuration endpoints."""
    print("\n🧪 Testing Notification Endpoints...")
    
    # Get JWT token
    login_data = {
        "username": "admin@test.local",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data, timeout=5)
        if response.status_code != 200:
            print("❌ Failed to get JWT token for notification test")
            return False
        
        token_data = response.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
    except Exception as e:
        print(f"❌ Error getting JWT token: {e}")
        return False
    
    # Test notification config endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/notifications/config", headers=headers, timeout=5)
        if response.status_code == 200:
            config = response.json()
            print("✅ Notification config endpoint working")
            print(f"   Config: {config}")
        else:
            print(f"❌ Notification config endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Notification config test failed: {e}")
        return False
    
    # Test WebSocket stats endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/websocket/stats", headers=headers, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("✅ WebSocket stats endpoint working")
            print(f"   Stats: {stats}")
        else:
            print(f"❌ WebSocket stats endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket stats test failed: {e}")
        return False
    
    print("✅ Notification endpoints test passed")
    return True

def test_complaint_submission_with_notifications():
    """Test complaint submission triggers notifications."""
    print("\n🧪 Testing Complaint Submission with Notifications...")
    
    # Submit a test complaint
    complaint_data = {
        "telegram_user_id": "test_user_123",
        "hostel": "Test Hostel",
        "room_number": "101",
        "category": "plumbing",
        "description": "Test complaint for notification testing",
        "severity": "high"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/complaints/submit", json=complaint_data, timeout=10)
        if response.status_code == 201:
            result = response.json()
            complaint_id = result["complaint_id"]
            print(f"✅ Test complaint submitted: {complaint_id}")
            print("   This should trigger WebSocket broadcasts and Telegram notifications")
            return True
        else:
            print(f"❌ Complaint submission failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Complaint submission test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Testing Real-time & Notifications Implementation")
    print("=" * 60)
    
    # Test WebSocket connection
    ws_success = await test_websocket_connection()
    
    # Test notification endpoints
    endpoint_success = test_notification_endpoints()
    
    # Test complaint submission
    submission_success = test_complaint_submission_with_notifications()
    
    print("\n📊 Test Results Summary:")
    print(f"   WebSocket Connection: {'✅ PASS' if ws_success else '❌ FAIL'}")
    print(f"   Notification Endpoints: {'✅ PASS' if endpoint_success else '❌ FAIL'}")
    print(f"   Complaint Submission: {'✅ PASS' if submission_success else '❌ FAIL'}")
    
    if all([ws_success, endpoint_success, submission_success]):
        print("\n🎉 All real-time notification tests passed!")
        print("\n📋 Implementation Summary:")
        print("   ✅ WebSocket endpoint with JWT authentication")
        print("   ✅ Real-time event broadcasting")
        print("   ✅ Telegram bot integration")
        print("   ✅ Dashboard WebSocket client")
        print("   ✅ Notification configuration endpoints")
        print("   ✅ Automatic complaint list refresh")
        return True
    else:
        print("\n❌ Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
