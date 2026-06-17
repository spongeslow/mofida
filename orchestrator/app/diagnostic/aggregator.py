"""Diagnostic result aggregator.

Folds the per-axis ``/diagnose`` responses into a single diagnostic snapshot:
maturity vs. self-assessment, prioritised blockers, composite scores and their
explanation trees, and the union of detected anomalies.
"""
from __future__ import annotations

from typing import Any, Optional

# Keyword (lower-cased) -> any blocker whose text contains it is "critical".
_CRITICAL_KEYWORDS = ("runway", "gdpr", "ai act", "no customer")
# Sort priority: critical first, then warning, then info.
_SEVERITY_RANK = {"critical": 0, "warning": 1, "info": 2}

# Composite scores expected from the scoring axes.
_EXPECTED_SCORES = ("market", "commercial_offer", "innovation", "scalability", "green")


def _classify_severity(blocker: dict) -> str:
    text = " ".join(
        str(blocker.get(k, "")) for k in ("description", "title", "domain")
    ).lower()
    return "critical" if any(kw in text for kw in _CRITICAL_KEYWORDS) else "warning"


def aggregate_results(profile: dict, axis_outputs: dict) -> dict:
    ideation = axis_outputs.get("ideation") or {}
    maturity_stage: Optional[str] = ideation.get("stage") or ideation.get("maturity_stage")
    self_assessed_stage: Optional[str] = ideation.get("self_assessed_stage") or profile.get(
        "self_assessed_stage"
    )
    perception_gap = maturity_stage != self_assessed_stage

    blockers: list[dict] = []
    anomalies: list[dict] = []
    scores: dict[str, float] = {}
    score_breakdowns: dict[str, Any] = {}

    for slug, out in axis_outputs.items():
        if not isinstance(out, dict):
            continue

        for raw in out.get("blockers") or []:
            blocker = dict(raw) if isinstance(raw, dict) else {"description": str(raw)}
            blocker["axis"] = slug
            blocker["severity"] = _classify_severity(blocker)
            blockers.append(blocker)

        anomalies.extend(out.get("anomalies") or [])

        name = out.get("score_name")
        if name is not None and out.get("score") is not None:
            scores[name] = out["score"]
            score_breakdowns[name] = out.get("explanation")

    blockers.sort(key=lambda b: _SEVERITY_RANK.get(b.get("severity"), 1))

    return {
        "maturity_stage": maturity_stage,
        "self_assessed_stage": self_assessed_stage,
        "perception_gap": perception_gap,
        "blockers": blockers,
        "anomalies": anomalies,
        "scores": scores,
        "score_breakdowns": score_breakdowns,
    }
