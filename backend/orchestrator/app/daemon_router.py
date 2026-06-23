"""Daemon control plane — pause flag, heartbeat, and project focus.

The Go daemon polls ``GET /daemon/control`` for both the pause flag and which
project to watch (``focus_project_id``), and POSTs ``/daemon/heartbeat`` on a
short cadence so the UI can tell "paused" apart from "offline". The companion
character reflects ``daemon_status`` (broadcast over SSE) as watching/sleeping.

All state lives in the single-row ``daemon_control`` table (013 migration).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import asyncpg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import sse
from .state_router import get_pool

router = APIRouter()

# Liveness window: the daemon heartbeats every ~30s; treat it as alive if we've
# heard from it within 90s (tolerates a couple of missed beats).
_ALIVE_WINDOW = timedelta(seconds=90)


def _is_alive(last_beat: datetime | None) -> bool:
    if last_beat is None:
        return False
    now = datetime.now(timezone.utc)
    if last_beat.tzinfo is None:
        last_beat = last_beat.replace(tzinfo=timezone.utc)
    return (now - last_beat) < _ALIVE_WINDOW


async def _read_control(pool: asyncpg.Pool) -> dict:
    row = await pool.fetchrow(
        "SELECT paused, focus_project_id, last_beat FROM daemon_control WHERE id = TRUE"
    )
    if row is None:
        # Defensive: the migration seeds a row, but never 500 if it's missing.
        return {"paused": False, "alive": False, "last_beat": None, "focus_project_id": None}
    return {
        "paused":           bool(row["paused"]),
        "alive":            _is_alive(row["last_beat"]),
        "last_beat":        row["last_beat"].isoformat() if row["last_beat"] else None,
        "focus_project_id": str(row["focus_project_id"]) if row["focus_project_id"] else None,
    }


async def _broadcast_status(state: dict) -> None:
    await sse.broadcast_event("daemon_status", {
        "paused":           state["paused"],
        "alive":            state["alive"],
        "last_beat":        state["last_beat"],
        "focus_project_id": state["focus_project_id"],
    })


@router.get("/daemon/control")
async def get_control():
    """Current daemon control state — polled by the daemon and the UI."""
    pool = await get_pool()
    return await _read_control(pool)


class ControlPatch(BaseModel):
    """Partial update — only the provided fields are written."""
    paused: bool | None = None
    focus_project_id: str | None = None
    # Distinguishes "clear focus" (focus_project_id=null) from "don't touch it".
    clear_focus: bool = False


@router.post("/daemon/control")
async def set_control(patch: ControlPatch):
    """Set the pause flag and/or the focused project, then broadcast status."""
    pool = await get_pool()

    if patch.focus_project_id is not None:
        # Validate the target exists so we never point the daemon at a ghost.
        try:
            exists = await pool.fetchval(
                "SELECT id FROM profiles WHERE id = $1::uuid", patch.focus_project_id
            )
        except (asyncpg.DataError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"invalid focus_project_id: {exc}")
        if exists is None:
            raise HTTPException(status_code=404, detail="focus project not found")

    await pool.execute(
        """
        UPDATE daemon_control
           SET paused = COALESCE($1, paused),
               focus_project_id = CASE
                   WHEN $3 THEN NULL
                   WHEN $2::uuid IS NOT NULL THEN $2::uuid
                   ELSE focus_project_id
               END,
               updated_at = now()
         WHERE id = TRUE
        """,
        patch.paused,
        patch.focus_project_id,
        patch.clear_focus,
    )

    state = await _read_control(pool)
    await _broadcast_status(state)
    return state


@router.post("/daemon/heartbeat")
async def heartbeat():
    """Daemon liveness ping — bumps last_beat and broadcasts status."""
    pool = await get_pool()
    await pool.execute(
        "UPDATE daemon_control SET last_beat = now() WHERE id = TRUE"
    )
    state = await _read_control(pool)
    await _broadcast_status(state)
    return state


class DaemonActivity(BaseModel):
    """One watcher activity for the observability log (Phase H, H4)."""
    watcher: str
    activity: str
    project_id: str | None = None
    detail: dict | None = None


@router.post("/daemon/activity")
async def post_activity(act: DaemonActivity):
    """Record a daemon watcher activity for the admin panel (best-effort)."""
    from . import telemetry
    await telemetry.record_daemon_activity(
        project_id=act.project_id, watcher=act.watcher,
        activity=act.activity, detail=act.detail,
    )
    return {"ok": True}
