"""Investor Pitch Simulator (Phase H, H1).

An AI investor persona challenges the founder using questions grounded ONLY in
their own diagnostic evidence (scores, blockers, competitors, opportunities,
concept bottlenecks). Every question ships with an EvidenceTrace. The session
ends with a readiness report.
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

router = APIRouter(tags=["pitch"])
logger = logging.getLogger("moufida.pitch")

INVESTOR_PROFILES = {
    "seed_vc": "a sharp Seed-stage VC who probes traction, market size, defensibility and unit economics",
    "angel": "a pragmatic angel investor who probes the founder, the problem, and early customer validation",
    "impact_fund": "an impact-fund partner who probes social/environmental outcomes alongside financial returns",
    "strategic": "a strategic corporate investor who probes market fit, defensibility, and integration risk",
}


def _persona(profile: str) -> str:
    return INVESTOR_PROFILES.get(profile, INVESTOR_PROFILES["seed_vc"])


def _evidence_for_prompt(ev: dict) -> dict:
    """Compact projection of the evidence snapshot for the LLM prompt."""
    return {
        "scores": ev.get("scores", {}),
        "maturity_stage": ev.get("maturity_stage"),
        "weak_points": [
            {k: v for k, v in wp.items() if k in ("label", "field", "value", "detail")}
            for wp in ev.get("weak_points", [])
        ],
        "competitors": [c.get("name") for c in ev.get("competitors", [])],
        "opportunities": [o.get("title") for o in ev.get("opportunities", [])],
    }


def _trace_for(ev: dict, focus: str | None) -> list[dict]:
    """Pick the evidence refs most relevant to the question's focus."""
    wps = ev.get("weak_points", [])
    if focus:
        f = focus.lower()
        hit = [w for w in wps if f in (w.get("label", "").lower())]
        if hit:
            return hit[:3]
    return wps[:3]


async def _load_session(pool, project_id: str, session_id: str) -> dict:
    row = await pool.fetchrow(
        "SELECT id, investor_profile, exchanges, evidence FROM pitch_sessions "
        "WHERE id = $1::uuid AND project_id = $2::uuid",
        session_id, project_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="pitch session not found")
    return {
        "id": str(row["id"]),
        "investor_profile": row["investor_profile"],
        "exchanges": row["exchanges"] if isinstance(row["exchanges"], list)
                     else json.loads(row["exchanges"] or "[]"),
        "evidence": row["evidence"] if isinstance(row["evidence"], dict)
                    else json.loads(row["evidence"] or "{}"),
    }


class StartBody(BaseModel):
    investor_profile: str = "seed_vc"
    language: str = "fr"


@router.post("/project/{project_id}/pitch/start")
async def pitch_start(project_id: str, body: StartBody):
    pool = await get_pool()
    try:
        ev = await gather_evidence(pool, project_id)
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    persona = _persona(body.investor_profile)
    prompt = (
        f"You are {persona}, interviewing a Tunisian startup founder.\n"
        f"Founder's diagnostic evidence (JSON):\n{json.dumps(_evidence_for_prompt(ev), ensure_ascii=False)}\n\n"
        "Ask ONE tough but fair OPENING question, grounded ONLY in this evidence — "
        "target the weakest area. Do not invent facts.\n"
        'Respond JSON only: {"question": "...", "reasoning": "why, referencing the evidence", '
        '"focus_axis": "<the score/axis you targeted>"}\n'
        f"Write the question and reasoning in {body.language}."
    )
    out = await generate_json(prompt, temperature=0.3, axis="pitch")
    question = out.get("question") or "Tell me about your traction so far — what evidence do you have that customers want this?"
    reasoning = out.get("reasoning", "")
    trace = _trace_for(ev, out.get("focus_axis"))

    opening = {"role": "investor", "text": question, "reasoning": reasoning, "trace": trace}
    session_id = await pool.fetchval(
        """INSERT INTO pitch_sessions (project_id, investor_profile, exchanges, evidence)
           VALUES ($1::uuid, $2, $3::jsonb, $4::jsonb) RETURNING id""",
        project_id, body.investor_profile, json.dumps([opening]), json.dumps(ev),
    )
    return {"session_id": str(session_id), "opening_question": question,
            "reasoning": reasoning, "trace": trace}


class RespondBody(BaseModel):
    session_id: str
    answer: str
    language: str = "fr"


@router.post("/project/{project_id}/pitch/respond")
async def pitch_respond(project_id: str, body: RespondBody):
    pool = await get_pool()
    session = await _load_session(pool, project_id, body.session_id)
    ev = session["evidence"]
    persona = _persona(session["investor_profile"])

    transcript = [
        {"role": e["role"], "text": e["text"]} for e in session["exchanges"]
    ]
    transcript.append({"role": "founder", "text": body.answer})

    prompt = (
        f"You are {persona} continuing a pitch interview.\n"
        f"Evidence (JSON):\n{json.dumps(_evidence_for_prompt(ev), ensure_ascii=False)}\n\n"
        f"Transcript so far (JSON):\n{json.dumps(transcript, ensure_ascii=False)}\n\n"
        "Judge the founder's last answer. If it was weak or evasive, push harder; if strong, "
        "probe the next weakest area. Stay grounded ONLY in the evidence.\n"
        'Respond JSON only: {"question": "...", "reasoning": "...", "focus_axis": "...", '
        '"answer_quality": "strong|weak|evasive"}\n'
        f"Write in {body.language}."
    )
    out = await generate_json(prompt, temperature=0.35, axis="pitch")
    question = out.get("question") or "Can you be more specific, with numbers?"
    reasoning = out.get("reasoning", "")
    quality = out.get("answer_quality", "")
    trace = _trace_for(ev, out.get("focus_axis"))

    exchanges = session["exchanges"]
    exchanges.append({"role": "founder", "text": body.answer})
    exchanges.append({"role": "investor", "text": question, "reasoning": reasoning,
                      "trace": trace, "answer_quality": quality})
    await pool.execute(
        "UPDATE pitch_sessions SET exchanges = $1::jsonb WHERE id = $2::uuid",
        json.dumps(exchanges), body.session_id,
    )
    return {"follow_up_question": question, "reasoning": reasoning,
            "trace": trace, "answer_quality": quality}


class EndBody(BaseModel):
    session_id: str
    language: str = "fr"


@router.post("/project/{project_id}/pitch/end")
async def pitch_end(project_id: str, body: EndBody):
    pool = await get_pool()
    session = await _load_session(pool, project_id, body.session_id)
    ev = session["evidence"]
    persona = _persona(session["investor_profile"])
    transcript = [{"role": e["role"], "text": e["text"]} for e in session["exchanges"]]

    prompt = (
        f"You are {persona}. Assess the founder's pitch readiness from the transcript and evidence.\n"
        f"Evidence (JSON):\n{json.dumps(_evidence_for_prompt(ev), ensure_ascii=False)}\n\n"
        f"Transcript (JSON):\n{json.dumps(transcript, ensure_ascii=False)}\n\n"
        'Respond JSON only: {"overall_readiness": <0-100 integer>, '
        '"per_axis_readiness": {"<axis>": {"score": <0-100>, "gaps": ["..."]}}, '
        '"hardest_questions": ["..."], "recommended_actions": ["..."]}\n'
        f"Write all text in {body.language}."
    )
    out = await generate_json(prompt, temperature=0.3, axis="pitch")

    # Deterministic fallback / backfill from the diagnostic scores.
    scores = ev.get("scores", {})
    if not out.get("per_axis_readiness") and scores:
        out["per_axis_readiness"] = {
            name: {"score": round(score / 5 * 100), "gaps": []}
            for name, score in scores.items()
        }
    if out.get("overall_readiness") is None:
        if scores:
            out["overall_readiness"] = round(sum(scores.values()) / len(scores) / 5 * 100)
        else:
            out["overall_readiness"] = 0
    out.setdefault("hardest_questions",
                   [e["text"] for e in session["exchanges"] if e["role"] == "investor"][:5])
    out.setdefault("recommended_actions", [])
    out["evidence_used"] = ev.get("weak_points", [])

    await pool.execute(
        "UPDATE pitch_sessions SET readiness = $1::jsonb, ended_at = now() WHERE id = $2::uuid",
        json.dumps(out), body.session_id,
    )
    return out
