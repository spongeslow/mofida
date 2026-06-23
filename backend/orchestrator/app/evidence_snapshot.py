"""Shared evidence gathering for the H1–H3 analytical features.

Builds a grounded snapshot of a project from the diagnostic data already in the
database — scores, blockers, competitors, opportunities, and concept bottlenecks
— plus a list of ``weak_points`` rendered as EvidenceRef-shaped dicts so the UI
can show the source chain. Every claim a feature makes must trace back to one of
these items.
"""
from __future__ import annotations

import json
import logging

logger = logging.getLogger("moufida.evidence")


def _as_dict(v) -> dict:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {}
    return v or {}


def _as_list(v) -> list:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return []
    return v or []


async def gather_evidence(pool, project_id: str) -> dict:
    """Return a grounded evidence snapshot for a project (best-effort)."""
    snapshot: dict = {
        "scores": {}, "blockers": [], "competitors": [], "opportunities": [],
        "bottlenecks": [], "weak_points": [], "maturity_stage": None, "profile": {},
    }

    # Profile
    try:
        row = await pool.fetchrow("SELECT profile FROM profiles WHERE id = $1::uuid", project_id)
        if row:
            snapshot["profile"] = _as_dict(row["profile"])
    except Exception as exc:  # noqa: BLE001
        logger.debug("evidence profile: %s", exc)

    # Latest scores
    try:
        rows = await pool.fetch(
            """SELECT DISTINCT ON (score_name) score_name, score
                 FROM score_snapshots WHERE project_id = $1::uuid
                 ORDER BY score_name, created_at DESC""",
            project_id,
        )
        snapshot["scores"] = {r["score_name"]: round(float(r["score"]), 2) for r in rows}
    except Exception as exc:  # noqa: BLE001
        logger.debug("evidence scores: %s", exc)

    # Latest diagnostic → blockers + maturity
    try:
        d = await pool.fetchrow(
            """SELECT maturity_stage, blockers FROM diagnostic_history
                 WHERE project_id = $1::uuid ORDER BY created_at DESC LIMIT 1""",
            project_id,
        )
        if d:
            snapshot["maturity_stage"] = d["maturity_stage"]
            snapshot["blockers"] = _as_list(d["blockers"])[:8]
    except Exception as exc:  # noqa: BLE001
        logger.debug("evidence blockers: %s", exc)

    # Competitors
    try:
        rows = await pool.fetch(
            """SELECT name, pricing, positioning FROM competitors
                 WHERE project_id = $1::uuid LIMIT 6""",
            project_id,
        )
        snapshot["competitors"] = [
            {"name": r["name"], "pricing": _as_dict(r["pricing"]), "positioning": r["positioning"]}
            for r in rows
        ]
    except Exception as exc:  # noqa: BLE001
        logger.debug("evidence competitors: %s", exc)

    # Opportunities (active)
    try:
        rows = await pool.fetch(
            """SELECT title, deadline, match_score FROM opportunities
                 WHERE project_id = $1::uuid AND dismissed = FALSE
                 ORDER BY deadline ASC NULLS LAST LIMIT 6""",
            project_id,
        )
        snapshot["opportunities"] = [
            {"title": r["title"],
             "deadline": r["deadline"].isoformat() if r["deadline"] else None,
             "match_score": round(float(r["match_score"]), 2) if r["match_score"] is not None else None}
            for r in rows
        ]
    except Exception as exc:  # noqa: BLE001
        logger.debug("evidence opportunities: %s", exc)

    # Concept bottlenecks (latest per axis)
    try:
        rows = await pool.fetch(
            """SELECT DISTINCT ON (axis) axis, bottleneck, cbm_score
                 FROM concept_scores WHERE project_id = $1::uuid
                 ORDER BY axis, created_at DESC""",
            project_id,
        )
        for r in rows:
            b = _as_dict(r["bottleneck"])
            if b.get("concept_id"):
                snapshot["bottlenecks"].append({
                    "axis": r["axis"], "concept_id": b.get("concept_id"),
                    "label": b.get("label"), "cbm_score": r["cbm_score"],
                })
    except Exception as exc:  # noqa: BLE001
        logger.debug("evidence bottlenecks: %s", exc)

    snapshot["weak_points"] = _derive_weak_points(snapshot)
    return snapshot


def _derive_weak_points(s: dict) -> list[dict]:
    """EvidenceRef-shaped dicts of the most challengeable facts."""
    refs: list[dict] = []

    for name, score in sorted(s["scores"].items(), key=lambda kv: kv[1]):
        if score < 2.5:
            refs.append({
                "kind": "axis", "label": f"{name} score", "field": "score",
                "value": f"{score}/5", "detail": "below par",
            })

    for b in s["blockers"]:
        if not isinstance(b, dict):
            continue
        sev = b.get("severity", "info")
        if sev in ("critical", "warning"):
            refs.append({
                "kind": "axis", "label": f"{b.get('axis', 'blocker')} blocker",
                "detail": b.get("description", "")[:140],
            })

    for c in s["competitors"]:
        pricing = c.get("pricing") or {}
        if pricing:
            refs.append({
                "kind": "competitor", "label": c.get("name", "competitor"),
                "detail": "has published pricing",
            })

    for o in s["opportunities"]:
        if o.get("deadline"):
            refs.append({
                "kind": "opportunity", "label": o.get("title", "opportunity"),
                "detail": f"deadline {o['deadline']}",
            })

    for b in s["bottlenecks"]:
        refs.append({
            "kind": "axis", "label": f"{b['axis']} bottleneck",
            "field": b.get("concept_id"), "detail": b.get("label") or "",
        })

    return refs[:12]
