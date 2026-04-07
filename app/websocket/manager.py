import asyncio
import json
import logging
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
from app.utils.shared import notification_queue

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Manages all active WebSocket connections and fans out messages from
    the shared notification queue to every connected client.

    Key optimisations vs. the original:
    - A single background broadcaster loop replaces per-socket loops,
      so queue.get() is called exactly once per event regardless of how
      many clients are connected.
    - Disconnected sockets are pruned without raising an exception that
      could abort the whole broadcast.
    - json.dumps is called once per event, not once per client.
    - asyncio.gather broadcasts to all clients concurrently instead of
      serially, cutting total send time from O(n) sequential to ~O(1).
    """

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self._broadcaster_task: asyncio.Task | None = None

    def start(self) -> None:
        """Spawn the single shared broadcaster. Call once at startup."""
        if self._broadcaster_task is None or self._broadcaster_task.done():
            self._broadcaster_task = asyncio.create_task(
                self._broadcaster(), name="ws-broadcaster"
            )

    def stop(self) -> None:
        """Cancel the broadcaster. Call on shutdown."""
        if self._broadcaster_task and not self._broadcaster_task.done():
            self._broadcaster_task.cancel()


    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.debug("WebSocket connected. Total: %d", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.debug("WebSocket disconnected. Total: %d", len(self.active_connections))


    async def listen(self, websocket: WebSocket) -> None:
        """
        Keep the connection alive and handle client-initiated closes.
        The actual broadcasting is done by the shared _broadcaster task.
        """
        try:
            while True:
                # Drain any incoming frames (pings, close frames, etc.)
                await websocket.receive_text()
        except WebSocketDisconnect:
            await self.disconnect(websocket)

    async def _broadcaster(self) -> None:
        """
        Single coroutine that drains the queue and fans out to all clients.
        One queue.get() per event, one json.dumps per event.
        """
        while True:
            try:
                message = await notification_queue.get()
                notification_queue.task_done()

                if not self.active_connections:
                    continue

                payload = json.dumps(message)

                # Send to all clients concurrently; ignore individual failures.
                results = await asyncio.gather(
                    *[ws.send_text(payload) for ws in list(self.active_connections)],
                    return_exceptions=True,
                )

                # Prune any sockets that errored during send.
                for ws, result in zip(list(self.active_connections), results):
                    if isinstance(result, Exception):
                        logger.debug("Pruning failed WebSocket: %s", result)
                        await self.disconnect(ws)

            except asyncio.CancelledError:
                logger.info("Broadcaster task cancelled.")
                return
            except Exception as exc:
                logger.exception("Unexpected broadcaster error: %s", exc)
