"""Async Redis consumer: routes daemon metric events to axis metric_update endpoints.

Runs as a background task wired into the FastAPI lifespan. On each message
published to ``REDIS_METRICS_CHANNEL``, it fans out to the axis services listed
in ``axis_registry.METRIC_ROUTES``. Network errors from individual axes are
logged and swallowed — they never crash the consumer loop.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os

import httpx
import redis.asyncio as aioredis

from .axis_registry import METRIC_ROUTES, axis_host

logger = logging.getLogger("moufida.redis_consumer")

try:
    from toolkit import ToolManager as _ToolManager
    _tool_manager = _ToolManager()
except ImportError:
    _tool_manager = None

REDIS_URL = os.environ["REDIS_URL"]
REDIS_CHANNEL = os.environ["REDIS_METRICS_CHANNEL"]

_OLLAMA_BASE  = os.environ.get("OLLAMA_BASE_URL",  "http://ollama:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", os.environ.get("OLLAMA_MODEL", "llama3.1:8b"))


async def _handle_significant_change(data: dict) -> None:
    """Interpret a daemon 'significant_change' event, write events row, push SSE."""
    from .state_router import get_pool
    from .updates.pipeline import apply_update, interpret_daemon_event

    project_id = data.get("project_id")
    if not project_id:
        # Broadcast to all active projects — handle only if a project is specified.
        logger.debug("significant_change without project_id — skipping targeted event")
        return

    event_text = data.get("text", data.get("description", ""))
    sector     = data.get("sector", "cross-sector")
    language   = data.get("language", "fr")

    pool = await get_pool()
    interpreted = await interpret_daemon_event(
        _OLLAMA_BASE, _OLLAMA_MODEL, event_text, sector, language,
    )

    await apply_update(
        pool, project_id,
        changed_axes=interpreted.get("changed_axes", []),
        summary=interpreted.get("summary", event_text[:200]),
        source="daemon",
        severity=interpreted.get("severity", "info"),
        suggestion=interpreted.get("suggestion", {}),
        event_type="significant_change",
        auto_persist=False,
    )
    logger.info("significant_change event logged for project=%s", project_id)


# Human-readable summary + severity per daemon metric type (Phase F4 digest).
def _summarise_signal(metric_type: str, value: dict) -> tuple[str, str]:
    """Return (summary, severity) for a daemon metric, for the persisted event."""
    v = value if isinstance(value, dict) else {}
    if metric_type == "trend":
        kw = v.get("keyword", "?")
        pct = v.get("change_pct", 0)
        direction = v.get("direction", "")
        sev = "warning" if abs(float(pct or 0)) >= 100 else "info"
        return f"Tendance « {kw} » {direction} {abs(float(pct or 0)):.0f}%", sev
    if metric_type == "legal":
        return f"Veille réglementaire : {v.get('title', v.get('source', 'mise à jour'))}", "warning"
    if metric_type == "budget":
        return f"Signal budget : {v.get('message', v.get('title', 'variation détectée'))}", "warning"
    if metric_type == "milestone":
        return f"Jalon : {v.get('message', v.get('title', 'échéance proche'))}", "info"
    return f"Signal {metric_type}", "info"


async def _persist_daemon_signal(metric_type: str, data: dict) -> None:
    """Write a routed daemon metric as an events row so it survives transiently
    and feeds the WhatsNew/EventFeed digest (Phase F4)."""
    project_id = data.get("project_id")
    if not project_id:
        return
    from .state_router import get_pool
    from .updates.pipeline import apply_update

    summary, severity = _summarise_signal(metric_type, data.get("value", {}))
    axes = METRIC_ROUTES.get(metric_type, [])
    pool = await get_pool()
    try:
        await apply_update(
            pool, project_id,
            changed_axes=axes,
            summary=summary,
            source="daemon",
            severity=severity,
            event_type=metric_type,
            diff={"signal": data.get("value", {})},
            auto_persist=False,
        )
    except Exception as exc:
        logger.warning("persist daemon signal failed (%s): %s", metric_type, exc)

    # Mirror to the observability daemon-activity log (Phase H, best-effort).
    try:
        from . import telemetry
        await telemetry.record_daemon_activity(
            project_id=project_id, watcher=metric_type, activity="signal",
            detail={"summary": summary, "severity": severity, "value": data.get("value", {})},
        )
    except Exception:  # noqa: BLE001
        pass


async def consume() -> None:
    """Subscribe to the metrics channel and fan out to axis metric_update endpoints.

    Also handles the 'significant_change' message type emitted by the Go daemon
    when it detects an externally significant event (regulatory change, competitor
    move, market news). These are interpreted by the LLM and written to events.
    """
    client = aioredis.from_url(REDIS_URL)
    pubsub = client.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL)
    logger.info("Redis consumer started, listening on channel '%s'", REDIS_CHANNEL)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        try:
            data = json.loads(message["data"])
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Unparseable Redis message: %s", exc)
            continue

        metric_type = data.get("type")
        project_id = data.get("project_id")

        # Daemon significant-change events bypass axis routing.
        if metric_type == "significant_change":
            try:
                await _handle_significant_change(data)
            except Exception as exc:
                logger.warning("significant_change handling failed: %s", exc)
            continue

        target_slugs: list[str] = METRIC_ROUTES.get(metric_type, [])
        if not target_slugs:
            logger.debug("No route for metric type %r — ignoring", metric_type)
            continue

        # Phase F4: persist the signal as an event so it survives + feeds the digest.
        try:
            await _persist_daemon_signal(metric_type, data)
        except Exception as exc:
            logger.warning("daemon signal persist error: %s", exc)

        async with httpx.AsyncClient(timeout=10.0) as http:
            for slug in target_slugs:
                url = f"{axis_host(slug)}/metric_update"
                try:
                    resp = await http.post(url, json=data)
                    logger.info(
                        "metric_update %s -> %s: HTTP %d",
                        metric_type,
                        slug,
                        resp.status_code,
                    )
                    # Fan alert to push tools (e.g. Slack) when the axis confirms severity.
                    if _tool_manager is not None and project_id and resp.status_code == 200:
                        try:
                            body = resp.json()
                        except Exception:
                            body = {}
                        alert = body.get("alert")
                        if alert:
                            from .state_router import get_pool
                            pool = await get_pool()
                            await _tool_manager.dispatch_alert(pool, project_id, alert)
                except httpx.HTTPError as exc:
                    logger.warning(
                        "metric_update failed for %s (%s): %s",
                        slug,
                        metric_type,
                        exc,
                    )
