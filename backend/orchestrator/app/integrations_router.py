"""Composio inbound integrations (Phase G).

Two ingress paths land here, both funnelling into ``tool_signals`` + the signal
processor:
  - ``POST /integrations/webhook`` — hosted/tunnelled Composio triggers (verified
    by a shared secret).
  - ``POST /integrations/poll`` — the desktop fallback: the Go daemon calls this
    on a cadence so a NAT'd machine with no public ingress still receives
    triggers (the orchestrator pulls them from Composio and ingests them).

Both dedupe by Composio event id (stored as ``payload._event_id``) so a retried
delivery never drives a double re-run.
"""
from __future__ import annotations

import asyncio
import hmac
import json
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request

from . import signals
from .state_router import get_pool

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = logging.getLogger("moufida.integrations")

WEBHOOK_SECRET = os.getenv("COMPOSIO_WEBHOOK_SECRET", "")


def _composio():
    from toolkit.tools.composio import client as composio
    return composio


async def _resolve_project(pool) -> str | None:
    """Single-user desktop: route inbound signals to the daemon's focused
    project, falling back to the most recently updated project."""
    try:
        focused = await pool.fetchval(
            "SELECT focus_project_id FROM daemon_control WHERE id = TRUE"
        )
    except Exception:
        focused = None
    if focused:
        return str(focused)
    recent = await pool.fetchval(
        "SELECT id FROM profiles WHERE archived = false ORDER BY updated_at DESC LIMIT 1"
    )
    return str(recent) if recent else None


async def _already_seen(pool, event_id: str) -> bool:
    if not event_id:
        return False
    found = await pool.fetchval(
        "SELECT 1 FROM tool_signals WHERE payload->>'_event_id' = $1 LIMIT 1",
        event_id,
    )
    return found is not None


async def _ingest_event(pool, app: str, trigger_name: str, event_id: str, payload: dict) -> bool:
    """Insert a tool_signals row for one trigger event and process it. Returns
    False if it was a duplicate / unroutable."""
    composio = _composio()
    tool_slug = composio.slug_for_app(app) or (app or "").lower()
    if await _already_seen(pool, event_id):
        return False
    project_id = await _resolve_project(pool)
    if project_id is None:
        logger.info("no project to attribute %s/%s — dropping", app, trigger_name)
        return False

    stored_payload = {**payload, "_event_id": event_id, "_app": app}
    signal_id = await pool.fetchval(
        """
        INSERT INTO tool_signals (project_id, tool_slug, signal_type, payload, processed)
        VALUES ($1::uuid, $2, $3, $4::jsonb, FALSE)
        RETURNING id
        """,
        project_id, tool_slug, trigger_name or "trigger", json.dumps(stored_payload),
    )
    # Process out-of-band so we ack the webhook quickly.
    asyncio.create_task(signals.process_signal_id(str(signal_id)))
    return True


@router.post("/webhook")
async def composio_webhook(
    request: Request,
    x_composio_secret: str | None = Header(default=None),
    x_composio_signature: str | None = Header(default=None),
):
    """Receive a Composio trigger. Verifies the shared secret before any write."""
    # Signature verification is mandatory before any write — untrusted input
    # otherwise drives axis re-runs. With no secret configured we cannot verify,
    # so we refuse the webhook entirely (the desktop default uses /poll instead).
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="webhook disabled: COMPOSIO_WEBHOOK_SECRET unset")
    provided = x_composio_secret or x_composio_signature or ""
    if not hmac.compare_digest(provided, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="invalid webhook signature")

    raw = await request.body()
    try:
        body = json.loads(raw or b"{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid JSON")

    # Composio nests the trigger payload under varying keys across versions.
    data = body.get("data") or body.get("payload") or body
    app = body.get("appName") or body.get("app") or data.get("appName") or data.get("app") or ""
    trigger_name = body.get("triggerName") or body.get("trigger") or data.get("triggerName") or ""
    event_id = str(body.get("id") or body.get("eventId") or data.get("id") or "")

    pool = await get_pool()
    ingested = await _ingest_event(pool, app, trigger_name, event_id, data)
    return {"ok": True, "ingested": ingested}


@router.post("/poll")
async def composio_poll():
    """Desktop fallback: pull recent trigger events from Composio and ingest them.

    Called by the Go daemon on a cadence (no secret needed — the orchestrator
    holds the API key). Safe to call when Composio is unconfigured (returns 0).
    """
    composio = _composio()
    if not composio.is_available():
        return {"ok": True, "ingested": 0, "composio": "unavailable"}

    events = composio.fetch_recent_trigger_events()
    pool = await get_pool()
    ingested = 0
    for ev in events:
        try:
            if await _ingest_event(pool, ev.get("app", ""), ev.get("trigger_name", ""),
                                   ev.get("event_id", ""), ev.get("payload", {})):
                ingested += 1
        except Exception as exc:
            logger.warning("poll ingest failed: %s", exc)
    return {"ok": True, "ingested": ingested, "fetched": len(events)}
