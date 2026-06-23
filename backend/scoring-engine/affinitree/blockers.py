"""Deterministic blocker derivation from Affinitree ScoreResult.

A blocker is raised when a sub-dimension's normalised value falls below
LOW_THRESHOLD, meaning the startup is materially weak on that dimension.
Blockers are separate from anomalies (cross-field contradictions) and DD
flags (investor-grade concerns).
"""
from __future__ import annotations

from .scorer import ScoreResult

LOW_THRESHOLD = 0.34  # vi below this triggers a blocker

# (score_name, sub_dimension_id) -> (human description, remediation)
BLOCKER_RULES: dict[tuple[str, str], tuple[str, str]] = {
    ("market", "addressable_market_size"): (
        "Market size not quantified (no SAM/TAM data).",
        "Estimate TAM/SAM/SOM with a bottom-up model.",
    ),
    ("market", "customer_validation"): (
        "No customer validation evidence.",
        "Run at least 5 structured customer interviews.",
    ),
    ("market", "revenue_model_clarity"): (
        "Revenue model not defined.",
        "Select a revenue model and document MRR/ARR targets.",
    ),
    ("market", "competitive_intensity"): (
        "Competitive landscape not mapped.",
        "Identify direct and indirect competitors and document your positioning.",
    ),
    ("commercial_offer", "value_proposition_clarity"): (
        "Value proposition is unclear or generic.",
        "State problem, segment, and measurable benefit in one sentence.",
    ),
    ("commercial_offer", "pricing_coherence"): (
        "Pricing model undefined.",
        "Define a pricing strategy — at minimum document your pricing basis.",
    ),
    ("commercial_offer", "differentiation"): (
        "Competitive differentiation not established.",
        "Document 3 defensible differentiators vs. named competitors.",
    ),
    ("commercial_offer", "product_maturity"): (
        "Product not yet at MVP stage.",
        "Build an MVP and gather initial user feedback.",
    ),
    ("innovation", "product_novelty"): (
        "Product novelty not demonstrated (low TRL or no IP).",
        "Document TRL level and IP protection steps taken.",
    ),
    ("innovation", "market_novelty"): (
        "Market novelty unclear.",
        "Document what is genuinely new in your market approach.",
    ),
    ("innovation", "brand_distinctiveness"): (
        "Brand not differentiated from competitors.",
        "Define a distinctive positioning statement.",
    ),
    ("innovation", "value_creation_novelty"): (
        "Value creation novelty weak.",
        "Articulate clearly how your venture creates new value vs. existing solutions.",
    ),
    ("scalability", "unit_economics"): (
        "Unit economics not established.",
        "Compute CAC, LTV, and payback period from current data.",
    ),
    ("scalability", "funding_readiness"): (
        "Short runway / insufficient funding runway.",
        "Extend runway via revenue, cost cuts, or financing.",
    ),
    ("scalability", "operational_automation"): (
        "Operations are highly manual.",
        "Identify the top 3 manual steps and automate or systematise them.",
    ),
    ("scalability", "supply_chain_resilience"): (
        "Supply chain has a single point of failure.",
        "Identify alternative suppliers for critical inputs.",
    ),
    ("scalability", "quality_framework"): (
        "No standard operating procedures documented.",
        "Document core operational procedures to enable delegation and quality control.",
    ),
    ("green", "regulatory_compliance"): (
        "Data protection compliance gaps (GDPR / Tunisian Law 2004-63).",
        "Implement a privacy policy and Tunisian data law compliance checklist.",
    ),
    ("green", "sdg_alignment"): (
        "SDG alignment not articulated.",
        "Map the venture to 2-3 specific UN SDGs with concrete actions.",
    ),
    ("green", "environmental_impact"): (
        "Environmental impact not assessed.",
        "Conduct a basic environmental impact assessment.",
    ),
    ("green", "ip_protection"): (
        "IP not registered despite declared IP assets.",
        "Initiate IP registration via INNORPI or the relevant authority.",
    ),
    ("green", "ai_act_compliance"): (
        "EU AI Act applicable but compliance assessment not complete.",
        "Conduct a conformity assessment and document AI system classification.",
    ),
}


def derive_blockers(result: ScoreResult, axis_slug: str) -> list[dict]:
    """Derive blockers from an Affinitree ScoreResult.

    Returns one blocker per sub-dimension below LOW_THRESHOLD that has a rule
    entry, plus one info-level blocker per missing required field.
    """
    out: list[dict] = []

    for c in result.components:
        rule = BLOCKER_RULES.get((result.score_name, c.name))
        if rule and c.raw_value < LOW_THRESHOLD:
            desc, remediation = rule
            out.append({
                "axis": axis_slug,
                "code": f"{result.score_name}.{c.name}.low",
                "description": desc,
                "severity": "critical" if c.weight >= 0.25 else "warning",
                "score_dimension": result.score_name,
                "remediation": remediation,
            })

    for mf in result.missing_fields:
        out.append({
            "axis": axis_slug,
            "code": f"missing.{mf}",
            "description": f"Required field not provided: {mf}.",
            "severity": "info",
            "score_dimension": result.score_name,
            "remediation": f"Provide '{mf}' during intake.",
        })

    return out
