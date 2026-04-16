import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timezone, timedelta
from app.config.db import connect_to_mongo, close_mongo_connection, get_database
from app.routes import auth_routes, ticket_routes, message_routes
from app.websocket.websocket_routes import router as websocket_router, notification_manager, manager
from app.services.ticket_service import start_auto_resolve_loop
from app.utils.shared import notification_queue
from app.config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

POLL_INTERVAL = 1  # seconds


async def _poll_ticket_changes():
    """
    Poll MongoDB every 2s for new customer messages and broadcast them to
    connected engineers via WebSocket.

    Fix: We track the message count per ticket from the moment we FIRST see it
    in the poll window. On first encounter we store the current count so that
    the NEXT poll cycle can detect truly new messages. This avoids the race
    where initializing prev_count = len(messages) on first sight causes us to
    miss messages that arrived in that same poll window.

    ticket_created notifications are handled directly in ticket_service.py
    to avoid double-notification.
    """
    db = get_database()
    # ticket_id -> last known message count
    ticket_msg_counts: dict[int, int] = {}
    # ticket_id -> timestamp when we first registered this ticket in our tracker
    ticket_first_seen: dict[int, datetime] = {}

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        try:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=POLL_INTERVAL + 1)

            async for ticket in db.tickets.find(
                {"last_message_at": {"$gt": window_start}},
                {"ticket_id": 1, "messages": 1, "last_message_at": 1},
            ):
                tid = ticket["ticket_id"]
                messages = ticket.get("messages", [])
                current_count = len(messages)

                if tid not in ticket_msg_counts:
                    # First time we see this ticket — record count now, broadcast
                    # on next cycle (avoids replaying old messages on startup).
                    ticket_msg_counts[tid] = current_count
                    ticket_first_seen[tid] = now
                    continue

                prev_count = ticket_msg_counts[tid]
                if current_count > prev_count:
                    new_msgs = messages[prev_count:]
                    for msg in new_msgs:
                        if msg.get("sender_type") == "customer":
                            await manager.broadcast(tid, jsonable_encoder(msg))
                            logger.debug("Broadcast new customer msg to engineers on ticket %s", tid)
                    ticket_msg_counts[tid] = current_count

        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.warning("Poll error: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    notification_manager.start()
    auto_resolve_task = asyncio.create_task(start_auto_resolve_loop())
    poll_task = asyncio.create_task(_poll_ticket_changes())
    logger.info("Admin-support backend started.")
    try:
        yield
    finally:
        auto_resolve_task.cancel()
        poll_task.cancel()
        for t in [auto_resolve_task, poll_task]:
            try: await t
            except asyncio.CancelledError: pass
        notification_manager.stop()
        await close_mongo_connection()


app = FastAPI(title="Ticket Support — Admin & Support API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # Local dev origins — add your deployed URLs here when going to production
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(ticket_routes.router)
app.include_router(message_routes.router)
app.include_router(websocket_router)

@app.get("/", tags=["Health"])
async def root():
    return {"message": "Admin/Support API is running.", "docs": "/docs"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
