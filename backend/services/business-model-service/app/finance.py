"""Deterministic financial engine for Axis 05 (Business Model / Scalability).

Computes exact financial metrics (CAC, LTV, payback, runway, gross margin) from
the StartupProfile and derives financial blockers. No LLM involved — pure Python.
"""
from __future__ import annotations


def compute_financials(profile: dict) -> dict:
    """Compute financial metrics and financial-specific blockers from the profile.

    Returns:
        financials   — computed metrics (None when inputs missing)
        blockers     — list of financial blocker dicts
    """
    f = profile.get("finance") or {}
    offer = profile.get("offer") or {}

    cac: float | None = f.get("cac_usd")
    ltv: float | None = f.get("ltv_usd")
    burn: float | None = f.get("burn_rate_usd")
    runway: float | None = f.get("runway_months")
    gross_margin: float | None = f.get("gross_margin_pct")
    funding_stage: str = f.get("funding_stage", "bootstrapped")

    # Derived metrics
    ltv_cac_ratio: float | None = None
    payback_months: float | None = None

    if cac is not None and ltv is not None and cac > 0:
        ltv_cac_ratio = round(ltv / cac, 3)

    if cac is not None and ltv is not None and ltv > 0:
        monthly_value = ltv / 12
        if monthly_value > 0:
            payback_months = round(cac / monthly_value, 1)

    blockers: list[dict] = []

    # LTV/CAC < 1 → destroying value on every acquisition
    if ltv_cac_ratio is not None and ltv_cac_ratio < 1.0:
        blockers.append({
            "axis": "business-model",
            "code": "finance.ltv_cac_below_one",
            "description": f"LTV/CAC = {ltv_cac_ratio:.2f} — acquiring customers destroys value.",
            "severity": "critical",
            "score_dimension": "scalability",
            "remediation": "Reduce CAC or increase LTV before scaling customer acquisition spend.",
        })

    # LTV/CAC < 3 → poor unit economics (industry benchmark is ≥ 3)
    elif ltv_cac_ratio is not None and ltv_cac_ratio < 3.0:
        blockers.append({
            "axis": "business-model",
            "code": "finance.ltv_cac_below_three",
            "description": f"LTV/CAC = {ltv_cac_ratio:.2f} (< 3.0 — below the healthy threshold).",
            "severity": "warning",
            "score_dimension": "scalability",
            "remediation": "Target LTV/CAC ≥ 3.0 before planning significant growth spend.",
        })

    # Runway: critical < 3 months
    if runway is not None and runway < 3:
        blockers.append({
            "axis": "business-model",
            "code": "finance.critical_runway",
            "description": f"Runway is {runway:.1f} months — existential risk.",
            "severity": "critical",
            "score_dimension": "scalability",
            "remediation": "Cut non-essential burn and initiate emergency fundraising immediately.",
        })
    elif runway is not None and runway < 6:
        blockers.append({
            "axis": "business-model",
            "code": "finance.short_runway",
            "description": f"Runway is {runway:.1f} months (< 6 months).",
            "severity": "warning",
            "score_dimension": "scalability",
            "remediation": "Raise a bridge round or extend runway to at least 12 months.",
        })

    # Gross margin < 30% for software/digital (low-margin models are normal for hardware/agri)
    if gross_margin is not None and gross_margin < 30:
        blockers.append({
            "axis": "business-model",
            "code": "finance.low_gross_margin",
            "description": f"Gross margin is {gross_margin:.1f}% — below the 30% sustainability threshold.",
            "severity": "warning",
            "score_dimension": "scalability",
            "remediation": "Review cost of goods sold and pricing strategy to improve gross margin.",
        })

    # Burn with no runway tracking
    if burn is not None and burn > 0 and runway is None:
        blockers.append({
            "axis": "business-model",
            "code": "finance.burn_without_runway",
            "description": "Burn rate reported but runway not calculated.",
            "severity": "warning",
            "score_dimension": "scalability",
            "remediation": "Divide current cash balance by monthly burn to compute runway.",
        })

    return {
        "financials": {
            "ltv_cac_ratio": ltv_cac_ratio,
            "payback_months": payback_months,
            "burn_rate_usd": burn,
            "runway_months": runway,
            "gross_margin_pct": gross_margin,
        },
        "blockers": blockers,
    }
