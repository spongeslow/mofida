"""Tool-signal processor (Phase G).

Turns inbound ``tool_signals`` rows (written by the Composio webhook / poll) into
the existing update pipeline: route the signal's tool to its axes via
``axes_for_tool``, compute the transitive re-run set with ``affected_axes``, log
an ``events`` row (source=``tool``) + ``event_new`` SSE, and mark the signal
processed. This finally makes ``tool_signals`` a live part of the system and
reuses the Event Feed / dependency machinery rather than inventing a new path.
"""
from __future__ import annotations

import json
import logging

from .axis_registry import axes_for_tool
from .dependency import affected_axes
from .state_router import get_pool
from .updates.pipeline import apply_update

logger = logging.getLogger("moufida.signals")


def _parse(val):
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {}
    return val if val is not None else {}


def _summarise(tool_slug: str, signal_type: str, payload: dict) -> str:
    """Human-readable one-liner for the Event Feed."""
    label = tool_slug.replace("composio_", "").replace("_", " ").title()
    detail = (
        payload.get("title")
        or payload.get("text")
        or payload.get("message")
        or payload.get("name")
        or signal_type
    )
    return f"{label}: {str(detail)[:140]}"


async def process_signal_row(pool, row) -> None:
    """Process one tool_signals row: route → event + SSE → mark processed."""
    project_id = str(row["project_id"])
    tool_slug = row["tool_slug"]
    signal_type = row["signal_type"]
    payload = _parse(row["payload"])

    axes = axes_for_tool(tool_slug)
    downstream = affected_axes(set(axes)) if axes else []
    summary = _summarise(tool_slug, signal_type, payload)

    try:
        await apply_update(
            pool, project_id,
            changed_axes=axes,
            summary=summary,
            source="tool",
            severity="info",
            event_type=f"{tool_slug}:{signal_type}",
            diff={"signal": payload},
            suggestion={
                "action": "rerun_axes",
                "axes": downstream,
                "description": f"Changement externe ({tool_slug}) — les axes liés peuvent nécessiter une mise à jour",
            },
            auto_persist=False,
        )
    except Exception as exc:
        logger.warning("apply_update failed for signal %s: %s", row["id"], exc)
        return

    await pool.execute(
        "UPDATE tool_signals SET processed = TRUE WHERE id = $1::uuid", row["id"]
    )
    logger.info("processed tool_signal %s (%s/%s) → axes=%s", row["id"], tool_slug, signal_type, axes)


async def process_signal_id(signal_id: str) -> None:
    """Process a single signal by id (used inline right after insert)."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """SELECT id, project_id, tool_slug, signal_type, payload
             FROM tool_signals WHERE id = $1::uuid AND processed = FALSE""",
        signal_id,
    )
    if row is not None:
        await process_signal_row(pool, row)


async def drain_unprocessed(limit: int = 100) -> int:
    """Process any unprocessed signals (startup catch-up / safety net)."""
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT id, project_id, tool_slug, signal_type, payload
             FROM tool_signals WHERE processed = FALSE
            ORDER BY created_at ASC LIMIT $1""",
        limit,
    )
    for row in rows:
        try:
            await process_signal_row(pool, row)
        except Exception as exc:
            logger.warning("drain: signal %s failed: %s", row["id"], exc)
    return len(rows)
