"""Moufida Orchestrator -- FastAPI + LangGraph brain (port 8001).

Phase 0 scaffold: exposes /health and a static description of the axis routing
topology. The state router, adaptive intake, diagnostic runner, LangGraph state
machine and Redis consumer are filled in across Phases 2 and 5.
"""
from __future__ import annotations

from fastapi import FastAPI

from .axis_registry import AXES, diagnostic_order

app = FastAPI(title="Moufida Orchestrator")


@app.get("/health")
def health():
    return {"status": "ok", "service": "orchestrator"}


@app.get("/topology")
def topology():
    """The axis map the diagnostic pass and Redis consumer rely on."""
    return {
        "axes": AXES,
        "diagnostic_order": diagnostic_order(),
    }


@app.get("/state/{project_id}")
def get_state(project_id: str):
    """Returns STATE_NEW / STATE_EXISTING for a project (Phase 2)."""
    return {"project_id": project_id, "state": "unknown", "status": "not_implemented"}
