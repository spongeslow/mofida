"""Axis 01 -- Ideation. FastAPI microservice (port 8101)."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, ValidationError
from affinitree import build_citations, format_evidence_block
from affinitree.profile import StartupProfile

AXIS = 1
SLUG = "ideation"
app = FastAPI(title="Moufida Axis 01 - Ideation")

logger = logging.getLogger("moufida.ideation")

OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
OLLAMA_MODEL = os.environ["OLLAMA_MODEL"]
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))

STAGES = [
    "Ideation",
    "Market Validation",
    "Structuration",
    "Fundraising",
    "Launch Planning",
    "Growth",
]

PROMPT_TEMPLATE = (
    "Based on the following startup profile, assign exactly one maturity stage "
    "from [Ideation, Market Validation, Structuration, Fundraising, Launch Planning, Growth]. "
    "List 3–5 specific evidence points from the profile that justify this classification. "
    "Respond in JSON with keys: stage, confidence (0.0–1.0), evidence (list of strings).\n\n"
    "Startup profile:\n{profile_json}"
)


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


def _build_ideation_prompt(req: GenerateRequest) -> str:
    lang = req.language
    constraints_block = f"\nConstraints from founder: {req.constraints}" if req.constraints else ""
    return (
        f"You are a startup strategy expert. Generate an Ideation plan section for this startup idea.\n"
        f"Language for output: {lang}\n\n"
        f"FOUNDER'S IDEA:\n{req.idea}\n"
        f"{constraints_block}\n\n"
        "Respond ONLY with valid JSON matching this exact structure:\n"
        '{"refined_idea": "...", "vision": "...", "problem": "...", "solution_fit": "...", "positioning": "..."}'
    )


def _default_ideation_content() -> dict:
    return {
        "refined_idea": req_idea_placeholder,
        "vision": "",
        "problem": "",
        "solution_fit": "",
        "positioning": "",
    }


@app.post("/generate")
async def generate(req: GenerateRequest):
    """Creation mode: generate a structured Ideation proposal from a raw idea."""
    temperature = 0.7 if req.mode == "regenerate" else 0.4
    prompt = _build_ideation_prompt(req)
    content = {"refined_idea": req.idea, "vision": "", "problem": "", "solution_fit": "", "positioning": ""}
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": format_evidence_block(req.evidence) + prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": temperature},
                },
            )
            if not resp.is_success:
                logger.warning("ollama %s: %s", resp.status_code, resp.text[:400])
                resp.raise_for_status()
            raw = resp.json().get("response", "")
        parsed = _parse_llm_json(raw)
        content = {
            "refined_idea": str(parsed.get("refined_idea", req.idea)),
            "vision":       str(parsed.get("vision", "")),
            "problem":      str(parsed.get("problem", "")),
            "solution_fit": str(parsed.get("solution_fit", "")),
            "positioning":  str(parsed.get("positioning", "")),
        }
    except Exception as exc:
        logger.warning("ideation generate failed: %s", exc)

    summary = content["refined_idea"][:120] if content["refined_idea"] else req.idea[:120]
    return {
        "axis": SLUG,
        "mode": "generate",
        "content": content,
        "summary": summary,
        "assumptions": [],
        "needs_input": [],
        "citations": build_citations(req.evidence),
    }


def _self_assessed_stage(profile: StartupProfile) -> Optional[str]:
    """Return the self-declared stage if the profile carries one.

    The current schema exposes it directly on the profile; a ``meta`` block is
    also tolerated for forward compatibility."""
    meta = getattr(profile, "meta", None)
    if meta is not None:
        declared = getattr(meta, "self_assessed_stage", None)
        if declared is not None:
            return declared
    return getattr(profile, "self_assessed_stage", None)


def _parse_llm_json(raw: str) -> dict[str, Any]:
    """Parse the model's JSON output, tolerating surrounding prose/fences."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Salvage the first {...} block if the model wrapped it in prose.
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
    raise ValueError("no parseable JSON object in model output")


def _normalise(parsed: dict[str, Any]) -> dict[str, Any]:
    """Coerce a parsed LLM dict into the contract's stage/confidence/evidence."""
    stage = parsed.get("stage")
    stage = stage if stage in STAGES else (str(stage) if stage else "Ideation")

    try:
        confidence = float(parsed.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    evidence = parsed.get("evidence", [])
    if isinstance(evidence, str):
        evidence = [evidence]
    elif not isinstance(evidence, list):
        evidence = []
    evidence = [str(e) for e in evidence]

    return {"stage": stage, "confidence": confidence, "evidence": evidence}


def _extract(payload: dict) -> tuple[StartupProfile, str, Optional[str]]:
    """Normalise the request body into (profile, description, declared_stage).

    Accepts three shapes for cross-service consistency: a bare StartupProfile, the
    orchestrator's ``{"profile": ...}`` wrapper, and an eval payload carrying a
    free-text ``meta.description`` / ``meta.self_assessed_stage``. Unknown keys are
    dropped before constructing the typed model so validation never fails."""
    body = payload if isinstance(payload, dict) else {}
    raw = body.get("profile") if isinstance(body.get("profile"), dict) else body
    raw = raw or {}
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    description = str(meta.get("description") or raw.get("description") or "")
    declared = meta.get("self_assessed_stage") or raw.get("self_assessed_stage")
    known = {k: v for k, v in raw.items() if k in StartupProfile.model_fields}
    try:
        profile = StartupProfile(**known)
    except ValidationError:
        profile = StartupProfile()
    return profile, description, declared


@app.post("/diagnose")
async def diagnose(payload: dict | None = None):
    """STATE_EXISTING: classify the startup's maturity stage via Mistral 7B."""
    profile, description, declared = _extract(payload or {})
    context = profile.model_dump_json()
    if description:
        context = f"Founder description: {description}\n\nStructured profile: {context}"
    prompt = PROMPT_TEMPLATE.format(profile_json=context)

    result = {"stage": "Ideation", "confidence": 0.0, "evidence": []}
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
            )
            if not resp.is_success:
                logger.warning("ollama %s: %s", resp.status_code, resp.text[:400])
                resp.raise_for_status()
            raw = resp.json().get("response", "")
        result = _normalise(_parse_llm_json(raw))
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("ideation diagnose: falling back to default classification: %s", exc)

    result["self_assessed_stage"] = declared or _self_assessed_stage(profile)
    return result


@app.post("/metric_update")
def metric_update(payload: dict):
    """Receive a Go-daemon milestone signal routed by the orchestrator (Phase 5).

    Expected shape: ``{"type": "milestone", "value": Any, "project_id": str}``."""
    logger.info(
        "metric_update axis=%s type=%s project_id=%s value=%r",
        AXIS,
        payload.get("type"),
        payload.get("project_id"),
        payload.get("value"),
    )
    return {"status": "received"}
