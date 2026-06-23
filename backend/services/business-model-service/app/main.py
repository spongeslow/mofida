"""Axis 05 -- Business Model / Scalability. FastAPI microservice (port 8105)."""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from affinitree import build_citations, format_evidence_block

from affinitree import (
    OllamaClient,
    StartupProfile,
    derive_blockers,
    generate_justification,
    run_due_diligence,
    score as affinitree_score,
)
from .finance import compute_financials

AXIS = 5
SLUG = "business-model"
app = FastAPI(title="Moufida Axis 05 - Business Model")
logger = logging.getLogger("moufida.business_model")

OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
OLLAMA_MODEL = os.environ["OLLAMA_MODEL"]
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))

_OLLAMA = OllamaClient(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)


class DiagnoseRequest(BaseModel):
    profile: dict


@app.get("/health")
def health():
    return {"status": "ok", "axis": AXIS, "slug": SLUG}


@app.post("/execute")
def execute(payload: dict | None = None):
    """Kept for backward compat. Use /generate instead."""
    return {"axis": AXIS, "mode": "execute", "status": "not_implemented"}


class GenerateRequest(BaseModel):
    language: str = "fr"
    idea: str = ""
    profile: dict = {}
    upstream: dict = {}
    constraints: str | None = None
    mode: str = "generate"
    evidence: dict = {}


def _parse_gen_json(raw: str) -> dict:
    import json as _json
    try:
        return _json.loads(raw)
    except Exception:
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e > s:
            try:
                return _json.loads(raw[s:e + 1])
            except Exception:
                pass
    return {}


@app.post("/generate")
def generate(req: GenerateRequest):
    """Creation mode: generate a structured Business Model proposal."""
    upstream_idea = req.upstream.get("ideation", {}).get("refined_idea", req.idea)
    upstream_market = req.upstream.get("market", {})
    constraints_block = f"\nConstraints: {req.constraints}" if req.constraints else ""
    prompt = (
        f"You are a business model expert. Generate a Business Model plan section.\n"
        f"Language for output: {req.language}\n\n"
        f"STARTUP IDEA: {upstream_idea}\n"
        f"MARKET CONTEXT: {upstream_market}\n"
        f"{constraints_block}\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"revenue_streams": [{"stream": "...", "model": "...", "price_point": "..."}], '
        '"pricing": "...", '
        '"cost_structure": {"fixed": ["..."], "variable": ["..."]}, '
        '"unit_economics": {"ltv": "...", "cac": "...", "margin": "..."}}'
    )
    temperature = 0.7 if req.mode == "regenerate" else 0.4
    content = {"revenue_streams": [], "pricing": "", "cost_structure": {}, "unit_economics": {}}
    try:
        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": format_evidence_block(req.evidence) + prompt, "stream": False,
                  "format": "json", "options": {"temperature": temperature}},
            timeout=OLLAMA_TIMEOUT,
        )
        if not resp.is_success:
            logger.warning("ollama %s: %s", resp.status_code, resp.text[:400])
            resp.raise_for_status()
        parsed = _parse_gen_json(resp.json().get("response", ""))
        content = {
            "revenue_streams": parsed.get("revenue_streams", []),
            "pricing":         str(parsed.get("pricing", "")),
            "cost_structure":  parsed.get("cost_structure", {}),
            "unit_economics":  parsed.get("unit_economics", {}),
        }
    except Exception as exc:
        logger.warning("business-model generate failed: %s", exc)

    streams = len(content["revenue_streams"])
    summary = f"{streams} revenue stream(s); {content['pricing'][:80]}"
    return {"axis": SLUG, "mode": "generate", "content": content,
            "summary": summary, "assumptions": [], "needs_input": [], "citations": build_citations(req.evidence)}


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """STATE_EXISTING: compute scalability score with deterministic financial engine, blockers, and DD."""
    profile = StartupProfile(**req.profile)
    result = affinitree_score(profile, "scalability")

    # Deterministic financial engine — CAC/LTV/payback/runway/margin.
    fin = compute_financials(req.profile)

    # Merge Affinitree blockers with financial-engine blockers.
    blockers = derive_blockers(result, SLUG) + fin["blockers"]
    dd = run_due_diligence(profile, SLUG)

    justification = None
    try:
        justification = generate_justification(result, _OLLAMA, profile.language)
    except Exception as exc:
        logger.warning("justification failed: %s", exc)

    return {
        "axis": AXIS,
        "score_name": "scalability",
        "score": result.score,
        "explanation": result.explanation_tree(),
        "missing_fields": result.missing_fields,
        "financials": fin["financials"],
        "blockers": blockers,
        "due_diligence": dd,
        "justification": justification,
    }


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
    """Receive a budget signal from the Go daemon and push a runway SSE alert."""
    metric_type = payload.get("type")
    project_id = payload.get("project_id", "")
    value = payload.get("value", {})
    logger.info("metric_update axis=%s type=%s project_id=%s", AXIS, metric_type, project_id)

    if metric_type == "budget":
        runway = value.get("runway_months", 0)
        severity = value.get("severity", "warning")
        msg = f"Alerte trésorerie : runway {runway:.1f} mois — {severity.upper()}"
        await _push_alert(project_id, "budget", severity, msg)

    return {"axis": AXIS, "status": "ok"}
