"""Axis 06 -- Legal Compliance & Green. FastAPI microservice (port 8106)."""
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
    score_profile_text_fields_detail,
)

AXIS = 6
SLUG = "legal"
app = FastAPI(title="Moufida Axis 06 - Legal Compliance & Green")
logger = logging.getLogger("moufida.legal")

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
    """Creation mode: generate a structured Legal & Compliance proposal."""
    upstream_idea = req.upstream.get("ideation", {}).get("refined_idea", req.idea)
    upstream_bm = req.upstream.get("business-model", {})
    constraints_block = f"\nConstraints: {req.constraints}" if req.constraints else ""
    prompt = (
        f"You are a legal expert for startups in Tunisia. Generate a Legal plan section.\n"
        f"Language for output: {req.language}\n\n"
        f"STARTUP IDEA: {upstream_idea}\n"
        f"BUSINESS MODEL: {upstream_bm}\n"
        f"{constraints_block}\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"legal_structure": "...", "ip_strategy": "...", "regulatory": ["...", "..."]}'
    )
    temperature = 0.7 if req.mode == "regenerate" else 0.4
    content = {"legal_structure": "", "ip_strategy": "", "regulatory": []}
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
            "legal_structure": str(parsed.get("legal_structure", "")),
            "ip_strategy":     str(parsed.get("ip_strategy", "")),
            "regulatory":      parsed.get("regulatory", []),
        }
    except Exception as exc:
        logger.warning("legal generate failed: %s", exc)

    summary = f"Structure: {content['legal_structure'][:60]}; IP: {content['ip_strategy'][:60]}"
    return {"axis": SLUG, "mode": "generate", "content": content,
            "summary": summary, "assumptions": [], "needs_input": [], "citations": build_citations(req.evidence)}


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """STATE_EXISTING: compute green score with SDG rubric scoring, blockers, and DD."""
    profile = StartupProfile(**req.profile)

    # Score rubric text field (sdg_alignment_text).
    rubric_detail: dict = {}
    degraded_rubric = False
    try:
        rubric_detail = score_profile_text_fields_detail(profile, _OLLAMA)
    except Exception as exc:
        logger.warning("rubric scoring degraded: %s", exc)
        degraded_rubric = True

    result = affinitree_score(profile, "green")

    blockers = derive_blockers(result, SLUG)
    dd = run_due_diligence(profile, SLUG)

    justification = None
    try:
        justification = generate_justification(result, _OLLAMA, profile.language)
    except Exception as exc:
        logger.warning("justification failed: %s", exc)

    response: dict = {
        "axis": AXIS,
        "score_name": "green",
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
    """Receive a legal/regulatory signal from the Go daemon and push an SSE alert."""
    metric_type = payload.get("type")
    project_id = payload.get("project_id", "")
    value = payload.get("value", {})
    logger.info("metric_update axis=%s type=%s project_id=%s", AXIS, metric_type, project_id)

    if metric_type == "legal":
        src = value.get("source", "")
        title = value.get("title", "")
        keywords = value.get("keywords_matched", [])
        kw_str = ", ".join(keywords) if keywords else ""
        msg = f"Nouvelle réglementation [{src}] : {title}" + (f" (mots-clés : {kw_str})" if kw_str else "")
        await _push_alert(project_id, "legal", "warning", msg)

    return {"axis": AXIS, "status": "ok"}
