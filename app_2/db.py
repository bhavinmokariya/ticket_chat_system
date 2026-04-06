import logging
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError
from fastapi import HTTPException
from app_2.conf import settings

logger = logging.getLogger(__name__)


class DbManager:
    __slots__ = ("client", "db")

    def __init__(self) -> None:
        self.client: AsyncMongoClient | None = None
        self.db = None


db_manager = DbManager()


async def connect_to_mongo() -> None:
    try:
        db_manager.client = AsyncMongoClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=5_000,
            uuidRepresentation="standard",
            # Connection-pool tuning: keep a small pool ready, allow bursts
            minPoolSize=2,
            maxPoolSize=20,
            waitQueueTimeoutMS=3_000,
        )
        db_manager.db = db_manager.client["app"]
        await db_manager.client.admin.command("ping")
        logger.info("Connected to MongoDB successfully.")
    except Exception as exc:
        logger.exception("MongoDB connection failed: %s", exc)
        raise


async def disconnect_from_mongo() -> None:
    if db_manager.client is not None:
        await db_manager.client.close()
        logger.info("MongoDB connection closed.")


def get_db():
    """FastAPI dependency — yields the database handle."""
    if db_manager.db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        yield db_manager.db
    except PyMongoError as exc:
        logger.error("MongoDB error: %s", exc)
        raise HTTPException(status_code=500, detail="Database error") from exc


def get_collection():
    """Direct (non-dependency) access to the tickets collection."""
    if db_manager.db is None:
        raise RuntimeError("Database not initialised")
    return db_manager.db[settings.collection]
