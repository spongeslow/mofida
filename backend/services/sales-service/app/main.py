"""Axis 08 -- Sales Readiness. FastAPI microservice (port 8108)."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from pydantic import BaseModel
from affinitree import build_citations, format_evidence_block

from affinitree import StartupProfile, run_due_diligence

AXIS = 8
SLUG = "sales"
app = FastAPI(title="Moufida Axis 08 - Sales")
logger = logging.getLogger("moufida.sales")

# Weights for the sales readiness score.
_W_PILOTS = 0.40
_W_INTERVIEWS = 0.35
_W_CAC_TRACKED = 0.25


class DiagnoseRequest(BaseModel):
    profile: dict


@app.get("/health")
def health():
    return {"status": "ok", "axis": AXIS, "slug": SLUG}


@app.post("/execute")
def execute(payload: dict | None = None):
    """Kept for backward compat. Use /generate instead."""
    return {"axis": AXIS, "mode": "execute", "status": "not_implemented"}


import os as _os
import httpx as _httpx

_OLLAMA_BASE = _os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
_OLLAMA_MODEL = _os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = float(_os.getenv("OLLAMA_TIMEOUT", "300"))


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
    """Creation mode: generate a structured Sales plan proposal."""
    upstream_idea = req.upstream.get("ideation", {}).get("refined_idea", req.idea)
    upstream_marketing = req.upstream.get("marketing", {})
    constraints_block = f"\nConstraints: {req.constraints}" if req.constraints else ""
    prompt = (
        f"You are a sales expert. Generate a Sales plan section for a startup.\n"
        f"Language for output: {req.language}\n\n"
        f"STARTUP IDEA: {upstream_idea}\n"
        f"MARKETING CONTEXT: {upstream_marketing}\n"
        f"{constraints_block}\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"sales_channels": ["..."], "pipeline_model": "...", '
        '"partnerships": [{"partner": "...", "type": "...", "value": "..."}]}'
    )
    temperature = 0.7 if req.mode == "regenerate" else 0.4
    content = {"sales_channels": [], "pipeline_model": "", "partnerships": []}
    try:
        resp = _httpx.post(
            f"{_OLLAMA_BASE}/api/generate",
            json={"model": _OLLAMA_MODEL, "prompt": format_evidence_block(req.evidence) + prompt, "stream": False,
                  "format": "json", "options": {"temperature": temperature}},
            timeout=OLLAMA_TIMEOUT,
        )
        if not resp.is_success:
            logger.warning("ollama %s: %s", resp.status_code, resp.text[:400])
            resp.raise_for_status()
        parsed = _parse_gen_json(resp.json().get("response", ""))
        content = {
            "sales_channels": parsed.get("sales_channels", []),
            "pipeline_model": str(parsed.get("pipeline_model", "")),
            "partnerships":   parsed.get("partnerships", []),
        }
    except Exception as exc:
        import logging as _log
        _log.getLogger("moufida.sales").warning("sales generate failed: %s", exc)

    ch = len(content["sales_channels"])
    summary = f"{ch} canal/canaux de vente; {content['pipeline_model'][:80]}"
    return {"axis": SLUG, "mode": "generate", "content": content,
            "summary": summary, "assumptions": [], "needs_input": [], "citations": build_citations(req.evidence)}


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """STATE_EXISTING: compute sales readiness score, gaps, blockers, and DD."""
    profile = StartupProfile(**req.profile)

    pilots_ok = 1.0 if profile.market.paid_pilots_count > 0 else 0.0
    interviews_ok = 1.0 if profile.market.customer_interviews_count > 0 else 0.0
    cac_ok = 1.0 if (profile.finance.cac_usd or 0) > 0 else 0.0

    sales_readiness = round(
        pilots_ok * _W_PILOTS
        + interviews_ok * _W_INTERVIEWS
        + cac_ok * _W_CAC_TRACKED,
        4,
    )

    gaps: list[str] = []
    if profile.market.paid_pilots_count == 0:
        gaps.append("no_paying_pilots")
    if profile.market.customer_interviews_count == 0:
        gaps.append("no_customer_interviews")
    if not (profile.finance.cac_usd or 0) > 0:
        gaps.append("cac_not_tracked")

    # Derive blockers from gaps.
    blockers: list[dict] = []
    if profile.market.paid_pilots_count == 0:
        blockers.append({
            "axis": SLUG,
            "code": "sales.no_paying_pilots",
            "description": "No paying pilots — sales traction unproven.",
            "severity": "critical" if profile.offer.product_stage in ("mvp", "ga", "mature") else "warning",
            "score_dimension": "sales_readiness",
            "remediation": "Close at least one paid pilot to validate willingness-to-pay.",
        })
    if profile.market.customer_interviews_count == 0:
        blockers.append({
            "axis": SLUG,
            "code": "sales.no_customer_interviews",
            "description": "No customer discovery interviews — needs not validated.",
            "severity": "critical",
            "score_dimension": "sales_readiness",
            "remediation": "Run at least 5 structured problem interviews with target customers.",
        })
    if not (profile.finance.cac_usd or 0) > 0:
        blockers.append({
            "axis": SLUG,
            "code": "sales.cac_not_tracked",
            "description": "Customer Acquisition Cost not tracked.",
            "severity": "info",
            "score_dimension": "sales_readiness",
            "remediation": "Calculate CAC: total sales + marketing spend ÷ customers acquired in period.",
        })

    dd = run_due_diligence(profile, SLUG)

    return {
        "axis": AXIS,
        "score_name": "sales_readiness",
        "score": sales_readiness,
        "sales_readiness": sales_readiness,
        "gaps": gaps,
        "blockers": blockers,
        "due_diligence": dd,
    }
