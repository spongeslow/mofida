"""Axis 10 — Go-to-Market roadmap service (port 8110)."""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from .roadmap import generate_roadmap

AXIS = 10
SLUG = "gtm"
app = FastAPI(title="Moufida Axis 10 - GTM Roadmap")
logger = logging.getLogger("moufida.gtm")


class RoadmapRequest(BaseModel):
    project_id: str
    stage: str
    sector: str
    language: str = "fr"
    blockers: list[dict] = []
    scores: dict[str, float] = {}
    profile: dict = {}


class DiagnoseRequest(BaseModel):
    profile: dict


@app.get("/health")
def health():
    return {"status": "ok", "axis": AXIS, "slug": SLUG}


@app.post("/execute")
def execute(payload: dict | None = None):
    return {"axis": AXIS, "mode": "execute", "status": "not_implemented"}


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    return {"axis": AXIS, "mode": "diagnose", "status": "not_implemented"}


@app.post("/roadmap")
async def roadmap(req: RoadmapRequest):
    """Generate a 3-horizon RAG-augmented action roadmap for the project."""
    result = await generate_roadmap(
        project_id=req.project_id,
        stage=req.stage,
        sector=req.sector,
        language=req.language,
        blockers=req.blockers,
        scores=req.scores,
        profile=req.profile,
    )
    return {"project_id": req.project_id, **result}


_ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8001")


async def _push_alert(project_id: str, source: str, severity: str, message: str) -> None:
    if not project_id:
        return
    async with httpx.AsyncClient(timeout=5.0) as http:
        try:
            await http.post(
                f"{_ORCHESTRATOR_URL}/api/v1/sse/push/{project_id}",
                json={"event": "alert", "payload": {"source": source, "severity": severity, "message": message}},
            )
        except httpx.HTTPError as exc:
            logger.warning("SSE push failed: %s", exc)


@app.post("/metric_update")
async def metric_update(payload: dict):
    """Receive a milestone signal from the Go daemon and push a deadline SSE alert."""
    metric_type = payload.get("type")
    project_id = payload.get("project_id", "")
    value = payload.get("value", {})
    logger.info("metric_update axis=%s type=%s project_id=%s", AXIS, metric_type, project_id)

    if metric_type == "milestone":
        name = value.get("name", "")
        days_left = value.get("days_left", 0)
        deadline = value.get("deadline_date", "")
        if days_left <= 1:
            severity = "critical"
        elif days_left <= 7:
            severity = "warning"
        else:
            severity = "info"
        msg = (
            f"Milestone '{name}' : échéance {'aujourd\'hui' if days_left == 0 else f'dans {days_left} jour(s)'}"
            + (f" ({deadline})" if deadline else "")
        )
        await _push_alert(project_id, "milestone", severity, msg)

    return {"axis": AXIS, "status": "ok"}
