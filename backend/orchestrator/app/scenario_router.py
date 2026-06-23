"""Pivot Scenario Planner (Phase H, H2).

Projects the impact of a set of profile overrides on all nine axes. Each axis
projection is a RAG-grounded Ollama call run in parallel; results carry a
confidence level and cited KB sources. Projections are ephemeral (kept in a
small in-memory cache per project); adopting one patches the profile so the
caller can re-diagnose.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone

import asyncpg
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .axis_registry import AXES, NETWORK_AXES
from .evidence_snapshot import gather_evidence
from .llm_json import generate_json
from .state_router import get_pool

router = APIRouter(tags=["scenario"])
logger = logging.getLogger("moufida.scenario")

RAG_URL = os.environ.get("RAG_URL", "http://rag:8300")

# Ephemeral per-project projection cache (process-local; projections are cheap to
# recompute and not worth a table).
_SCENARIOS: dict[str, list[dict]] = {}
_MAX_CACHED = 10


def _current_score(axis: str, scores: dict, bottlenecks: list[dict]) -> float | None:
    """Best available current score for an axis: its composite, else its CBM score."""
    score_name = AXES.get(axis, {}).get("score")
    if score_name and score_name in scores:
        return scores[score_name]
    for b in bottlenecks:
        if b.get("axis") == axis and b.get("cbm_score") is not None:
            return round(float(b["cbm_score"]), 2)
    return None


async def _rag_sources(client: httpx.AsyncClient, axis: str, query: str) -> list[dict]:
    try:
        resp = await client.post(
            f"{RAG_URL}/retrieve",
            json={"query": query, "top_k": 3, "current_axis": axis},
            timeout=20.0,
        )
        resp.raise_for_status()
        out = []
        for r in resp.json().get("results", []):
            title = r.get("title") or r.get("resource_id") or "KB"
            out.append({"kind": "kb", "label": "KB", "doc": title})
        return out
    except Exception as exc:  # noqa: BLE001
        logger.debug("scenario rag failed axis=%s: %s", axis, exc)
        return []


async def _project_axis(
    client: httpx.AsyncClient, axis: str, current: float | None,
    overrides: dict, sector: str, language: str,
) -> tuple[str, dict]:
    override_str = ", ".join(f"{k}→{v}" for k, v in overrides.items())
    query = f"In the {sector} sector, when a startup changes {override_str}, how does {axis} change?"
    sources = await _rag_sources(client, axis, query)
    kb_text = "; ".join(s["doc"] for s in sources) or "no specific KB evidence"

    base = current if current is not None else 2.5
    prompt = (
        f"You are a startup analyst. The '{axis}' axis currently scores {base}/5.\n"
        f"Proposed pivot (parameter overrides): {override_str}\n"
        f"Sector: {sector}. Relevant KB evidence: {kb_text}\n\n"
        "Estimate the pivot's effect on THIS axis. Be realistic and conservative; "
        "use the KB evidence. Confidence reflects how much evidence supports the estimate.\n"
        'Respond JSON only: {"projected_score": <0-5 float>, '
        '"confidence": "high|medium|low", "reasoning": "one or two sentences"}\n'
        f"Write the reasoning in {language}."
    )
    out = await generate_json(prompt, temperature=0.3, axis="scenario")
    try:
        projected = float(out.get("projected_score", base))
    except (TypeError, ValueError):
        projected = base
    projected = max(0.0, min(5.0, projected))
    confidence = out.get("confidence", "low")
    if confidence not in ("high", "medium", "low"):
        confidence = "low"
    return axis, {
        "current_score": current,
        "projected_score": round(projected, 2),
        "delta": round(projected - base, 2),
        "confidence": confidence,
        "reasoning": out.get("reasoning", ""),
        "sources": sources,
    }


class ProjectBody(BaseModel):
    label: str
    overrides: dict
    language: str = "fr"


@router.post("/project/{project_id}/scenario/project")
async def project_scenario(project_id: str, body: ProjectBody):
    if not body.overrides:
        raise HTTPException(status_code=400, detail="no overrides provided")
    pool = await get_pool()
    try:
        ev = await gather_evidence(pool, project_id)
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    sector = str(ev.get("profile", {}).get("sector", "cross-sector"))
    scores = ev.get("scores", {})
    bottlenecks = ev.get("bottlenecks", [])

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*(
            _project_axis(client, axis,
                          _current_score(axis, scores, bottlenecks),
                          body.overrides, sector, body.language)
            for axis in NETWORK_AXES
        ))

    axis_projections = dict(results)
    deltas = [p["delta"] for p in axis_projections.values()]
    overall_delta = round(sum(deltas) / len(deltas), 2) if deltas else 0.0

    projection = {
        "label": body.label,
        "overrides": body.overrides,
        "axis_projections": axis_projections,
        "overall_delta": overall_delta,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    cache = _SCENARIOS.setdefault(project_id, [])
    cache[:] = [c for c in cache if c["label"] != body.label]  # replace same label
    cache.insert(0, projection)
    del cache[_MAX_CACHED:]
    return projection


@router.get("/project/{project_id}/scenarios")
async def list_scenarios(project_id: str):
    return {"scenarios": _SCENARIOS.get(project_id, [])}


@router.post("/project/{project_id}/scenario/{label}/adopt")
async def adopt_scenario(project_id: str, label: str):
    cache = _SCENARIOS.get(project_id, [])
    scenario = next((c for c in cache if c["label"] == label), None)
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario not found (re-project it first)")

    pool = await get_pool()
    try:
        await pool.execute(
            "UPDATE profiles SET profile = COALESCE(profile, '{}'::jsonb) || $2::jsonb WHERE id = $1::uuid",
            project_id, json.dumps(scenario["overrides"]),
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"ok": True, "overrides_applied": scenario["overrides"],
            "hint": "re-run the diagnostic to see the adopted scenario reflected"}
