"""Label-Free concept scoring + linear-bottleneck orchestration.

The LLM (Ollama, via ``llm_json.generate_json``) scores each named concept in
[0, 1] for a given axis; the Rust ``moufida-signal`` service applies the
calibrated linear head and returns the composite score + bottleneck. Everything
here is best-effort: any failure yields ``None`` so the diagnostic still returns.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

from ..llm_json import generate_json

logger = logging.getLogger("moufida.cbm")

SIGNAL_URL = os.environ.get("SIGNAL_URL", "http://signal:8010")
_CBM_TIMEOUT = float(os.getenv("CBM_SIGNAL_TIMEOUT", "10"))
_MAX_CONCURRENCY = int(os.getenv("CBM_MAX_CONCURRENCY", "6"))

CONCEPTS: dict[str, list[dict]] = json.loads(
    (Path(__file__).parent / "concepts.json").read_text(encoding="utf-8")
)


def concept_labels(axis: str) -> dict[str, str]:
    """{concept_id: human label} for one axis."""
    return {c["id"]: c["label"] for c in CONCEPTS.get(axis, [])}


# Profile fields worth surfacing to the concept scorer, in a stable order.
_PROFILE_FIELDS = [
    "name", "sector", "raw_idea", "description", "offer", "value_proposition",
    "target_market", "target_segment", "icp", "business_model", "revenue_model",
    "pricing", "stage", "self_assessed_stage", "team", "team_size", "traction",
    "customers", "competitors", "innovation", "ip_protection", "legal_structure",
    "market_size", "channels", "milestones",
]


def profile_to_text(profile: dict) -> str:
    """Flatten the structured profile into a compact text block for the LLM."""
    lines: list[str] = []
    for key in _PROFILE_FIELDS:
        if key in profile and profile[key] not in (None, "", [], {}):
            val = profile[key]
            if isinstance(val, (list, dict)):
                val = json.dumps(val, ensure_ascii=False)
            lines.append(f"{key}: {val}")
    # Include any remaining scalar fields not already covered.
    for key, val in profile.items():
        if key in _PROFILE_FIELDS or key.startswith("_"):
            continue
        if isinstance(val, (str, int, float)) and val not in (None, ""):
            lines.append(f"{key}: {val}")
    return "\n".join(lines) if lines else json.dumps(profile, ensure_ascii=False)[:2000]


async def _score_one_concept(
    axis: str, concept: dict, profile_text: str, sem: asyncio.Semaphore
) -> tuple[str, float]:
    prompt = (
        f"You are evaluating a startup profile for the '{axis}' diagnostic axis.\n"
        f"Task: {concept['prompt']}\n\n"
        f"Profile:\n{profile_text}\n\n"
        'Respond with JSON only: {"score": <float between 0.0 and 1.0>}'
    )
    async with sem:
        result = await generate_json(prompt, temperature=0.1)
    try:
        score = float(result.get("score", 0.5))
    except (TypeError, ValueError):
        score = 0.5
    return concept["id"], max(0.0, min(1.0, score))


async def score_concepts(
    axis: str, profile_text: str, sem: asyncio.Semaphore | None = None
) -> dict[str, float]:
    """Score every concept of one axis. Returns {concept_id: float}."""
    axis_concepts = CONCEPTS.get(axis, [])
    if not axis_concepts:
        return {}
    sem = sem or asyncio.Semaphore(_MAX_CONCURRENCY)
    pairs = await asyncio.gather(
        *(_score_one_concept(axis, c, profile_text, sem) for c in axis_concepts)
    )
    return dict(pairs)


async def _signal_score(client: httpx.AsyncClient, axis: str, concepts: dict[str, float]) -> dict | None:
    try:
        resp = await client.post(
            f"{SIGNAL_URL}/cbm/score",
            json={"axis": axis, "concepts": concepts},
            timeout=_CBM_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001 — best-effort
        logger.warning("cbm: signal /cbm/score failed for axis=%s: %s", axis, exc)
        return None


async def _run_one_axis(
    client: httpx.AsyncClient,
    axis: str,
    profile_text: str,
    sem: asyncio.Semaphore,
    actual_score: float | None,
) -> tuple[str, dict[str, Any]] | None:
    concepts = await score_concepts(axis, profile_text, sem)
    if not concepts:
        return None
    signal = await _signal_score(client, axis, concepts)
    if signal is None:
        # Signal down — still surface the raw concept activations.
        return axis, {
            "concepts": concepts,
            "cbm_score": None,
            "bottleneck": None,
            "calibrated": False,
            "actual_score": actual_score,
            "labels": concept_labels(axis),
        }

    bottleneck = signal.get("bottleneck")
    if bottleneck and isinstance(bottleneck, dict):
        labels = concept_labels(axis)
        bottleneck["label"] = labels.get(bottleneck.get("concept_id", ""), bottleneck.get("concept_id"))

    return axis, {
        "concepts": concepts,
        "cbm_score": signal.get("score"),
        "weighted_contributions": signal.get("weighted_contributions", {}),
        "bottleneck": bottleneck,
        "calibrated": bool(signal.get("calibrated", False)),
        "actual_score": actual_score,
        "labels": concept_labels(axis),
    }


async def run_cbm_for_axes(
    profile: dict,
    axes: list[str],
    actual_scores: dict[str, float | None] | None = None,
) -> dict[str, dict[str, Any]]:
    """Run the full concept-bottleneck pass for the given axes.

    Returns ``{ axis: { concepts, cbm_score, bottleneck, calibrated, ... } }``.
    Best-effort: a failing axis is simply omitted.
    """
    actual_scores = actual_scores or {}
    profile_text = profile_to_text(profile)
    sem = asyncio.Semaphore(_MAX_CONCURRENCY)
    results: dict[str, dict[str, Any]] = {}

    async with httpx.AsyncClient() as client:
        outcomes = await asyncio.gather(
            *(
                _run_one_axis(client, axis, profile_text, sem, actual_scores.get(axis))
                for axis in axes
            ),
            return_exceptions=True,
        )

    for outcome in outcomes:
        if isinstance(outcome, Exception):
            logger.warning("cbm: axis run raised: %s", outcome)
            continue
        if outcome is None:
            continue
        axis, data = outcome
        results[axis] = data
    return results
