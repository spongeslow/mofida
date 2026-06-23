"""In-memory Server-Sent Events broker, keyed by project id.

Phase-2 scope: a process-local fan-out good enough to push live events to a
connected client. Events fired with no active subscriber are dropped -- the
authoritative result is always available from the REST endpoints.

Frame format on the wire::

    data: {"event": "<type>", "payload": {...}}\\n\\n

``push_event`` is the single entry point used by the diagnostic runner and the
metric_update handlers; ``event_stream`` backs the SSE endpoint in main.py.
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import AsyncGenerator

# Recognised event types (documentation / validation aid).
EVENT_TYPES = frozenset(
    {
        "score_update", "alert", "roadmap_update", "review_ready", "maturity_update",
        "event_new", "daemon_status", "competitor_update", "opportunity_new",
        "watch_targets_updated", "concept_update",
    }
)

_registry: dict[str, set[asyncio.Queue]] = defaultdict(set)


async def push_event(project_id: str, event: str, payload: dict) -> None:
    """Broadcast an event to every subscriber of ``project_id``."""
    frame = {"event": event, "payload": payload}
    for queue in list(_registry.get(project_id, ())):
        await queue.put(frame)


async def broadcast_event(event: str, payload: dict) -> None:
    """Fan an event to *every* connected project channel.

    Used for events that aren't project-scoped (e.g. ``daemon_status`` — the
    companion window subscribes via whatever project it currently watches, and
    multiple windows may be open). Iterates a snapshot of the registry so a
    disconnect mid-broadcast can't mutate the set under us.
    """
    frame = {"event": event, "payload": payload}
    for queues in [set(qs) for qs in _registry.values()]:
        for queue in queues:
            await queue.put(frame)


async def event_stream(project_id: str) -> AsyncGenerator[str, None]:
    """Yield SSE frames for ``project_id`` until the client disconnects."""
    queue: asyncio.Queue = asyncio.Queue()
    _registry[project_id].add(queue)
    try:
        while True:
            frame = await queue.get()
            yield f"data: {json.dumps(frame)}\n\n"
    finally:
        _registry[project_id].discard(queue)
        if not _registry[project_id]:
            _registry.pop(project_id, None)
