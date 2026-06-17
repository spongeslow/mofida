"""Axis 03 -- Product. FastAPI microservice (port 8103)."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from affinitree import StartupProfile, detect, score as affinitree_score

AXIS = 3
SLUG = "product"
app = FastAPI(title="Moufida Axis 03 - Product")


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
    """STATE_EXISTING: compute the commercial_offer score via Affinitree."""
    profile = StartupProfile(**req.profile)
    result = affinitree_score(profile, "commercial_offer")
    anomalies = [a.to_dict() for a in detect(profile)]
    return {
        "axis": AXIS,
        "score_name": "commercial_offer",
        "score": result.score,
        "explanation": result.explanation_tree(),
        "missing_fields": result.missing_fields,
        "anomalies": anomalies,
    }

