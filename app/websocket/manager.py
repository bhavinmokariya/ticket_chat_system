from typing import Dict, List
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder


class ConnectionManager:
    def __init__(self):
        # list of connected WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, ticket_id: int, websocket: WebSocket):
        """Accept the socket and register it under the ticket."""
        await websocket.accept()
        if ticket_id not in self.active_connections:
            self.active_connections[ticket_id] = []
        self.active_connections[ticket_id].append(websocket)

    def disconnect(self, ticket_id: int, websocket: WebSocket):
        """Remove socket from the ticket room. Clean up empty chat."""
        if ticket_id in self.active_connections:
            try:
                self.active_connections[ticket_id].remove(websocket)
            except ValueError:
                pass
            # Clean up the key when the room is empty
            if not self.active_connections[ticket_id]:
                del self.active_connections[ticket_id]

    async def send_history(self, websocket: WebSocket, messages: list):
        """Push the full chat history to chat"""
        await websocket.send_json({
            "type": "history",
            "messages": jsonable_encoder(messages)
        })

    async def broadcast(self, ticket_id: int, message: dict):
        """Send a new message to every client in the ticket room."""
        payload = {
            "type": "message",
            "message": jsonable_encoder(message)
        }
        if ticket_id in self.active_connections:
            dead = []
            for connection in self.active_connections[ticket_id]:
                try:
                    await connection.send_json(payload)
                except Exception:
                    dead.append(connection)
            # Remove any sockets that errored during send
            for d in dead:
                self.disconnect(ticket_id, d)