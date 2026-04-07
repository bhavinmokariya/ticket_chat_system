from fastapi import APIRouter, WebSocket
from app.websocket.manager import NotificationManager
from app.utils.shared import notification_queue
# from app.db import get_collection

notify_rt = APIRouter(prefix="/notify")

# One manager instance shared across all connections on this router.
manager = NotificationManager()


@notify_rt.websocket("/live-tickets")
async def live(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    # listen() blocks until the client disconnects, then cleans up.
    await manager.listen(websocket)


@notify_rt.get('/')
async def temp():
    return "Hello User"

@notify_rt.post('/insert')
async def insert_mock_ticket():
    await notification_queue.put({'ticket':'ticketdata'})
