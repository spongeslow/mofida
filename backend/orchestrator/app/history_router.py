"""History endpoints for Mon Parcours view.

Provides time-series score snapshots and diagnostic history for a project,
plus the human-in-the-loop review endpoint.
"""
from __future__ import annotations

import json
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import sse
from .state_router import get_pool

router = APIRouter()


@router.get("/project/{project_id}/history")
async def score_history(project_id: str):
    """Score snapshot time series for the ScoreChart component."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT score_name, score, created_at
              FROM score_snapshots
             WHERE project_id = $1::uuid
             ORDER BY created_at ASC
            """,
            project_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "snapshots": [
            {
                "score_name": r["score_name"],
                "score": r["score"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ]
    }


@router.get("/project/{project_id}/diagnostic-history")
async def diagnostic_history(project_id: str):
    """Past diagnostic runs for the HistoryList component."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT maturity_stage, self_assessed, perception_gap,
                   confidence, evidence, blockers, created_at
              FROM diagnostic_history
             WHERE project_id = $1::uuid
             ORDER BY created_at DESC
            """,
            project_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    def _parse_jsonb(val) -> list:
        if val is None:
            return []
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        return val if isinstance(val, list) else []

    return {
        "history": [
            {
                "maturity_stage": r["maturity_stage"],
                "self_assessed": r["self_assessed"],
                "perception_gap": r["perception_gap"],
                "confidence": r["confidence"],
                "evidence": _parse_jsonb(r["evidence"]),
                "blockers": _parse_jsonb(r["blockers"]),
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ]
    }


@router.get("/project/{project_id}/roadmap")
async def latest_roadmap(project_id: str):
    """Most-recent roadmap version for a project (dashboard / Mon Parcours)."""
    pool = await get_pool()
    try:
        row = await pool.fetchrow(
            """
            SELECT version, roadmap, created_at
              FROM roadmap_versions
             WHERE project_id = $1::uuid
             ORDER BY version DESC
             LIMIT 1
            """,
            project_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if row is None:
        return {"roadmap": None, "version": 0, "created_at": None}
    roadmap = row["roadmap"]
    if isinstance(roadmap, str):
        roadmap = json.loads(roadmap or "{}")
    return {
        "roadmap": roadmap,
        "version": row["version"],
        "created_at": row["created_at"].isoformat(),
    }


class RoadmapActionRequest(BaseModel):
    action_key: str
    action_text: Optional[str] = None
    horizon: Optional[str] = None
    completed: bool = True


@router.post("/project/{project_id}/roadmap/action")
async def set_roadmap_action(project_id: str, req: RoadmapActionRequest):
    """Mark a roadmap action complete / incomplete (upsert by action_key)."""
    pool = await get_pool()
    try:
        await pool.execute(
            """
            INSERT INTO roadmap_action_status
                (project_id, action_key, action_text, horizon, completed, completed_at)
            VALUES ($1::uuid, $2, $3, $4, $5, now())
            ON CONFLICT (project_id, action_key)
            DO UPDATE SET completed = EXCLUDED.completed,
                          action_text = EXCLUDED.action_text,
                          horizon = EXCLUDED.horizon,
                          completed_at = now()
            """,
            project_id,
            req.action_key,
            req.action_text,
            req.horizon,
            req.completed,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True, "action_key": req.action_key, "completed": req.completed}


@router.get("/project/{project_id}/roadmap/actions")
async def roadmap_action_statuses(project_id: str):
    """All action completion records for a project (hydrate checkboxes + journey)."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT action_key, action_text, horizon, completed, completed_at
              FROM roadmap_action_status
             WHERE project_id = $1::uuid
             ORDER BY completed_at DESC
            """,
            project_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "actions": [
            {
                "action_key": r["action_key"],
                "action_text": r["action_text"],
                "horizon": r["horizon"],
                "completed": r["completed"],
                "completed_at": r["completed_at"].isoformat(),
            }
            for r in rows
        ]
    }


@router.get("/project/{project_id}/history/compare")
async def compare_diagnostic_runs(project_id: str, from_idx: int = 2, to_idx: int = 1):
    """Compare two diagnostic runs by 1-based recency index (1 = most recent).

    Returns per-score deltas, and blocker resolved/new between the two runs.
    """
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT id, maturity_stage, confidence, evidence, blockers, created_at
              FROM diagnostic_history
             WHERE project_id = $1::uuid
             ORDER BY created_at DESC
            """,
            project_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if len(rows) < max(from_idx, to_idx):
        raise HTTPException(
            status_code=404,
            detail=f"Not enough runs: have {len(rows)}, need index {max(from_idx, to_idx)}",
        )

    def _parse(val) -> list:
        if val is None:
            return []
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        return val if isinstance(val, list) else []

    run_from = rows[from_idx - 1]
    run_to   = rows[to_idx - 1]

    # Load score snapshots closest to each run's timestamp.
    async def _scores_near(ts) -> dict[str, float]:
        score_rows = await pool.fetch(
            """
            SELECT DISTINCT ON (score_name) score_name, score
              FROM score_snapshots
             WHERE project_id = $1::uuid
               AND created_at <= $2::timestamptz + interval '5 minutes'
             ORDER BY score_name, created_at DESC
            """,
            project_id,
            ts,
        )
        return {r["score_name"]: r["score"] for r in score_rows}

    scores_from = await _scores_near(run_from["created_at"])
    scores_to   = await _scores_near(run_to["created_at"])

    all_score_names = set(scores_from) | set(scores_to)
    score_deltas = {
        name: {
            "from":  scores_from.get(name),
            "to":    scores_to.get(name),
            "delta": (scores_to.get(name) or 0) - (scores_from.get(name) or 0),
        }
        for name in sorted(all_score_names)
    }

    blockers_from = {b.get("code", b.get("description", "")): b for b in _parse(run_from["blockers"])}
    blockers_to   = {b.get("code", b.get("description", "")): b for b in _parse(run_to["blockers"])}

    return {
        "project_id": project_id,
        "from": {
            "created_at":    run_from["created_at"].isoformat(),
            "maturity_stage": run_from["maturity_stage"],
        },
        "to": {
            "created_at":    run_to["created_at"].isoformat(),
            "maturity_stage": run_to["maturity_stage"],
        },
        "score_deltas": score_deltas,
        "blockers_resolved": [b for k, b in blockers_from.items() if k not in blockers_to],
        "blockers_new":      [b for k, b in blockers_to.items()   if k not in blockers_from],
    }


class ReviewRequest(BaseModel):
    axis: str
    decision: Literal["approve", "edit", "retry"]
    edit: Optional[str] = None


@router.post("/project/{project_id}/review")
async def submit_review(project_id: str, req: ReviewRequest):
    """Handle human-in-the-loop Approve / Edit / Retry decisions."""
    event_map = {
        "approve": "review_approved",
        "edit": "review_edited",
        "retry": "review_retry",
    }
    payload: dict = {"axis": req.axis, "decision": req.decision}
    if req.edit:
        payload["edit"] = req.edit

    await sse.push_event(project_id, event_map[req.decision], payload)
    return {"status": "ok", "axis": req.axis, "decision": req.decision}
