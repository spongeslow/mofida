"""Axis 04 -- Brand. FastAPI microservice (port 8104)."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from affinitree import StartupProfile, detect, score as affinitree_score

AXIS = 4
SLUG = "brand"
app = FastAPI(title="Moufida Axis 04 - Brand")


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
    """STATE_EXISTING: compute the innovation score via Affinitree."""
    profile = StartupProfile(**req.profile)
    result = affinitree_score(profile, "innovation")
    anomalies = [a.to_dict() for a in detect(profile)]
    return {
        "axis": AXIS,
        "score_name": "innovation",
        "score": result.score,
        "explanation": result.explanation_tree(),
        "missing_fields": result.missing_fields,
        "anomalies": anomalies,
    }

