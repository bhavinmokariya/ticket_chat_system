import asyncio

# Single shared queue consumed by the notification broadcaster.
# maxsize=0  → unbounded (keeps existing behaviour).
# Increase maxsize and add a dead-letter strategy if back-pressure is needed.
notification_queue: asyncio.Queue[dict | str] = asyncio.Queue()
