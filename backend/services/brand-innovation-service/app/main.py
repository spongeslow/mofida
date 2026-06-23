"""Axis 04 -- Brand & Innovation. FastAPI microservice (port 8104)."""
from __future__ import annotations

import logging
import os

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
    score_profile_text_fields_detail,
)

AXIS = 4
SLUG = "brand"
app = FastAPI(title="Moufida Axis 04 - Brand & Innovation")
logger = logging.getLogger("moufida.brand")

OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
OLLAMA_MODEL = os.environ["OLLAMA_MODEL"]
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))

_OLLAMA = OllamaClient(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)


class DiagnoseRequest(BaseModel):
    profile: dict
    prior_outputs: dict = {}


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
    """Creation mode: generate a structured Brand proposal."""
    import httpx as _httpx
    upstream_idea = req.upstream.get("ideation", {}).get("refined_idea", req.idea)
    upstream_product = req.upstream.get("product", {})
    constraints_block = f"\nConstraints: {req.constraints}" if req.constraints else ""
    prompt = (
        f"You are a brand strategist. Generate a Brand Identity plan section.\n"
        f"Language for output: {req.language}\n\n"
        f"STARTUP IDEA: {upstream_idea}\n"
        f"PRODUCT CONTEXT: {upstream_product}\n"
        f"{constraints_block}\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"values": ["...", "..."], "tone": "...", "visual_direction": "..."}'
    )
    temperature = 0.7 if req.mode == "regenerate" else 0.4
    content = {"values": [], "tone": "", "visual_direction": ""}
    try:
        resp = _httpx.post(
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
            "values":           parsed.get("values", []),
            "tone":             str(parsed.get("tone", "")),
            "visual_direction": str(parsed.get("visual_direction", "")),
        }
    except Exception as exc:
        logger.warning("brand generate failed: %s", exc)

    summary = f"Valeurs: {', '.join(str(v) for v in content['values'][:3])}; Ton: {content['tone'][:60]}"
    return {"axis": SLUG, "mode": "generate", "content": content,
            "summary": summary, "assumptions": [], "needs_input": [], "citations": build_citations(req.evidence)}


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """STATE_EXISTING: compute innovation score with rubric scoring, prior outputs, blockers, and DD."""
    profile = StartupProfile(**req.profile)

    # Score rubric text fields (novelty_text, brand_distinctiveness_text, value_prop_text).
    rubric_detail: dict = {}
    degraded_rubric = False
    try:
        rubric_detail = score_profile_text_fields_detail(profile, _OLLAMA)
    except Exception as exc:
        logger.warning("rubric scoring degraded: %s", exc)
        degraded_rubric = True

    result = affinitree_score(profile, "innovation")

    blockers = derive_blockers(result, SLUG)
    dd = run_due_diligence(profile, SLUG)

    # Use prior market output to enrich competitor-related blockers.
    market_out = req.prior_outputs.get("market") or {}
    if profile.market.competitor_count == 0 and not market_out:
        blockers.append({
            "axis": SLUG,
            "code": "innovation.market_novelty.no_competitor_data",
            "description": "Competitor count unknown — market-novelty confidence reduced.",
            "severity": "warning",
            "score_dimension": "innovation",
            "remediation": "Complete the market competitor analysis (Axis 02).",
        })

    justification = None
    try:
        justification = generate_justification(result, _OLLAMA, profile.language)
    except Exception as exc:
        logger.warning("justification failed: %s", exc)

    response: dict = {
        "axis": AXIS,
        "score_name": "innovation",
        "score": result.score,
        "explanation": result.explanation_tree(),
        "missing_fields": result.missing_fields,
        "blockers": blockers,
        "due_diligence": dd,
        "justification": justification,
    }
    if rubric_detail:
        response["rubric_detail"] = rubric_detail
    if degraded_rubric:
        response["degraded_rubric"] = True
    return response
