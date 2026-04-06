from fastapi import APIRouter, WebSocket
from app_2.websocket.services.notification_manager import NotificationManager
from app_2.db import get_collection

notify_rt = APIRouter(prefix="/notify")

# One manager instance shared across all connections on this router.
manager = NotificationManager()


@notify_rt.websocket("/live-tickets")
async def live(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    # listen() blocks until the client disconnects, then cleans up.
    await manager.listen(websocket)


# ---------------------------------------------------------------------------
# Dev/test helper — remove or gate behind an env flag in production.
# ---------------------------------------------------------------------------
@notify_rt.get("/insert")
async def insert() -> dict:
    collection = get_collection()
    result = await collection.insert_one({"name": "deval"})
    return {"inserted_id": str(result.inserted_id)}
