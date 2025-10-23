"""
Telegram bot integration for admin alerts and notifications.
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from telegram import Bot
from telegram.error import TelegramError
from pydantic import BaseModel
import os
from dotenv import dotenv_values

logger = logging.getLogger(__name__)

# Load configuration
config = dotenv_values("../.env")
TELEGRAM_BOT_TOKEN = config.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_CHAT_ID = config.get("TELEGRAM_ADMIN_CHAT_ID")


class NotificationConfig(BaseModel):
    """Configuration for notification settings."""
    enabled: bool = True
    high_severity_only: bool = True
    rate_limit_minutes: int = 5
    hostel_specific: bool = False
    admin_chat_ids: List[str] = []


class RateLimiter:
    """Simple rate limiter for notifications."""
    
    def __init__(self, max_requests: int = 10, time_window_minutes: int = 5):
        self.max_requests = max_requests
        self.time_window_minutes = time_window_minutes
        self.requests: List[datetime] = []
    
    def is_allowed(self) -> bool:
        """Check if a request is allowed based on rate limiting."""
        now = datetime.now(timezone.utc)
        
        # Remove old requests outside the time window
        cutoff = now.timestamp() - (self.time_window_minutes * 60)
        self.requests = [req for req in self.requests if req.timestamp() > cutoff]
        
        # Check if we're under the limit
        if len(self.requests) >= self.max_requests:
            return False
        
        # Add current request
        self.requests.append(now)
        return True


class TelegramNotifier:
    """Handles Telegram notifications for admin alerts."""
    
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.config = NotificationConfig()
        self.rate_limiter = RateLimiter()
        self._initialize_bot()
    
    def _initialize_bot(self):
        """Initialize the Telegram bot."""
        if not TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not configured. Telegram notifications disabled.")
            self.config.enabled = False
            return
        
        try:
            self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
            logger.info("Telegram bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            self.config.enabled = False
    
    async def send_complaint_alert(self, complaint_data: Dict[str, Any]) -> bool:
        """Send a complaint alert to admin chat."""
        if not self.config.enabled or not self.bot:
            logger.debug("Telegram notifications disabled or bot not initialized")
            return False
        
        if not self.rate_limiter.is_allowed():
            logger.warning("Rate limit exceeded for Telegram notifications")
            return False
        
        # Check if we should send this notification
        if not self._should_send_notification(complaint_data):
            return False
        
        try:
            message = self._format_complaint_message(complaint_data)
            chat_id = TELEGRAM_ADMIN_CHAT_ID or self.config.admin_chat_ids[0] if self.config.admin_chat_ids else None
            
            if not chat_id:
                logger.warning("No admin chat ID configured for Telegram notifications")
                return False
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Sent complaint alert to Telegram: {complaint_data.get('id', 'unknown')}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram notification: {e}")
            return False
    
    def _should_send_notification(self, complaint_data: Dict[str, Any]) -> bool:
        """Determine if a notification should be sent based on configuration."""
        if self.config.high_severity_only:
            severity = complaint_data.get('severity', '').lower()
            if severity not in ['high', 'critical']:
                return False
        
        return True
    
    def _format_complaint_message(self, complaint_data: Dict[str, Any]) -> str:
        """Format complaint data into a Telegram message."""
        complaint_id = complaint_data.get('id', 'Unknown')
        hostel = complaint_data.get('hostel', 'Unknown')
        category = complaint_data.get('category', 'Unknown')
        severity = complaint_data.get('severity', 'Unknown')
        description = complaint_data.get('description', 'No description')
        room_number = complaint_data.get('room_number', 'Unknown')
        
        # Truncate description if too long
        if len(description) > 200:
            description = description[:200] + "..."
        
        message = f"""
🚨 <b>New Complaint Alert</b>

<b>ID:</b> {complaint_id[:8]}...
<b>Hostel:</b> {hostel}
<b>Room:</b> {room_number}
<b>Category:</b> {category}
<b>Severity:</b> {severity.upper()}

<b>Description:</b>
{description}

<i>Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</i>
        """.strip()
        
        return message
    
    async def send_status_update_alert(self, complaint_id: str, old_status: str, new_status: str, updated_by: str) -> bool:
        """Send a status update alert."""
        if not self.config.enabled or not self.bot:
            return False
        
        if not self.rate_limiter.is_allowed():
            return False
        
        try:
            message = f"""
📝 <b>Complaint Status Updated</b>

<b>Complaint ID:</b> {complaint_id[:8]}...
<b>Status:</b> {old_status} → {new_status}
<b>Updated by:</b> {updated_by}

<i>Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</i>
            """.strip()
            
            chat_id = TELEGRAM_ADMIN_CHAT_ID or self.config.admin_chat_ids[0] if self.config.admin_chat_ids else None
            
            if chat_id:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='HTML'
                )
                return True
            
        except Exception as e:
            logger.error(f"Failed to send status update alert: {e}")
        
        return False
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update notification configuration."""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        logger.info(f"Updated notification config: {new_config}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current notification configuration."""
        return self.config.model_dump()


# Global notifier instance
telegram_notifier = TelegramNotifier()
