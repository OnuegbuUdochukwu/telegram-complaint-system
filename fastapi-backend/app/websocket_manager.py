"""
WebSocket and real-time notification management for the complaint system.
"""
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WebSocketEvent(BaseModel):
    """Base model for WebSocket events."""
    event_type: str
    timestamp: datetime = None
    data: Dict[str, Any] = {}

    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now(timezone.utc)
        super().__init__(**data)


class NewComplaintEvent(WebSocketEvent):
    """Event sent when a new complaint is created."""
    event_type: str = "new_complaint"
    data: Dict[str, Any]

    def __init__(self, complaint_id: str, hostel: str, category: str, severity: str, **kwargs):
        data = {
            "complaint_id": complaint_id,
            "hostel": hostel,
            "category": category,
            "severity": severity
        }
        super().__init__(data=data, **kwargs)


class StatusUpdateEvent(WebSocketEvent):
    """Event sent when a complaint status is updated."""
    event_type: str = "status_update"
    data: Dict[str, Any]

    def __init__(self, complaint_id: str, old_status: str, new_status: str, updated_by: str, **kwargs):
        data = {
            "complaint_id": complaint_id,
            "old_status": old_status,
            "new_status": new_status,
            "updated_by": updated_by
        }
        super().__init__(data=data, **kwargs)


class AssignmentEvent(WebSocketEvent):
    """Event sent when a complaint is assigned to a porter."""
    event_type: str = "assignment_update"
    data: Dict[str, Any]

    def __init__(self, complaint_id: str, assigned_to: str, assigned_by: str, **kwargs):
        data = {
            "complaint_id": complaint_id,
            "assigned_to": assigned_to,
            "assigned_by": assigned_by
        }
        super().__init__(data=data, **kwargs)


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        # Store active connections with user info
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
        # Store connections by user role for targeted broadcasting
        self.connections_by_role: Dict[str, List[WebSocket]] = {
            "admin": [],
            "porter": []
        }

    async def connect(self, websocket: WebSocket, user_id: str, user_role: str = "porter"):
        """Accept a WebSocket connection and store user info."""
        await websocket.accept()
        self.active_connections[websocket] = {
            "user_id": user_id,
            "user_role": user_role,
            "connected_at": datetime.now(timezone.utc)
        }
        
        # Add to role-based connections
        if user_role in self.connections_by_role:
            self.connections_by_role[user_role].append(websocket)
        
        logger.info(f"WebSocket connected: user_id={user_id}, role={user_role}")
        return user_id

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            user_info = self.active_connections[websocket]
            user_role = user_info.get("user_role", "porter")
            
            # Remove from role-based connections
            if user_role in self.connections_by_role and websocket in self.connections_by_role[user_role]:
                self.connections_by_role[user_role].remove(websocket)
            
            del self.active_connections[websocket]
            logger.info(f"WebSocket disconnected: user_id={user_info.get('user_id')}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, event: WebSocketEvent, target_role: Optional[str] = None):
        """Broadcast an event to all connected clients or specific role."""
        message = event.model_dump_json()
        
        if target_role:
            # Send to specific role
            connections = self.connections_by_role.get(target_role, [])
        else:
            # Send to all connections
            connections = list(self.active_connections.keys())
        
        if not connections:
            logger.info(f"No connections to broadcast to (role={target_role})")
            return
        
        # Send to all target connections
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)
        
        logger.info(f"Broadcasted {event.event_type} to {len(connections)} connections")

    async def broadcast_new_complaint(self, complaint_id: str, hostel: str, category: str, severity: str):
        """Broadcast a new complaint event to all admins."""
        event = NewComplaintEvent(
            complaint_id=complaint_id,
            hostel=hostel,
            category=category,
            severity=severity
        )
        await self.broadcast(event, target_role="admin")

    async def broadcast_status_update(self, complaint_id: str, old_status: str, new_status: str, updated_by: str):
        """Broadcast a status update event to all connected users."""
        event = StatusUpdateEvent(
            complaint_id=complaint_id,
            old_status=old_status,
            new_status=new_status,
            updated_by=updated_by
        )
        await self.broadcast(event)

    async def broadcast_assignment(self, complaint_id: str, assigned_to: str, assigned_by: str):
        """Broadcast an assignment event to all connected users."""
        event = AssignmentEvent(
            complaint_id=complaint_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by
        )
        await self.broadcast(event)

    def get_connection_count(self) -> int:
        """Get the total number of active connections."""
        return len(self.active_connections)

    def get_connections_by_role(self) -> Dict[str, int]:
        """Get connection count by role."""
        return {
            role: len(connections) 
            for role, connections in self.connections_by_role.items()
        }


# Global connection manager instance
manager = ConnectionManager()
