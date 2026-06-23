"""CBM HTTP surface: fetch the latest concept breakdown, and calibrate the
linear bottleneck head from accumulated diagnostic history."""
from __future__ import annotations

import json
import logging
import os

import httpx
from fastapi import APIRouter, HTTPException

from ..axis_registry import AXES, NETWORK_AXES
from ..state_router import get_pool
from .scorer import SIGNAL_URL, concept_labels

router = APIRouter(tags=["cbm"])
logger = logging.getLogger("moufida.cbm.router")

# Minimum (concept_vector, actual_score) pairs before an axis is worth calibrating.
_MIN_OBS = int(os.getenv("CBM_MIN_CALIBRATION_OBS", "8"))


def _as_dict(v) -> dict:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {}
    return v or {}


@router.get("/project/{project_id}/concept-scores")
async def get_concept_scores(project_id: str):
    """Latest concept breakdown per axis for a project."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT DISTINCT ON (axis)
                   axis, concepts, cbm_score, actual_score, bottleneck, calibrated, created_at
              FROM concept_scores
             WHERE project_id = $1::uuid
             ORDER BY axis, created_at DESC
            """,
            project_id,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"invalid project_id: {exc}")

    axes: list[dict] = []
    for r in rows:
        axes.append({
            "axis": r["axis"],
            "concepts": _as_dict(r["concepts"]),
            "cbm_score": r["cbm_score"],
            "actual_score": r["actual_score"],
            "bottleneck": _as_dict(r["bottleneck"]) or None,
            "calibrated": r["calibrated"],
            "labels": concept_labels(r["axis"]),
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        })
    return {"project_id": project_id, "axes": axes, "count": len(axes)}


@router.post("/cbm/calibrate")
async def calibrate(project_id: str | None = None):
    """Re-fit the per-axis linear weights from stored (concepts, actual_score)
    observations and push them to the signal service.

    Pools observations across all projects by default (more data = better fit);
    pass ``?project_id=`` to restrict to one project. Only axes that own a
    composite score and have >= CBM_MIN_CALIBRATION_OBS observations are fitted.
    """
    pool = await get_pool()

    if project_id:
        where, args = "WHERE axis = $1 AND actual_score IS NOT NULL AND project_id = $2::uuid", (project_id,)
    else:
        where, args = "WHERE axis = $1 AND actual_score IS NOT NULL", ()

    results: list[dict] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for axis in NETWORK_AXES:
            # Only axes mapped to a composite score have a calibration target.
            if AXES.get(axis, {}).get("score") is None:
                continue
            rows = await pool.fetch(
                f"SELECT concepts, actual_score FROM concept_scores {where}",
                axis, *args,
            )
            observations = [
                {"concepts": _as_dict(r["concepts"]), "actual_score": float(r["actual_score"])}
                for r in rows
                if r["actual_score"] is not None
            ]
            if len(observations) < _MIN_OBS:
                results.append({"axis": axis, "skipped": True, "observations": len(observations)})
                continue
            try:
                resp = await client.post(
                    f"{SIGNAL_URL}/cbm/calibrate",
                    json={"axis": axis, "observations": observations},
                )
                resp.raise_for_status()
                out = resp.json()
                results.append({
                    "axis": axis,
                    "calibrated": True,
                    "observations": out.get("observations"),
                    "r_squared": out.get("r_squared"),
                })
            except Exception as exc:  # noqa: BLE001
                logger.warning("cbm calibrate failed axis=%s: %s", axis, exc)
                results.append({"axis": axis, "error": str(exc)})

    return {"results": results}
