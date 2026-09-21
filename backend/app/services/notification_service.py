import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Notification
from app.websocket.manager import ws_connection_manager

class NotificationService:
    """
    NotificationService writes administrative alert signals to the database
    and streams them instantly to WebSocket clients.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_alert(
        self,
        org_id: uuid.UUID,
        title: str,
        message: str,
        alert_type: str  # e.g., 'worker_offline', 'queue_paused', 'job_failed', 'high_failure_rate'
    ) -> Notification:
        """Create and write an alert notification, then broadcast to all WS listeners."""
        notification = Notification(
            organization_id=org_id,
            title=title,
            message=message,
            type=alert_type,
            status="pending"
        )
        self.session.add(notification)
        await self.session.flush()

        # Build message payload for WebSocket
        payload = {
            "id": str(notification.id),
            "organization_id": str(org_id),
            "title": title,
            "message": message,
            "type": alert_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # Broadcast via WebSockets to subscribers of notifications topic
        await ws_connection_manager.broadcast_to_topic("notifications", payload)
        
        return notification
