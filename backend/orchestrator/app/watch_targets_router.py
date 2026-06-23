"""Adaptive watch-targets — what the daemon should monitor for a project.

Two tiers:
  1. Deterministic seeds (``_sector_seeds``) — a sector→sources floor that mirrors
     the daemon's ``derive.go`` so ``GET /watch-targets`` is always safe to call.
  2. LLM-enriched, cached targets — niche-specific feeds / regulators / keywords
     derived from the *full* profile, cached by ``profile_hash`` so we re-derive
     only when the profile changes. Optionally grounded via the RAG web_search.

The daemon GETs the merged view and unions it with its own ``derive.go`` seeds.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os

import asyncpg
import httpx
from fastapi import APIRouter, HTTPException

from . import sse
from .llm_json import generate_json
from .state_router import get_pool

router = APIRouter()
logger = logging.getLogger("moufida.watch_targets_router")

RAG_URL = os.getenv("RAG_URL", "")

# Universal feeds every sector watches (mirror of derive.go sectorNewsFeeds base).
_BASE_FEEDS = [
    "https://www.wamda.com/feed",
    "https://technewsafrica.com/feed",
]
_SECTOR_FEEDS = {
    "agri-food":    ["https://www.agenceecofin.com/rss"],
    "digital-tech": ["https://techcrunch.com/feed", "https://disrupt-africa.com/feed"],
    "industry":     ["https://www.agenceecofin.com/rss", "https://www.africanews.com/rss"],
}
_BASE_LEGAL = [
    {"name": "JORT", "url": "http://www.iort.gov.tn/WD120AWP/WD120Awp.exe/CONNECT/IORT_INTERNET"},
]
_SECTOR_LEGAL = {
    "agri-food": [
        {"name": "MARHP", "url": "http://www.agriculture.tn.gov/"},
        {"name": "ONAGRI", "url": "http://www.onagri.nat.tn/"},
    ],
    "digital-tech": [
        {"name": "EUR-Lex GDPR", "url": "https://eur-lex.europa.eu/legal-content/FR/LSU/?uri=CELEX:32016R0679"},
        {"name": "INNORPI", "url": "https://www.innorpi.tn"},
    ],
    "industry": [
        {"name": "INNORPI", "url": "https://www.innorpi.tn"},
        {"name": "CETIME", "url": "https://www.cetime.ind.tn"},
    ],
}
_DEFAULT_LEGAL = [
    {"name": "EUR-Lex GDPR", "url": "https://eur-lex.europa.eu/legal-content/FR/LSU/?uri=CELEX:32016R0679"},
    {"name": "INNORPI", "url": "https://www.innorpi.tn"},
]


def _parse_jsonb(val):
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return []
    return val if val is not None else []


def _sector_seeds(sector: str) -> dict:
    feeds = [*_BASE_FEEDS, *_SECTOR_FEEDS.get(sector, ["https://www.africanews.com/rss"])]
    legal = [*_BASE_LEGAL, *_SECTOR_LEGAL.get(sector, _DEFAULT_LEGAL)]
    return {
        "feeds":         [{"url": u, "why": "sector seed"} for u in feeds],
        "legal_sources": legal,
        "keywords":      [sector] if sector and sector != "cross-sector" else [],
        "competitors":   [],
    }


def _profile_hash(profile: dict, sector: str) -> str:
    """Stable hash over the fields fed to the LLM prompt."""
    blob = json.dumps(
        {
            "sector": sector,
            "offer": profile.get("offer"),
            "innovation": profile.get("innovation"),
            "market": profile.get("market"),
        },
        sort_keys=True, ensure_ascii=False, default=str,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _merge(seeds: dict, stored: dict) -> dict:
    """Union seeds with stored LLM targets, deduping by url / name / keyword."""
    def dedup_by(items, key):
        seen, out = set(), []
        for it in items:
            k = (it.get(key) or "").strip().lower() if isinstance(it, dict) else str(it).lower()
            if k and k not in seen:
                seen.add(k)
                out.append(it)
        return out

    return {
        "feeds":         dedup_by([*seeds["feeds"], *_parse_jsonb(stored.get("feeds"))], "url"),
        "legal_sources": dedup_by([*seeds["legal_sources"], *_parse_jsonb(stored.get("legal_sources"))], "url"),
        "keywords":      _dedup_str([*seeds["keywords"], *_parse_jsonb(stored.get("keywords"))]),
        "competitors":   dedup_by([*seeds["competitors"], *_parse_jsonb(stored.get("competitors"))], "name"),
    }


def _dedup_str(items) -> list[str]:
    seen, out = set(), []
    for it in items:
        s = str(it).strip().lower()
        if s and s not in seen:
            seen.add(s)
            out.append(str(it).strip())
    return out


async def _load(pool: asyncpg.Pool, project_id: str):
    row = await pool.fetchrow(
        "SELECT profile, sector FROM profiles WHERE id = $1::uuid", project_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="project not found")
    profile = row["profile"]
    if isinstance(profile, str):
        profile = json.loads(profile or "{}")
    return profile or {}, (row["sector"] or "cross-sector")


async def _stored_targets(pool: asyncpg.Pool, project_id: str) -> dict:
    row = await pool.fetchrow(
        """SELECT feeds, legal_sources, keywords, competitors, profile_hash
             FROM project_watch_targets WHERE project_id = $1::uuid""",
        project_id,
    )
    return dict(row) if row else {}


async def _ground_feeds(sector: str, keywords: list[str]) -> list[dict]:
    """Best-effort: ask the RAG web_search for fresh sources for this niche."""
    if not RAG_URL or not keywords:
        return []
    query = f"{sector} {' '.join(keywords[:4])} Tunisie actualités RSS"
    try:
        async with httpx.AsyncClient(timeout=15.0) as http:
            resp = await http.post(
                f"{RAG_URL}/web_search",
                json={"query": query, "top_k": 3, "language": "fr"},
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
    except Exception as exc:
        logger.info("watch-targets grounding skipped: %s", exc)
        return []
    return [{"url": r["url"], "why": f"web: {r.get('title', '')[:80]}"}
            for r in results if r.get("url")]


@router.post("/project/{project_id}/watch-targets/refresh")
async def refresh_watch_targets(project_id: str):
    """Re-derive LLM watch targets (cached by profile_hash) and persist them."""
    pool = await get_pool()
    profile, sector = await _load(pool, project_id)
    phash = _profile_hash(profile, sector)

    stored = await _stored_targets(pool, project_id)
    if stored.get("profile_hash") == phash:
        # Profile unchanged → no LLM call, return the cached merged view.
        return {"refreshed": False, **_merge(_sector_seeds(sector), stored)}

    prompt = (
        "You are a market-intelligence analyst for a Tunisian startup. Based on the "
        "profile below, propose niche-specific monitoring targets.\n\n"
        f"SECTOR: {sector}\n"
        f"PROFILE: {json.dumps(profile, ensure_ascii=False)[:2500]}\n\n"
        "Respond ONLY with valid JSON matching exactly:\n"
        '{"feeds": [{"url": "https://...", "why": "..."}], '
        '"legal_sources": [{"name": "...", "url": "https://..."}], '
        '"keywords": ["..."], '
        '"competitors": [{"name": "...", "url": "https://..."}]}\n'
        "Prefer real, sector-specific Tunisian/African/EU sources. Max 6 of each. "
        "Use only well-known URLs; never invent domains."
    )
    derived = await generate_json(prompt, temperature=0.2)

    feeds         = [f for f in (derived.get("feeds") or []) if isinstance(f, dict) and f.get("url")]
    legal_sources = [l for l in (derived.get("legal_sources") or []) if isinstance(l, dict) and l.get("url")]
    keywords      = _dedup_str(derived.get("keywords") or [])
    competitors   = [c for c in (derived.get("competitors") or []) if isinstance(c, dict) and c.get("name")]

    # Optional grounding: add a few fresh feeds discovered via web search.
    feeds.extend(await _ground_feeds(sector, keywords))

    await pool.execute(
        """
        INSERT INTO project_watch_targets
            (project_id, feeds, legal_sources, keywords, competitors, profile_hash, derived_at)
        VALUES ($1::uuid, $2::jsonb, $3::jsonb, $4::jsonb, $5::jsonb, $6, now())
        ON CONFLICT (project_id) DO UPDATE
            SET feeds = EXCLUDED.feeds, legal_sources = EXCLUDED.legal_sources,
                keywords = EXCLUDED.keywords, competitors = EXCLUDED.competitors,
                profile_hash = EXCLUDED.profile_hash, derived_at = now()
        """,
        project_id, json.dumps(feeds), json.dumps(legal_sources),
        json.dumps(keywords), json.dumps(competitors), phash,
    )

    await sse.push_event(project_id, "watch_targets_updated", {"project_id": project_id})
    merged = _merge(_sector_seeds(sector), {
        "feeds": feeds, "legal_sources": legal_sources,
        "keywords": keywords, "competitors": competitors,
    })
    return {"refreshed": True, **merged}


@router.get("/project/{project_id}/watch-targets")
async def get_watch_targets(project_id: str):
    """Merged view the daemon consumes: deterministic seeds ∪ stored LLM targets."""
    pool = await get_pool()
    _, sector = await _load(pool, project_id)
    stored = await _stored_targets(pool, project_id)
    return _merge(_sector_seeds(sector), stored)
