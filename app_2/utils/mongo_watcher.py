import logging
import asyncio
from app_2.db import get_collection
from app_2.utils.shared import notification_queue

logger = logging.getLogger(__name__)

# Only pull back the fields we actually need from change-stream events.
_PROJECTION = {
    "_id": 1,
    "operationType": 1,
    "fullDocument": 1,
    "documentKey": 1,
    "updateDescription.updatedFields.assigned_engineer_id": 1,
}

_PIPELINE = [
    {
        "$match": {
            "$or": [
                {"operationType": "insert"},
                {
                    "operationType": "update",
                    "updateDescription.updatedFields.assigned_engineer_id": {
                        "$exists": True
                    },
                },
            ]
        }
    },
    # Strip everything the consumer doesn't need before the event leaves the server.
    {"$project": _PROJECTION},
]


async def watcher() -> None:
    """
    Tail the MongoDB change stream and enqueue events for broadcasting.

    Reconnects automatically on transient errors so a momentary network
    blip doesn't kill the whole stream.
    """
    collection = get_collection()

    while True:
        try:
            async with await collection.watch(
                _PIPELINE,
                full_document="updateLookup",   # gives fullDocument on updates too
                max_await_time_ms=1_000,        # heartbeat — keeps the cursor alive
            ) as stream:
                logger.info("Change-stream watch started.")
                async for event in stream:
                    op = event["operationType"]
                    if op == "insert":
                        doc: dict = event["fullDocument"]
                        # Serialise ObjectId once here, not in every broadcast path.
                        doc["_id"] = str(doc["_id"])
                        await notification_queue.put(doc)
                    elif op == "update":
                        await notification_queue.put(str(event["documentKey"]))
        except asyncio.CancelledError:
            logger.info("Watcher cancelled — shutting down.")
            return
        except Exception as exc:
            logger.exception("Change-stream error, reconnecting in 2 s: %s", exc)
            await asyncio.sleep(2)
