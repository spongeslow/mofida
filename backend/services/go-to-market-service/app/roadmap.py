"""RAG-augmented 3-horizon roadmap generator (Axis 10)."""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

import httpx

RAG_URL = os.environ["RAG_URL"]
OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
OLLAMA_CHAT_MODEL = os.environ["OLLAMA_CHAT_MODEL"]
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))

logger = logging.getLogger("moufida.gtm.roadmap")

_LANG_NAMES = {"fr": "French", "en": "English", "ar": "French", "ar-TN": "French"}

# Natural-language query per score dimension for RAG retrieval.
_DIM_QUERIES: dict[str, str] = {
    "market": "étude de marché validation clients concurrents TAM SAM",
    "commercial_offer": "proposition de valeur produit MVP pricing différentiation",
    "innovation": "innovation brevet propriété intellectuelle R&D technologie",
    "scalability": "financement investissement levée de fonds économie unitaire CAC LTV",
    "green": "conformité réglementaire protection données RGPD INPDP impact environnemental",
}


def _deduplicate(resources: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for r in resources:
        key = r.get("resource_id") or r.get("url", "")
        if key and key not in seen:
            seen.add(key)
            out.append(r)
    return out


async def _query_rag(
    query: str,
    stage: Optional[str],
    dimensions: list[str],
    sector: Optional[str],
    http: httpx.AsyncClient,
    top_k: int = 3,
) -> list[dict]:
    resp = await http.post(
        f"{RAG_URL}/retrieve",
        json={"query": query, "stage": stage, "dimensions": dimensions, "sector": sector, "top_k": top_k},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


async def generate_roadmap(
    project_id: str,
    stage: str,
    sector: str,
    language: str,
    blockers: list[dict],
    scores: dict[str, float],
    profile: dict,
) -> dict:
    """Query RAG for each gap, then ask the LLM to build a 3-horizon action plan."""
    lang_name = _LANG_NAMES.get(language, "French")

    low_dims = [name for name, val in scores.items() if val < 0.40]
    critical_blocker_dims = list(
        {b["score_dimension"] for b in blockers
         if b.get("severity") == "critical" and b.get("score_dimension")}
    )
    all_dims = list(dict.fromkeys(low_dims + critical_blocker_dims))  # deduplicated, ordered

    all_resources: list[dict] = []
    async with httpx.AsyncClient() as http:
        # Per-dimension queries.
        for dim in all_dims[:5]:
            query = _DIM_QUERIES.get(dim, f"ressources startup {dim} Tunisie")
            try:
                hits = await _query_rag(query, stage, [dim], sector, http)
                all_resources.extend(hits)
            except Exception as exc:
                logger.warning("RAG dim query failed dim=%s: %s", dim, exc)

        # General stage+sector query.
        try:
            general = await _query_rag(
                f"ressources startup {stage} {sector} Tunisie accompagnement financement",
                stage, [], sector, http,
            )
            all_resources.extend(general)
        except Exception as exc:
            logger.warning("RAG general query failed: %s", exc)

    resources = _deduplicate(all_resources)[:9]

    # Build LLM prompt.
    gaps_lines = "\n".join(
        f"- {d}: score {scores.get(d, 0):.2f}/1.00" for d in all_dims
    ) or "- Aucune dimension critique identifiée"

    blocker_lines = "\n".join(
        f"- [{b.get('severity','?').upper()}] {b.get('description','')}" for b in blockers[:5]
    ) or "- Aucun blocage critique"

    resources_lines = "\n".join(
        f"{i + 1}. **{r.get('title')}** — {r.get('provider', '')} — {r.get('url', '')}\n"
        f"   Extrait: {r.get('matched_chunk', '')[:120]}..."
        for i, r in enumerate(resources)
    ) or "Aucune ressource disponible dans la base de connaissances."

    prompt = (
        f"Tu es un conseiller expert en startups tunisiennes.\n\n"
        f"Startup: stage={stage}, secteur={sector}\n\n"
        f"Dimensions à améliorer (score < 0.40):\n{gaps_lines}\n\n"
        f"Blocages critiques:\n{blocker_lines}\n\n"
        f"Ressources disponibles (cite UNIQUEMENT ces ressources par leur titre et URL):\n"
        f"{resources_lines}\n\n"
        f"Génère un plan d'action en {lang_name} avec 3 horizons temporels:\n"
        f'- "immediate": 2-3 actions à faire dans 0-2 semaines\n'
        f'- "short_term": 2-3 actions à faire dans 1-3 mois\n'
        f'- "medium_term": 2-3 actions à faire dans 3-12 mois\n\n'
        f"Chaque action doit être spécifique, actionnable, et citer une ressource de la liste.\n\n"
        f"Réponds UNIQUEMENT avec ce JSON (sans texte avant ni après):\n"
        f'{{"immediate":[{{"action":"...","rationale":"...","resource":{{"title":"...","url":"..."}}}}],'
        f'"short_term":[...],"medium_term":[...]}}'
    )

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as http:
            resp = await http.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_CHAT_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"seed": 42, "temperature": 0.2},
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "{}")
        roadmap = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("LLM non-JSON response: %.200s — %s", raw, exc)
        roadmap = {"immediate": [], "short_term": [], "medium_term": [], "parse_error": True}
    except Exception as exc:
        logger.error("LLM roadmap call failed: %s", exc)
        roadmap = {"immediate": [], "short_term": [], "medium_term": [], "llm_error": str(exc)}

    return {
        "stage": stage,
        "sector": sector,
        "language": language,
        "gaps": all_dims,
        "resources_used": len(resources),
        "roadmap": roadmap,
    }
