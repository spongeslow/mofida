"""Diagnostic wave runner.

Fans the StartupProfile out to the axis micro-services in three dependency
ordered waves (see ``axis_registry.DIAGNOSTIC_WAVES``) and collects every
``/diagnose`` response into a single ``axis_outputs`` map keyed by service slug.

A failing or unreachable axis never aborts the pass: its slot is filled with an
``{"error": ...}`` stub so the aggregator can still run on partial results.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

# Per-axis HTTP timeout. Wave 0 includes the Axis 01 maturity classifier, whose
# LLM generation can take 15-40s on a freshly loaded model, so the budget is
# larger than the deterministic axes would need.
_TIMEOUT = 60.0
# Wave 1 (brand) receives the outputs of these wave-0 axes as ``prior_outputs``.
_BRAND_DEPENDENCIES = ("ideation", "market", "product")


async def _call_axis(client: httpx.AsyncClient, axis_registry, slug: str, body: dict) -> tuple[str, dict]:
    """POST a profile body to one axis ``/diagnose`` endpoint, never raising."""
    url = f"{axis_registry.axis_host(slug)}/diagnose"
    try:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        return slug, resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        return slug, {"axis": slug, "error": str(exc)}


async def run_diagnostic_pass(project_id: str, profile: dict, axis_registry) -> dict:
    """Run the three diagnostic waves and return the collected axis outputs."""
    waves = axis_registry.DIAGNOSTIC_WAVES
    axis_outputs: dict[str, Any] = {}

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # ---- Wave 0: ideation / market / product, concurrently --------------
        wave0 = await asyncio.gather(
            *(_call_axis(client, axis_registry, slug, {"profile": profile}) for slug in waves[0])
        )
        axis_outputs.update(dict(wave0))

        # ---- Wave 1: brand, after wave 0 (consumes its outputs) -------------
        for slug in waves[1]:
            body = {
                "profile": profile,
                "prior_outputs": {dep: axis_outputs.get(dep) for dep in _BRAND_DEPENDENCIES},
            }
            slug, out = await _call_axis(client, axis_registry, slug, body)
            axis_outputs[slug] = out

        # ---- Wave 2: remaining scoring axes, concurrently -------------------
        wave2 = await asyncio.gather(
            *(_call_axis(client, axis_registry, slug, {"profile": profile}) for slug in waves[2])
        )
        axis_outputs.update(dict(wave2))

    return axis_outputs
