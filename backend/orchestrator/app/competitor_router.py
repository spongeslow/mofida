"""Competitor analysis board — ingest daemon page observations, LLM-extract
structured competitive data, diff against the last snapshot, regenerate SWOT.

The Go daemon POSTs trimmed competitor page text / news headlines to
``/project/{id}/competitor/observe``; this router turns that into persisted,
structured rows that the dashboard renders as a comparison board.
"""
from __future__ import annotations

import json
import logging

import asyncpg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import sse
from .llm_json import generate_json
from .state_router import get_pool

router = APIRouter()
logger = logging.getLogger("moufida.competitor_router")


def _parse_jsonb(val):
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {}
    return val if val is not None else {}


class ObserveBody(BaseModel):
    name: str
    url: str | None = None
    raw_text: str = ""
    source: str = "page_changed"   # 'page_changed' | 'news_mention'
    headline: str | None = None


async def _load_profile(pool: asyncpg.Pool, project_id: str) -> dict:
    row = await pool.fetchrow(
        "SELECT profile FROM profiles WHERE id = $1::uuid", project_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="project not found")
    return _parse_jsonb(row["profile"])


async def _extract_competitor(name: str, raw_text: str) -> dict:
    """LLM-extract pricing tiers, one-line positioning, and any funding mention."""
    if not raw_text.strip():
        return {}
    prompt = (
        f"You are a competitive-intelligence analyst. From the following web page text "
        f"about the company \"{name}\", extract structured data.\n\n"
        f"PAGE TEXT (may be noisy):\n{raw_text[:6000]}\n\n"
        "Respond ONLY with valid JSON matching exactly:\n"
        '{"pricing": {"tiers": [{"name": "...", "price": "...", "features": ["..."]}]}, '
        '"positioning": "one concise sentence", '
        '"funding": {"stage": "...", "amount": "...", "investors": ["..."]}}\n'
        "Use empty values when unknown; never invent numbers."
    )
    return await generate_json(prompt, temperature=0.2)


async def _generate_swot(name: str, profile: dict, competitor: dict) -> dict:
    """Regenerate SWOT for a competitor relative to this project."""
    prompt = (
        "You are a startup strategist. Produce a SWOT analysis of the competitor "
        f"\"{name}\" from the perspective of THIS startup.\n\n"
        f"OUR PROFILE: {json.dumps(profile, ensure_ascii=False)[:2500]}\n"
        f"COMPETITOR DATA: {json.dumps(competitor, ensure_ascii=False)[:2500]}\n\n"
        "Respond ONLY with valid JSON matching exactly:\n"
        '{"strengths": ["..."], "weaknesses": ["..."], '
        '"opportunities": ["..."], "threats": ["..."]}'
    )
    return await generate_json(prompt, temperature=0.3)


def _diff_extraction(before: dict, after: dict) -> dict:
    """Field-level diff between two extractions (pricing/positioning/funding)."""
    diff: dict = {}
    for field in ("pricing", "positioning", "funding"):
        b, a = before.get(field), after.get(field)
        if a and a != b:
            diff[field] = {"before": b, "after": a}
    return diff


@router.post("/project/{project_id}/competitor/observe")
async def observe_competitor(project_id: str, body: ObserveBody):
    """Daemon hook: a competitor page changed or was mentioned in the news."""
    pool = await get_pool()
    profile = await _load_profile(pool, project_id)

    # --- 1. Upsert the competitor row (by project_id + name). ---
    try:
        comp_row = await pool.fetchrow(
            """
            INSERT INTO competitors (project_id, name, url)
            VALUES ($1::uuid, $2, $3)
            ON CONFLICT (project_id, name)
            DO UPDATE SET url = COALESCE(EXCLUDED.url, competitors.url),
                          updated_at = now()
            RETURNING id, pricing, positioning, funding
            """,
            project_id, body.name, body.url,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    competitor_id = comp_row["id"]
    prev = {
        "pricing":     _parse_jsonb(comp_row["pricing"]),
        "positioning": comp_row["positioning"],
        "funding":     _parse_jsonb(comp_row["funding"]),
    }

    # --- News path: prepend the headline (cap at 20), no heavy extraction. ---
    if body.source == "news_mention":
        from datetime import date
        news_row = await pool.fetchval(
            "SELECT news FROM competitors WHERE id = $1::uuid", competitor_id
        )
        news = _parse_jsonb(news_row)
        if not isinstance(news, list):
            news = []
        entry = {"headline": body.headline or body.name, "url": body.url,
                 "date": date.today().isoformat()}
        news = [entry, *news][:20]
        await pool.execute(
            "UPDATE competitors SET news = $2::jsonb, updated_at = now() WHERE id = $1::uuid",
            competitor_id, json.dumps(news),
        )
        await sse.push_event(project_id, "competitor_update",
                             {"name": body.name, "diff": {}})
        return {"competitor_id": str(competitor_id), "source": "news_mention"}

    # --- Page-changed path: extract, diff, snapshot, regenerate SWOT. ---
    extracted = await _extract_competitor(body.name, body.raw_text)
    new_state = {
        "pricing":     extracted.get("pricing") or prev["pricing"],
        "positioning": extracted.get("positioning") or prev["positioning"],
        "funding":     extracted.get("funding") or prev["funding"],
    }
    diff = _diff_extraction(prev, new_state)

    swot = await _generate_swot(body.name, profile, new_state)

    await pool.execute(
        """
        UPDATE competitors
           SET pricing = $2::jsonb, positioning = $3, funding = $4::jsonb,
               swot = $5::jsonb, updated_at = now()
         WHERE id = $1::uuid
        """,
        competitor_id,
        json.dumps(new_state["pricing"]),
        new_state["positioning"],
        json.dumps(new_state["funding"]),
        json.dumps(swot),
    )

    await pool.execute(
        """
        INSERT INTO competitor_snapshots (competitor_id, raw_excerpt, diff)
        VALUES ($1::uuid, $2, $3::jsonb)
        """,
        competitor_id, body.raw_text[:6000], json.dumps(diff),
    )

    await sse.push_event(project_id, "competitor_update",
                         {"name": body.name, "diff": diff})
    try:
        from . import telemetry
        await telemetry.record_daemon_activity(
            project_id=project_id, watcher="competitor", activity="page_changed",
            detail={"name": body.name, "diff_keys": list(diff.keys()) if isinstance(diff, dict) else []},
        )
    except Exception:  # noqa: BLE001
        pass
    return {"competitor_id": str(competitor_id), "diff": diff, "source": "page_changed"}


@router.get("/project/{project_id}/competitors")
async def list_competitors(project_id: str):
    """Board data: every tracked competitor + a synthesised 'you' row."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT id, name, url, pricing, positioning, funding, news, swot, updated_at
              FROM competitors
             WHERE project_id = $1::uuid
             ORDER BY updated_at DESC
            """,
            project_id,
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    profile = await _load_profile(pool, project_id)

    # Synthesise the project's own positioning row from the market/product plan.
    own_positioning = ""
    market = profile.get("market") if isinstance(profile.get("market"), dict) else {}
    offer = profile.get("offer") if isinstance(profile.get("offer"), dict) else {}
    if isinstance(offer, dict):
        own_positioning = offer.get("value_prop_text") or ""
    if not own_positioning and isinstance(market, dict):
        own_positioning = market.get("differentiation") or ""

    return {
        "you": {
            "name":        profile.get("name") or "Vous",
            "positioning": own_positioning,
            "is_you":      True,
        },
        "competitors": [
            {
                "id":          str(r["id"]),
                "name":        r["name"],
                "url":         r["url"],
                "pricing":     _parse_jsonb(r["pricing"]),
                "positioning": r["positioning"],
                "funding":     _parse_jsonb(r["funding"]),
                "news":        _parse_jsonb(r["news"]),
                "swot":        _parse_jsonb(r["swot"]),
                "updated_at":  r["updated_at"].isoformat(),
            }
            for r in rows
        ],
    }
