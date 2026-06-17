"""Axis 06 -- Legal. FastAPI microservice (port 8106)."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from affinitree import StartupProfile, detect, score as affinitree_score

AXIS = 6
SLUG = "legal"
app = FastAPI(title="Moufida Axis 06 - Legal")


class DiagnoseRequest(BaseModel):
    profile: dict


@app.get("/health")
def health():
    return {"status": "ok", "axis": AXIS, "slug": SLUG}


@app.post("/execute")
def execute(payload: dict | None = None):
    """STATE_NEW guided step (Phase 4). Stubbed for now."""
    return {"axis": AXIS, "mode": "execute", "status": "not_implemented"}


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """STATE_EXISTING: compute the green score via Affinitree."""
    profile = StartupProfile(**req.profile)
    result = affinitree_score(profile, "green")
    anomalies = [a.to_dict() for a in detect(profile)]
    return {
        "axis": AXIS,
        "score_name": "green",
        "score": result.score,
        "explanation": result.explanation_tree(),
        "missing_fields": result.missing_fields,
        "anomalies": anomalies,
    }


@app.post("/metric_update")
def metric_update(payload: dict):
    """Receive a Go-daemon signal routed by the orchestrator (Phase 5)."""
    return {"axis": AXIS, "received": payload, "status": "not_implemented"}

