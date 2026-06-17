"""Axis 10 -- Gtm. FastAPI microservice (port 8110)."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

AXIS = 10
SLUG = "gtm"
app = FastAPI(title="Moufida Axis 10 - Gtm")


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


@app.post("/metric_update")
def metric_update(payload: dict):
    """Receive a Go-daemon signal routed by the orchestrator (Phase 5)."""
    return {"axis": AXIS, "received": payload, "status": "not_implemented"}

