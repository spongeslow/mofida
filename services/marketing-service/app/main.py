"""Axis 07 -- Marketing. FastAPI microservice (port 8107)."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

AXIS = 7
SLUG = "marketing"
app = FastAPI(title="Moufida Axis 07 - Marketing")


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
    """STATE_EXISTING diagnostic stub (filled in Phase 2)."""
    return {"axis": AXIS, "mode": "diagnose", "status": "not_implemented"}

