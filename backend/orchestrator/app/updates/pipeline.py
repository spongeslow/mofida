"""Shared update pipeline — all four sources converge here.

All sources call ``apply_update()``, which:
  1. Persists any section_patches to plan_sections
  2. Determines downstream affected axes via dependency engine
  3. Writes one events row (diff, axes_affected, suggestion, status='new')
  4. SSE-pushes 'event_new' so the UI reacts live

The caller decides which re-runs to schedule (proposals, not auto-apply).
Only daemon/tool "Act" auto-applies; chat + manual always produce proposals.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from .. import sse
from ..dependency import affected_axes as _affected_axes
from ..generation.runner import persist_section

logger = logging.getLogger("moufida.updates.pipeline")


async def apply_update(
    pool,
    project_id: str,
    changed_axes: list[str],
    *,
    section_patches: dict[str, dict] | None = None,
    summary: str,
    source: str,
    severity: str = "info",
    suggestion: dict | None = None,
    diff: dict | None = None,
    event_type: str = "update",
    auto_persist: bool = False,
) -> tuple[str, list[str]]:
    """Core update tail shared by all four sources.

    Returns (event_id, affected_axes_downstream).
    ``auto_persist=True`` commits section_patches immediately (tool/daemon Act);
    otherwise patches are stored in the event's ``suggestion`` for the user to approve.
    """
    if auto_persist and section_patches:
        for axis, patch in section_patches.items():
            try:
                await persist_section(
                    pool, project_id, axis,
                    patch.get("content", {}),
                    patch.get("summary"),
                    source=source,
                )
            except Exception as exc:
                logger.warning("persist_section failed axis=%s: %s", axis, exc)

    downstream = _affected_axes(set(changed_axes)) if changed_axes else []

    event_id = await pool.fetchval(
        """
        INSERT INTO events
            (project_id, source, type, severity, summary,
             axes_affected, diff, suggestion, status)
        VALUES ($1::uuid, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, 'new')
        RETURNING id
        """,
        project_id,
        source,
        event_type,
        severity,
        summary,
        changed_axes,
        json.dumps(diff or {}),
        json.dumps(suggestion or {}),
    )

    await sse.push_event(project_id, "event_new", {
        "event_id":     str(event_id),
        "source":       source,
        "summary":      summary,
        "axes_affected": changed_axes,
        "severity":     severity,
        "suggestion":   suggestion,
    })

    return str(event_id), downstream


async def interpret_chat_update(
    ollama_base: str,
    ollama_model: str,
    message: str,
    plan_sections: dict[str, Any],
    language: str = "fr",
) -> dict[str, Any]:
    """LLM call: decide if a chat message is an update assertion vs. a question.

    Returns:
      {
        is_update: bool,
        changed_axes: list[str],       # which axes the statement affects
        section_patches: dict,          # field-level updates (may be empty)
        summary: str,                   # human-readable what changed
        suggested_extra_axes: list[str] # wider scope suggestion
      }
    """
    import httpx

    system = (
        "You are Moufida, a startup advisor. A founder just said something.\n"
        "Decide if they are ASSERTING A CHANGE (e.g. 'I hired a CTO', 'We pivoted to B2B', "
        "'We got 10 paying customers') vs. ASKING A QUESTION.\n"
        "If it's an assertion, identify which startup plan axes are affected and summarise the change.\n\n"
        "Current plan axes: ideation, market, product, brand, business-model, legal, operations, marketing, sales.\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"is_update": false, "changed_axes": [], "section_patches": {}, '
        '"summary": "", "suggested_extra_axes": []}\n\n'
        f"Respond in {language}."
    )

    result = {
        "is_update": False,
        "changed_axes": [],
        "section_patches": {},
        "summary": "",
        "suggested_extra_axes": [],
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as http:
            resp = await http.post(
                f"{ollama_base}/api/chat",
                json={
                    "model": ollama_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user",   "content": message},
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("message", {}).get("content", "")
            s, e = raw.find("{"), raw.rfind("}")
            if s != -1 and e > s:
                parsed = json.loads(raw[s:e + 1])
                result.update({k: parsed[k] for k in result if k in parsed})
    except Exception as exc:
        logger.warning("interpret_chat_update failed: %s", exc)

    return result


async def interpret_daemon_event(
    ollama_base: str,
    ollama_model: str,
    event_text: str,
    sector: str,
    language: str = "fr",
) -> dict[str, Any]:
    """LLM call: map a daemon 'significant change' news item to affected axes + suggestion."""
    import httpx

    system = (
        "You are Moufida, a startup advisor. A daemon detected an external event.\n"
        "Map it to affected startup plan axes and propose an action.\n\n"
        "Axes: ideation, market, product, brand, business-model, legal, operations, marketing, sales.\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"changed_axes": ["market"], "severity": "warning", "summary": "", '
        '"suggestion": {"action": "rerun_axes", "axes": ["market"], "description": ""}}\n\n'
        f"Sector: {sector}. Respond in {language}."
    )

    result: dict[str, Any] = {
        "changed_axes": [],
        "severity": "info",
        "summary": event_text[:200],
        "suggestion": {},
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as http:
            resp = await http.post(
                f"{ollama_base}/api/chat",
                json={
                    "model": ollama_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user",   "content": event_text},
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("message", {}).get("content", "")
            s, e = raw.find("{"), raw.rfind("}")
            if s != -1 and e > s:
                parsed = json.loads(raw[s:e + 1])
                result.update({k: parsed[k] for k in result if k in parsed})
    except Exception as exc:
        logger.warning("interpret_daemon_event failed: %s", exc)

    return result
