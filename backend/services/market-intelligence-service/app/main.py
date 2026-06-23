"""Axis 02 -- Market Intelligence. FastAPI microservice (port 8102)."""
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

AXIS = 2
SLUG = "market"
app = FastAPI(title="Moufida Axis 02 - Market Intelligence")
logger = logging.getLogger("moufida.market")

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
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            try:
                return _json.loads(raw[start:end + 1])
            except Exception:
                pass
    return {}


def _build_market_prompt(req: GenerateRequest) -> str:
    upstream_idea = req.upstream.get("ideation", {}).get("refined_idea", req.idea)
    constraints_block = f"\nConstraints: {req.constraints}" if req.constraints else ""
    return (
        f"You are a market research expert. Generate a Market Analysis plan section.\n"
        f"Language for output: {req.language}\n\n"
        f"STARTUP IDEA: {upstream_idea}\n"
        f"{constraints_block}\n\n"
        "Respond ONLY with valid JSON matching this exact structure:\n"
        '{"segments": [{"name": "...", "size_estimate": "...", "pain_point": "..."}], '
        '"market_size": {"tam": "...", "sam": "...", "som": "..."}, '
        '"competitors": [{"name": "...", "strength": "...", "weakness": "..."}], '
        '"differentiation": "..."}'
    )


@app.post("/generate")
def generate(req: GenerateRequest):
    """Creation mode: generate a structured Market Analysis proposal."""
    import httpx as _httpx
    temperature = 0.7 if req.mode == "regenerate" else 0.4
    content = {"segments": [], "market_size": {}, "competitors": [], "differentiation": ""}
    try:
        resp = _httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": format_evidence_block(req.evidence) + _build_market_prompt(req),
                  "stream": False, "format": "json", "options": {"temperature": temperature}},
            timeout=OLLAMA_TIMEOUT,
        )
        if not resp.is_success:
            logger.warning("ollama %s: %s", resp.status_code, resp.text[:400])
            resp.raise_for_status()
        parsed = _parse_gen_json(resp.json().get("response", ""))
        content = {
            "segments":        parsed.get("segments", []),
            "market_size":     parsed.get("market_size", {}),
            "competitors":     parsed.get("competitors", []),
            "differentiation": str(parsed.get("differentiation", "")),
        }
    except Exception as exc:
        logger.warning("market generate failed: %s", exc)

    segs = len(content["segments"])
    summary = f"{segs} segment(s) identifié(s); {content['differentiation'][:80]}"
    return {"axis": SLUG, "mode": "generate", "content": content,
            "summary": summary, "assumptions": [], "needs_input": [], "citations": build_citations(req.evidence)}


@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    """STATE_EXISTING: compute market score, blockers, and investor DD checks."""
    profile = StartupProfile(**req.profile)
    result = affinitree_score(profile, "market")

    blockers = derive_blockers(result, SLUG)
    dd = run_due_diligence(profile, SLUG)

    justification = None
    try:
        justification = generate_justification(result, _OLLAMA, profile.language)
    except Exception as exc:
        logger.warning("justification failed: %s", exc)

    return {
        "axis": AXIS,
        "score_name": "market",
        "score": result.score,
        "explanation": result.explanation_tree(),
        "missing_fields": result.missing_fields,
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
    """Receive a competitor or trend signal from the Go daemon and push an SSE alert."""
    metric_type = payload.get("type")
    project_id = payload.get("project_id", "")
    value = payload.get("value", {})
    logger.info("metric_update axis=%s type=%s project_id=%s", AXIS, metric_type, project_id)

    if metric_type == "competitor":
        name = value.get("name", "")
        event = value.get("event", "page_changed")
        headline = value.get("headline", "")
        if event == "news_mention":
            msg = f"Competitor '{name}' mentionné dans l'actualité : {headline}"
        else:
            msg = f"Site concurrent modifié : '{name}'"
        await _push_alert(project_id, "competitor", "warning", msg)

    elif metric_type == "trend":
        kw = value.get("keyword", "")
        change_pct = value.get("change_pct", 0)
        direction = value.get("direction", "up")
        msg = f"Tendance marché : '{kw}' {direction} de {abs(change_pct):.0f}%"
        await _push_alert(project_id, "trend", "info", msg)

    return {"axis": AXIS, "status": "ok"}
