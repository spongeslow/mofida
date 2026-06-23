"""Customer Persona Simulator (Phase H, H3).

Generates evidence-grounded customer personas from the project's market/product/
brand axes + KB, then lets the founder chat with each one. Persona replies carry
``claims`` (each with a source) so the UI can footnote them. After a few
exchanges a close-strategy can be produced.
"""
from __future__ import annotations

import json
import logging

import asyncpg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .evidence_snapshot import gather_evidence
from .llm_json import generate_json
from .state_router import get_pool

router = APIRouter(tags=["persona"])
logger = logging.getLogger("moufida.persona")


def _profile_brief(ev: dict) -> dict:
    p = ev.get("profile", {})
    return {
        "sector": p.get("sector"),
        "offer": p.get("offer") or p.get("value_proposition") or p.get("raw_idea"),
        "target_market": p.get("target_market") or p.get("target_segment") or p.get("icp"),
        "pricing": p.get("pricing"),
        "scores": ev.get("scores", {}),
        "competitors": [c.get("name") for c in ev.get("competitors", [])],
    }


@router.post("/project/{project_id}/personas/generate")
async def generate_personas(project_id: str, language: str = "fr"):
    pool = await get_pool()
    try:
        ev = await gather_evidence(pool, project_id)
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    prompt = (
        "You are a market researcher building realistic CUSTOMER personas for a Tunisian "
        "startup, grounded ONLY in the evidence below. Generate 3 distinct personas.\n"
        f"Evidence (JSON):\n{json.dumps(_profile_brief(ev), ensure_ascii=False)}\n\n"
        'Respond JSON only: {"personas": [{'
        '"name": "First L.", "archetype": "short role", "age_range": "...", "region": "...", '
        '"goal": "...", "budget_range": "...", "top_objection": "...", '
        '"buying_triggers": ["...", "..."], '
        '"source_refs": {"archetype": "where this came from", "budget_range": "...", "top_objection": "..."}'
        "}]}\n"
        f"Write all human-readable text in {language}. Names should be plausibly Tunisian."
    )
    out = await generate_json(prompt, temperature=0.5, axis="persona")
    personas = out.get("personas") or []
    if not isinstance(personas, list) or not personas:
        raise HTTPException(status_code=502, detail="persona generation failed")

    # Replace any existing personas for this project.
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM customer_personas WHERE project_id = $1::uuid", project_id)
            saved = []
            for p in personas[:5]:
                if not isinstance(p, dict) or not p.get("name"):
                    continue
                pid = await conn.fetchval(
                    """INSERT INTO customer_personas (project_id, name, archetype, data)
                       VALUES ($1::uuid, $2, $3, $4::jsonb) RETURNING id""",
                    project_id, p.get("name"), p.get("archetype", ""), json.dumps(p),
                )
                p["id"] = str(pid)
                saved.append(p)
    return {"personas": saved, "evidence_refs": ev.get("weak_points", [])}


@router.get("/project/{project_id}/personas")
async def list_personas(project_id: str):
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT id, name, archetype, data FROM customer_personas
             WHERE project_id = $1::uuid ORDER BY generated_at ASC""",
        project_id,
    )
    out = []
    for r in rows:
        data = r["data"] if isinstance(r["data"], dict) else json.loads(r["data"] or "{}")
        data["id"] = str(r["id"])
        out.append(data)
    return {"personas": out, "count": len(out)}


async def _load_persona(pool, project_id: str, persona_id: str) -> dict:
    row = await pool.fetchrow(
        "SELECT data FROM customer_personas WHERE id = $1::uuid AND project_id = $2::uuid",
        persona_id, project_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="persona not found")
    return row["data"] if isinstance(row["data"], dict) else json.loads(row["data"] or "{}")


class ChatBody(BaseModel):
    message: str
    history: list[dict] = []
    language: str = "fr"


@router.post("/project/{project_id}/persona/{persona_id}/chat")
async def persona_chat(project_id: str, persona_id: str, body: ChatBody):
    pool = await get_pool()
    persona = await _load_persona(pool, project_id, persona_id)

    history = [{"role": m.get("role", "user"), "text": m.get("text", m.get("content", ""))}
               for m in body.history][-8:]
    prompt = (
        f"You ARE this customer persona (stay fully in character):\n{json.dumps(persona, ensure_ascii=False)}\n\n"
        f"Conversation so far (JSON):\n{json.dumps(history, ensure_ascii=False)}\n\n"
        f"The founder just said: \"{body.message}\"\n"
        "Reply as the persona — realistic, with the persona's concerns and budget in mind. "
        "Ground every substantive claim in the persona's own attributes.\n"
        'Respond JSON only: {"reply": "...", '
        '"claims": [{"claim": "...", "source_ref": "which persona attribute"}], '
        '"objection": "the main objection raised, or null", '
        '"buying_signal": "a positive signal if any, or null"}\n'
        f"Write in {body.language}."
    )
    out = await generate_json(prompt, temperature=0.6, axis="persona")
    return {
        "reply": out.get("reply", "…"),
        "claims": out.get("claims", []),
        "objection": out.get("objection"),
        "buying_signal": out.get("buying_signal"),
    }


class CloseBody(BaseModel):
    history: list[dict] = []
    language: str = "fr"


@router.post("/project/{project_id}/persona/{persona_id}/close-strategy")
async def close_strategy(project_id: str, persona_id: str, body: CloseBody):
    pool = await get_pool()
    persona = await _load_persona(pool, project_id, persona_id)
    history = [{"role": m.get("role", "user"), "text": m.get("text", m.get("content", ""))}
               for m in body.history][-12:]

    prompt = (
        f"Persona (JSON):\n{json.dumps(persona, ensure_ascii=False)}\n\n"
        f"Conversation (JSON):\n{json.dumps(history, ensure_ascii=False)}\n\n"
        "Produce a concrete strategy to close THIS customer.\n"
        'Respond JSON only: {"strategy": "2-3 sentence plan", '
        '"key_triggers": ["..."], "objections_to_address": ["..."]}\n'
        f"Write in {body.language}."
    )
    out = await generate_json(prompt, temperature=0.4, axis="persona")
    return {
        "strategy": out.get("strategy", ""),
        "key_triggers": out.get("key_triggers", []),
        "objections_to_address": out.get("objections_to_address", []),
    }
