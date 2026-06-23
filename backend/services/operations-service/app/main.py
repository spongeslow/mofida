"""Axis 09 -- Operations. FastAPI microservice (port 8109)."""
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
)

AXIS = 9
SLUG = "operations"
app = FastAPI(title="Moufida Axis 09 - Operations")
logger = logging.getLogger("moufida.operations")

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
    """Creation mode: generate a structured Operations proposal."""
    import httpx as _httpx
    upstream_idea = req.upstream.get("ideation", {}).get("refined_idea", req.idea)
    upstream_bm = req.upstream.get("business-model", {})
    constraints_block = f"\nConstraints: {req.constraints}" if req.constraints else ""
    prompt = (
        f"You are an operations expert. Generate an Operations plan section for a startup.\n"
        f"Language for output: {req.language}\n\n"
        f"STARTUP IDEA: {upstream_idea}\n"
        f"BUSINESS MODEL: {upstream_bm}\n"
        f"{constraints_block}\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"team": [{"role": "...", "responsibilities": "...", "hire_by": "..."}], '
        '"processes": ["..."], "tools": ["..."], '
        '"timeline": [{"milestone": "...", "target": "..."}]}'
    )
    temperature = 0.7 if req.mode == "regenerate" else 0.4
    content = {"team": [], "processes": [], "tools": [], "timeline": []}
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
            "team":      parsed.get("team", []),
            "processes": parsed.get("processes", []),
            "tools":     parsed.get("tools", []),
            "timeline":  parsed.get("timeline", []),
        }
    except Exception as exc:
        logger.warning("operations generate failed: %s", exc)

    roles = len(content["team"])
    summary = f"{roles} rôle(s) clé(s); {len(content['timeline'])} jalons"
    return {"axis": SLUG, "mode": "generate", "content": content,
            "summary": summary, "assumptions": [], "needs_input": [], "citations": build_citations(req.evidence)}


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """STATE_EXISTING: compute scalability/ops score with blockers and DD."""
    profile = StartupProfile(**req.profile)
    result = affinitree_score(profile, "scalability")

    blockers = derive_blockers(result, SLUG)
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
        "blockers": blockers,
        "due_diligence": dd,
        "justification": justification,
    }


@app.post("/metric_update")
def metric_update(payload: dict):
    """Receive a milestone signal from the Go daemon (Phase 5)."""
    logger.info("metric_update axis=%s type=%s", AXIS, payload.get("type"))
    return {"axis": AXIS, "received": payload, "status": "not_implemented"}
