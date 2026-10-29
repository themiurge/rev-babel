"""Class chat: an in-memory message log and its SSE feed.

Messages live only in this process's memory and expire 24 hours after they
are sent; nothing is written to disk, and a restart empties the log. Like
live.py this needs a single uvicorn worker, since the open SSE connections
and the log are process state. See docs/decisions/0017-class-chat.md.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from collections.abc import AsyncIterator
from typing import Any

MAX_TEXT_LENGTH = 500
MAX_MESSAGES = 500
TTL_SECONDS = 24 * 60 * 60

_messages: deque[dict[str, Any]] = deque(maxlen=MAX_MESSAGES)
_subscribers: set[asyncio.Queue] = set()
_next_id = 1


def _prune(now: float) -> None:
    while _messages and now - _messages[0]["ts"] > TTL_SECONDS:
        _messages.popleft()


def clean_text(raw: str) -> str | None:
    text = " ".join(raw.split())
    if not text or len(text) > MAX_TEXT_LENGTH or not text.isprintable():
        return None
    return text


def history() -> list[dict[str, Any]]:
    _prune(time.time())
    return list(_messages)


def post(name: str, text: str) -> dict[str, Any]:
    global _next_id
    now = time.time()
    _prune(now)
    message = {"id": _next_id, "name": name, "text": text, "ts": now}
    _next_id += 1
    _messages.append(message)
    for queue in _subscribers:
        queue.put_nowait(message)
    return message


def clear() -> None:
    _messages.clear()


async def sse_events() -> AsyncIterator[str]:
    """One SSE connection: the whole log on connect, then each new message."""
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.add(queue)
    try:
        yield "retry: 3000\n\n"
        yield f"event: history\ndata: {json.dumps(history())}\n\n"
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=15)
                yield f"event: message\ndata: {json.dumps(message)}\n\n"
            except TimeoutError:
                yield ": hb\n\n"
    finally:
        _subscribers.discard(queue)
