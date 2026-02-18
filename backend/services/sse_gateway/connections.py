"""SSE connection manager — maintains per-user event queues."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages SSE connections per user.

    Each user_id maps to a set of asyncio.Queue instances — one per connected client.
    When an event arrives for a user, it's broadcast to all their queues.
    """

    def __init__(self):
        self._connections: dict[str, set[asyncio.Queue]] = defaultdict(set)

    def connect(self, user_id: str) -> asyncio.Queue:
        """Register a new SSE connection for a user. Returns a queue to read events from."""
        queue: asyncio.Queue = asyncio.Queue()
        self._connections[user_id].add(queue)
        logger.info("SSE client connected", extra={"user_id": user_id, "total": len(self._connections[user_id])})
        return queue

    def disconnect(self, user_id: str, queue: asyncio.Queue) -> None:
        """Remove an SSE connection for a user."""
        self._connections[user_id].discard(queue)
        if not self._connections[user_id]:
            del self._connections[user_id]
        logger.info("SSE client disconnected", extra={"user_id": user_id})

    async def broadcast(self, user_id: str, event: dict) -> None:
        """Send an event to all connected clients for a user."""
        queues = self._connections.get(user_id, set())
        if not queues:
            return
        for queue in queues.copy():
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("SSE queue full, dropping event", extra={"user_id": user_id})

    @property
    def connection_count(self) -> int:
        return sum(len(qs) for qs in self._connections.values())

    @property
    def user_count(self) -> int:
        return len(self._connections)
