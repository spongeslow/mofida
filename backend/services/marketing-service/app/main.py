"""Axis 07 -- Marketing Readiness. FastAPI microservice (port 8107)."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from pydantic import BaseModel
from affinitree import build_citations, format_evidence_block

from affinitree import StartupProfile, run_due_diligence

AXIS = 7
SLUG = "marketing"
app = FastAPI(title="Moufida Axis 07 - Marketing")
logger = logging.getLogger("moufida.marketing")

# Weights for the marketing readiness score.
_W_BRAND_REGISTERED = 0.35
_W_LOGO_EXISTS = 0.25
_W_HAS_REVENUE = 0.40


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
    """Creation mode: generate a structured Marketing plan proposal."""
    upstream_idea = req.upstream.get("ideation", {}).get("refined_idea", req.idea)
    upstream_brand = req.upstream.get("brand", {})
    constraints_block = f"\nConstraints: {req.constraints}" if req.constraints else ""
    prompt = (
        f"You are a marketing expert. Generate a Marketing plan section for a startup.\n"
        f"Language for output: {req.language}\n\n"
        f"STARTUP IDEA: {upstream_idea}\n"
        f"BRAND: {upstream_brand}\n"
        f"{constraints_block}\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"channels": [{"channel": "...", "tactics": "...", "budget_pct": "..."}], '
        '"content_strategy": "...", "launch_plan": "..."}'
    )
    temperature = 0.7 if req.mode == "regenerate" else 0.4
    content = {"channels": [], "content_strategy": "", "launch_plan": ""}
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
            "channels":         parsed.get("channels", []),
            "content_strategy": str(parsed.get("content_strategy", "")),
            "launch_plan":      str(parsed.get("launch_plan", "")),
        }
    except Exception as exc:
        import logging as _log
        _log.getLogger("moufida.marketing").warning("marketing generate failed: %s", exc)

    ch = len(content["channels"])
    summary = f"{ch} canal/canaux; {content['content_strategy'][:80]}"
    return {"axis": SLUG, "mode": "generate", "content": content,
            "summary": summary, "assumptions": [], "needs_input": [], "citations": build_citations(req.evidence)}


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """STATE_EXISTING: compute marketing readiness score, gaps, blockers, and DD."""
    profile = StartupProfile(**req.profile)

    brand_ok = float(profile.offer.brand_name_registered)
    logo_ok = float(profile.offer.logo_exists)
    revenue_ok = 1.0 if profile.market.mrr_usd > 0 else 0.0

    marketing_readiness = round(
        brand_ok * _W_BRAND_REGISTERED
        + logo_ok * _W_LOGO_EXISTS
        + revenue_ok * _W_HAS_REVENUE,
        4,
    )

    gaps: list[str] = []
    if not profile.offer.brand_name_registered:
        gaps.append("brand_name_not_registered")
    if not profile.offer.logo_exists:
        gaps.append("no_logo")
    if profile.market.mrr_usd == 0:
        gaps.append("no_revenue_generating_product")

    # Derive blockers from gaps (info-severity — marketing is a secondary axis).
    blockers: list[dict] = []
    if not profile.offer.brand_name_registered:
        blockers.append({
            "axis": SLUG,
            "code": "marketing.no_brand_name",
            "description": "Brand name not registered.",
            "severity": "warning",
            "score_dimension": "marketing_readiness",
            "remediation": "Register your brand name via INNORPI.",
        })
    if not profile.offer.logo_exists:
        blockers.append({
            "axis": SLUG,
            "code": "marketing.no_logo",
            "description": "No logo / visual identity exists.",
            "severity": "info",
            "score_dimension": "marketing_readiness",
            "remediation": "Create a minimal visual identity (logo, brand colours, typography).",
        })
    if profile.market.mrr_usd == 0:
        blockers.append({
            "axis": SLUG,
            "code": "marketing.no_product_revenue",
            "description": "No revenue — product not yet revenue-generating.",
            "severity": "info",
            "score_dimension": "marketing_readiness",
            "remediation": "Achieve initial revenue before investing heavily in marketing infrastructure.",
        })

    dd = run_due_diligence(profile, SLUG)

    return {
        "axis": AXIS,
        "score_name": "marketing_readiness",
        "score": marketing_readiness,
        "marketing_readiness": marketing_readiness,
        "gaps": gaps,
        "blockers": blockers,
        "due_diligence": dd,
    }
