import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.websocket.routes import manager, notify_rt
# from fastapi.staticfiles import StaticFiles
# from app.db import connect_to_mongo, disconnect_from_mongo
# from app.utils.mongo_watcher import watcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── startup ──────────────────────────────────────────────────────────
    # await connect_to_mongo()

    # Start the change-stream watcher as a background task.
    # watcher_task = asyncio.create_task(watcher(), name="mongo-watcher")

    # Start the single shared WebSocket broadcaster.
    manager.start()

    try:
        yield
    finally:
        # ── shutdown ─────────────────────────────────────────────────────
        manager.stop()
        # watcher_task.cancel()
        # Give the tasks a moment to finish cleanly.
        # await asyncio.gather(watcher_task, return_exceptions=True)
        # await disconnect_from_mongo()


app = FastAPI(lifespan=lifespan)
app.include_router(notify_rt)
# app.mount("/", StaticFiles(directory="app_2/Frontend", html=True), name="frontend")
