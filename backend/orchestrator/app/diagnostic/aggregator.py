"""Diagnostic result aggregator.

Folds the per-axis ``/diagnose`` responses into a single diagnostic snapshot:
maturity vs. self-assessment, prioritised blockers, composite scores and their
explanation trees, anomaly detection (computed once here, not per-axis),
investor-grade due diligence summary, natural-language justifications,
and rule-based improvement recommendations.
"""
from __future__ import annotations

from typing import Any, Optional

# Severity sort order: critical first, warning, info last.
_SEVERITY_RANK: dict[str, int] = {"critical": 0, "warning": 1, "info": 2}

# Composite scores expected from the scoring axes.
_EXPECTED_SCORES = ("market", "commercial_offer", "innovation", "scalability", "green")

# Rule-based guidance: (score_name, sub_dimension_id) -> one-line action
_GUIDANCE: dict[tuple[str, str], str] = {
    ("market", "addressable_market_size"): "Conduct a TAM/SAM/SOM analysis to size your market.",
    ("market", "customer_validation"): "Run at least 5 structured customer interviews.",
    ("market", "revenue_model_clarity"): "Define and validate your revenue model.",
    ("market", "competitive_intensity"): "Map your competitive landscape and articulate your moat.",
    ("commercial_offer", "value_proposition_clarity"): (
        "Write a one-sentence value proposition using the Jobs-to-be-Done framework."
    ),
    ("commercial_offer", "pricing_coherence"): "Define a value-based pricing strategy.",
    ("commercial_offer", "differentiation"): (
        "Document 3 defensible differentiators vs. named competitors."
    ),
    ("commercial_offer", "product_maturity"): "Build an MVP to demonstrate technical feasibility.",
    ("innovation", "product_novelty"): "Document your TRL level and initiate IP protection steps.",
    ("innovation", "brand_distinctiveness"): "Define a distinctive brand positioning statement.",
    ("innovation", "value_creation_novelty"): (
        "Articulate how your venture creates genuinely new value vs. existing solutions."
    ),
    ("scalability", "unit_economics"): "Calculate your CAC, LTV, and payback period from current data.",
    ("scalability", "funding_readiness"): "Extend runway to at least 12 months before your next raise.",
    ("scalability", "operational_automation"): "Automate the top 3 highest-volume manual processes.",
    ("scalability", "quality_framework"): (
        "Document core SOPs to enable delegation and quality control."
    ),
    ("green", "sdg_alignment"): (
        "Map your project to 2-3 UN SDGs and define measurable impact KPIs."
    ),
    ("green", "regulatory_compliance"): (
        "Implement a privacy policy and Tunisian data law compliance checklist."
    ),
    ("green", "environmental_impact"): "Conduct a basic environmental impact assessment.",
    ("green", "ip_protection"): "Register your IP via INNORPI or file internationally via PCT.",
}

_LOW_NORMALISED = 0.40  # sub-dimension below this generates a recommendation


def _derive_recommendations(score_breakdowns: dict[str, Any]) -> list[dict]:
    """Rule-based recommendations keyed by low-scoring sub-dimensions."""
    recommendations: list[dict] = []
    for score_name, breakdown in score_breakdowns.items():
        if not isinstance(breakdown, dict):
            continue
        for c in breakdown.get("components", []):
            key = (score_name, c.get("name", ""))
            guidance = _GUIDANCE.get(key)
            if guidance and c.get("normalised_value", 1.0) < _LOW_NORMALISED:
                recommendations.append({
                    "score_name": score_name,
                    "sub_dimension": c.get("name"),
                    "action": guidance,
                    "current_value": round(c.get("normalised_value", 0), 3),
                    "weight": c.get("weight", 0),
                    "priority": "high" if c.get("weight", 0) >= 0.25 else "medium",
                })
    recommendations.sort(key=lambda r: r.get("weight", 0), reverse=True)
    return recommendations[:7]


def aggregate_results(profile: dict, axis_outputs: dict) -> dict:
    ideation = axis_outputs.get("ideation") or {}

    # The adaptive intake (CAT) produces a rigorous latent-stage estimate via
    # Item Response Theory. When present it is the ground-truth maturity signal;
    # the ideation LLM classification is the fallback for legacy/CAT-less intakes.
    cat = profile.get("cat") if isinstance(profile.get("cat"), dict) else {}
    cat_stage_label: Optional[str] = cat.get("stage_label")

    maturity_stage: Optional[str] = (
        cat_stage_label or ideation.get("stage") or ideation.get("maturity_stage")
    )
    self_assessed_stage: Optional[str] = (
        ideation.get("self_assessed_stage") or profile.get("self_assessed_stage")
    )
    perception_gap = (
        self_assessed_stage is not None and maturity_stage != self_assessed_stage
    )

    blockers: list[dict] = []
    scores: dict[str, float] = {}
    score_breakdowns: dict[str, Any] = {}
    justifications: dict[str, str] = {}
    all_dd_flags: list[dict] = []

    for slug, out in axis_outputs.items():
        if not isinstance(out, dict):
            continue

        # Blockers from each axis.
        for raw in out.get("blockers") or []:
            blocker = dict(raw) if isinstance(raw, dict) else {"description": str(raw)}
            blocker.setdefault("axis", slug)
            blockers.append(blocker)

        # Scores and breakdowns.
        name = out.get("score_name")
        if name is not None and out.get("score") is not None:
            scores[name] = out["score"]
            score_breakdowns[name] = out.get("explanation")

        # Collect NL justifications keyed by score_name.
        if name and out.get("justification"):
            justifications[name] = out["justification"]

        # Aggregate DD flags from all axes.
        dd = out.get("due_diligence") or {}
        for flag in dd.get("flags") or []:
            flag_copy = dict(flag)
            flag_copy.setdefault("axis", slug)
            all_dd_flags.append(flag_copy)

    # Sort blockers by severity.
    blockers.sort(key=lambda b: _SEVERITY_RANK.get(b.get("severity", "info"), 2))

    # Anomalies: computed once from the profile, not aggregated per-axis.
    # This eliminates the 5× duplication defect from the previous implementation.
    anomalies: list[dict] = []
    try:
        from affinitree import StartupProfile, detect
        startup_profile = StartupProfile(**profile)
        anomalies = [a.to_dict() for a in detect(startup_profile)]
    except Exception:
        pass

    # Due diligence summary across all axes.
    due_diligence_summary = {
        "flags": all_dd_flags,
        "critical_count": sum(1 for f in all_dd_flags if f.get("severity") == "critical"),
        "warning_count": sum(1 for f in all_dd_flags if f.get("severity") == "warning"),
        "info_count": sum(1 for f in all_dd_flags if f.get("severity") == "info"),
    }

    recommendations = _derive_recommendations(score_breakdowns)

    return {
        "maturity_stage": maturity_stage,
        "self_assessed_stage": self_assessed_stage,
        "perception_gap": perception_gap,
        "cat": cat or None,
        "blockers": blockers,
        "anomalies": anomalies,
        "due_diligence": due_diligence_summary,
        "scores": scores,
        "score_breakdowns": score_breakdowns,
        "justifications": justifications,
        "recommendations": recommendations,
    }
