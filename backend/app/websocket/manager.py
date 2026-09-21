import logging
from typing import Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger("app.websocket")

class ConnectionManager:
    """
    Manages active WebSocket connections.
    Supports single connection message, broadcast message, and group routing.
    """

    def __init__(self):
        # Maps active connections: websocket instance -> set of subscription topics
        self.active_connections: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a WebSocket connection and trace active connection pools."""
        await websocket.accept()
        self.active_connections[websocket] = set()
        logger.info(f"New WebSocket client connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Clean up connection pool when a client disconnects."""
        if websocket in self.active_connections:
            del self.active_connections[websocket]
            logger.info(f"WebSocket client disconnected: {websocket.client}")

    async def subscribe(self, websocket: WebSocket, topic: str) -> None:
        """Subscribe client socket connection to a specific event topic."""
        if websocket in self.active_connections:
            self.active_connections[websocket].add(topic)
            logger.debug(f"Client {websocket.client} subscribed to topic: {topic}")

    async def unsubscribe(self, websocket: WebSocket, topic: str) -> None:
        """Unsubscribe client socket connection from a specific event topic."""
        if websocket in self.active_connections and topic in self.active_connections[websocket]:
            self.active_connections[websocket].remove(topic)
            logger.debug(f"Client {websocket.client} unsubscribed from topic: {topic}")

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """Send a direct JSON message to a specific connection."""
        await websocket.send_json(message)

    async def broadcast(self, message: dict) -> None:
        """Broadcast a JSON message to all connected clients."""
        logger.debug(f"Broadcasting message to {len(self.active_connections)} clients")
        for connection in list(self.active_connections.keys()):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {str(e)}")
                self.disconnect(connection)

    async def broadcast_to_topic(self, topic: str, message: dict) -> None:
        """Broadcast a JSON message only to clients subscribed to a specific topic."""
        logger.debug(f"Broadcasting to topic {topic}")
        for connection, topics in list(self.active_connections.items()):
            if topic in topics:
                try:
                    await connection.send_json({"topic": topic, "data": message})
                except Exception as e:
                    logger.error(f"Error sending message to client on topic {topic}: {str(e)}")
                    self.disconnect(connection)

# Global singleton connection manager
ws_connection_manager = ConnectionManager()
