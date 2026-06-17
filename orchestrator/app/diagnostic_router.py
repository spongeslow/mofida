"""Diagnostic endpoint: run the STATE_EXISTING pass, persist it, stream events."""
from __future__ import annotations

import json

import asyncpg
from fastapi import APIRouter, HTTPException

from . import axis_registry, sse
from .diagnostic.aggregator import aggregate_results
from .diagnostic.runner import run_diagnostic_pass
from .state_router import get_pool

router = APIRouter()


async def _persist(conn: asyncpg.Connection, project_id: str, ideation: dict, agg: dict) -> None:
    """Write one diagnostic_history row plus a score_snapshots row per score."""
    await conn.execute(
        """
        INSERT INTO diagnostic_history
            (project_id, maturity_stage, self_assessed, perception_gap,
             confidence, evidence, blockers, anomalies)
        VALUES ($1::uuid, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb)
        """,
        project_id,
        agg["maturity_stage"],
        agg["self_assessed_stage"],
        "yes" if agg["perception_gap"] else "no",
        ideation.get("confidence"),
        json.dumps(ideation.get("evidence", [])),
        json.dumps(agg["blockers"]),
        json.dumps(agg["anomalies"]),
    )
    for name, score in agg["scores"].items():
        await conn.execute(
            """
            INSERT INTO score_snapshots (project_id, score_name, score, breakdown)
            VALUES ($1::uuid, $2, $3, $4::jsonb)
            """,
            project_id,
            name,
            float(score),
            json.dumps(agg["score_breakdowns"].get(name) or {}),
        )


@router.post("/project/{project_id}/run-diagnostic")
async def run_diagnostic(project_id: str):
    pool = await get_pool()

    # 1. Load the profile.
    try:
        row = await pool.fetchrow(
            "SELECT id, profile FROM profiles WHERE id = $1::uuid", project_id
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid project_id: {exc}")
    if row is None:
        raise HTTPException(status_code=404, detail="project not found")

    profile = row["profile"]
    if isinstance(profile, str):
        profile = json.loads(profile or "{}")

    # 2-3. Fan out to the axes and aggregate.
    axis_outputs = await run_diagnostic_pass(project_id, profile, axis_registry)
    agg = aggregate_results(profile, axis_outputs)

    # 4. Persist diagnostic history + score snapshots atomically.
    ideation = axis_outputs.get("ideation") or {}
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _persist(conn, project_id, ideation, agg)

    # 5. Fire SSE events.
    for name, score in agg["scores"].items():
        await sse.push_event(project_id, "score_update", {"score_name": name, "score": score})
    await sse.push_event(
        project_id,
        "maturity_update",
        {
            "maturity_stage": agg["maturity_stage"],
            "self_assessed_stage": agg["self_assessed_stage"],
            "perception_gap": agg["perception_gap"],
        },
    )

    # 6. Return the full aggregated result.
    return {"project_id": project_id, **agg, "axis_outputs": axis_outputs}
