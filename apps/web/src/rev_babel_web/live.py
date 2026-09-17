"""Slide Sync Lite: in-memory live-slide-position state and its SSE feed.

One live session at a time, held in this process's memory and mirrored to
a JSON file so a restart mid-lesson recovers. This only works with a
single uvicorn worker — the set of open SSE connections lives here, in
process memory; a second worker would silently split students across two
independent states. See docs/decisions/0014-slide-sync-lite.md.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

STATE_PATH = Path(os.environ.get("DATA_DIR", "data")) / "live_state.json"

_DEFAULT_STATE: dict[str, Any] = {
    "file_id": None,
    "title": "",
    "slide_count": 0,
    "index": 1,
    "status": "ended",
    "revision": 0,
}

_FILE_ID_RE = re.compile(r"/d/([a-zA-Z0-9_-]+)")


def _load() -> dict[str, Any]:
    if STATE_PATH.exists():
        try:
            return {**_DEFAULT_STATE, **json.loads(STATE_PATH.read_text())}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULT_STATE)


_state: dict[str, Any] = _load()
_subscribers: set[asyncio.Queue] = set()


def _save() -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(_state))


def _commit(**changes: Any) -> dict[str, Any]:
    _state.update(changes)
    _state["revision"] += 1
    _save()
    snapshot = dict(_state)
    for queue in _subscribers:
        queue.put_nowait(snapshot)
    return snapshot


def get_state() -> dict[str, Any]:
    return dict(_state)


def subscriber_count() -> int:
    return len(_subscribers)


def extract_file_id(raw: str) -> str:
    raw = raw.strip()
    match = _FILE_ID_RE.search(raw)
    return match.group(1) if match else raw


def start(file_id_or_url: str, title: str, slide_count: int) -> dict[str, Any]:
    file_id = extract_file_id(file_id_or_url)
    slide_count = max(1, int(slide_count))
    return _commit(
        file_id=file_id,
        title=title.strip(),
        slide_count=slide_count,
        index=1,
        status="live",
    )


def goto(index: int) -> dict[str, Any]:
    if _state["slide_count"] <= 0:
        return get_state()
    clamped = max(1, min(int(index), _state["slide_count"]))
    if clamped == _state["index"]:
        return get_state()
    return _commit(index=clamped)


def set_status(status: str) -> dict[str, Any]:
    if status not in ("live", "blank"):
        raise ValueError("status must be 'live' or 'blank'")
    return _commit(status=status)


def end() -> dict[str, Any]:
    return _commit(status="ended")


async def sse_events() -> AsyncIterator[str]:
    """One SSE connection's event text, from connect until the client drops."""
    queue: asyncio.Queue = asyncio.Queue()
    queue.put_nowait(get_state())
    _subscribers.add(queue)
    try:
        yield "retry: 3000\n\n"
        while True:
            try:
                snapshot = await asyncio.wait_for(queue.get(), timeout=15)
                yield f"event: state\ndata: {json.dumps(snapshot)}\n\n"
            except TimeoutError:
                yield ": hb\n\n"
    finally:
        _subscribers.discard(queue)
