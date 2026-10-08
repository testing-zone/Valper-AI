"""In-process pub/sub so the UI gets live updates over Server-Sent Events."""
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

_subscribers: set = set()


def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.add(q)
    return q


def unsubscribe(q: asyncio.Queue):
    _subscribers.discard(q)


def publish(event_type: str, payload: dict):
    message = f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
    for q in list(_subscribers):
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            logger.warning("Dropping event for slow subscriber")
