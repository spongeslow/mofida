"""Axis 03 -- Product Offering. FastAPI microservice (port 8103)."""
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

AXIS = 3
SLUG = "product"
app = FastAPI(title="Moufida Axis 03 - Product Offering")
logger = logging.getLogger("moufida.product")

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
    """Creation mode: generate a structured Product proposal."""
    import httpx as _httpx
    upstream_idea = req.upstream.get("ideation", {}).get("refined_idea", req.idea)
    upstream_market = req.upstream.get("market", {})
    constraints_block = f"\nConstraints: {req.constraints}" if req.constraints else ""
    prompt = (
        f"You are a product manager. Generate a Product plan section for a startup MVP.\n"
        f"Language for output: {req.language}\n\n"
        f"STARTUP IDEA: {upstream_idea}\n"
        f"MARKET CONTEXT: {upstream_market}\n"
        f"{constraints_block}\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"mvp_features": [{"feature": "...", "rationale": "...", "priority": "must"}], '
        '"user_stories": ["As a ... I want ... so that ..."], '
        '"tech_stack": [{"layer": "...", "choice": "...", "rationale": "..."}]}'
    )
    temperature = 0.7 if req.mode == "regenerate" else 0.4
    content = {"mvp_features": [], "user_stories": [], "tech_stack": []}
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
            "mvp_features": parsed.get("mvp_features", []),
            "user_stories":  parsed.get("user_stories", []),
            "tech_stack":    parsed.get("tech_stack", []),
        }
    except Exception as exc:
        logger.warning("product generate failed: %s", exc)

    feats = len(content["mvp_features"])
    summary = f"{feats} feature(s) MVP; stack: {', '.join(t.get('choice','') for t in content['tech_stack'][:3])}"
    return {"axis": SLUG, "mode": "generate", "content": content,
            "summary": summary, "assumptions": [], "needs_input": [], "citations": build_citations(req.evidence)}


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """STATE_EXISTING: compute commercial_offer score with rubric scoring, blockers, and DD."""
    profile = StartupProfile(**req.profile)

    # Score rubric text fields (value_prop_text, differentiation_text) before Affinitree.
    # On Ollama failure, rubric_scores stays empty and the numeric path degrades gracefully.
    rubric_detail: dict = {}
    degraded_rubric = False
    try:
        rubric_detail = score_profile_text_fields_detail(profile, _OLLAMA)
    except Exception as exc:
        logger.warning("rubric scoring degraded: %s", exc)
        degraded_rubric = True

    result = affinitree_score(profile, "commercial_offer")

    blockers = derive_blockers(result, SLUG)
    dd = run_due_diligence(profile, SLUG)

    justification = None
    try:
        justification = generate_justification(result, _OLLAMA, profile.language)
    except Exception as exc:
        logger.warning("justification failed: %s", exc)

    response: dict = {
        "axis": AXIS,
        "score_name": "commercial_offer",
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
