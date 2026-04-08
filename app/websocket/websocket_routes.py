from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from app.websocket.manager import ConnectionManager
from app.message_service import add_message, get_messages
from datetime import datetime

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/{ticket_id}")
async def websocket_endpoint(websocket: WebSocket, ticket_id: int):
    # 1. Register the connection
    await manager.connect(ticket_id, websocket)

    # 2. Immediately push previous chat history to the chat
    history = await get_messages(ticket_id)
    await manager.send_history(websocket, history)

    try:
        while True:
            # 3. Wait for an incoming message
            data = await websocket.receive_json()

            message = {
                "message_id": data.get("message_id"),
                "sender_id": data.get("sender_id"),
                "sender_type": data.get("sender_type"),
                "message": data.get("message"),
                "message_type": data.get("message_type", "text"),
                "file_url": data.get("file_url", ""),
                "timestamp": datetime.utcnow()
            }

            # 4. add message to DB
            await add_message(ticket_id, message)

            # 5. Broadcast to all chat
            await manager.broadcast(ticket_id, message)

    except WebSocketDisconnect:
        manager.disconnect(ticket_id, websocket)