"""Rule-based contradiction / unsubstantiated-signal detection.

Each rule is a pure predicate over the StartupProfile. When it fires it yields an
``Anomaly`` describing the contradiction, its severity, and the fields involved.
This is the recall test target of Tier 2c (10 contradiction profiles -> 100%).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from .profile import StartupProfile


@dataclass
class Anomaly:
    code: str
    severity: str  # critical | warning | info
    message: str
    fields: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


Rule = Callable[[StartupProfile], "Anomaly | None"]
_RULES: list[Rule] = []


def rule(fn: Rule) -> Rule:
    _RULES.append(fn)
    return fn


@rule
def revenue_without_interviews(p: StartupProfile) -> Anomaly | None:
    if p.market.mrr_usd > 0 and p.market.customer_interviews_count == 0:
        return Anomaly(
            "revenue_without_validation",
            "critical",
            "Reports monthly revenue but has conducted zero customer interviews.",
            ["market.mrr_usd", "market.customer_interviews_count"],
        )
    return None


@rule
def pilots_without_interviews(p: StartupProfile) -> Anomaly | None:
    if p.market.paid_pilots_count > 0 and p.market.customer_interviews_count == 0:
        return Anomaly(
            "pilots_without_validation",
            "warning",
            "Claims paying pilots but recorded no customer interviews.",
            ["market.paid_pilots_count", "market.customer_interviews_count"],
        )
    return None


@rule
def mature_product_concept_stage(p: StartupProfile) -> Anomaly | None:
    if p.market.mrr_usd > 0 and p.offer.product_stage in ("concept", "prototype"):
        return Anomaly(
            "revenue_without_product",
            "critical",
            "Generating revenue while the product is still at concept/prototype stage.",
            ["market.mrr_usd", "offer.product_stage"],
        )
    return None


@rule
def patent_without_prior_art(p: StartupProfile) -> Anomaly | None:
    if p.innovation.ip_type in ("patent-pending", "patent-granted") and not p.innovation.prior_art_search_done:
        return Anomaly(
            "patent_without_prior_art",
            "warning",
            "Holds or is pursuing a patent but no prior-art search was done.",
            ["innovation.ip_type", "innovation.prior_art_search_done"],
        )
    return None


@rule
def high_trl_concept_stage(p: StartupProfile) -> Anomaly | None:
    if p.innovation.tech_readiness_level >= 8 and p.offer.product_stage in ("concept", "prototype"):
        return Anomaly(
            "trl_stage_mismatch",
            "warning",
            "Declares a high technology-readiness level but only a concept/prototype product.",
            ["innovation.tech_readiness_level", "offer.product_stage"],
        )
    return None


@rule
def ltv_without_cac(p: StartupProfile) -> Anomaly | None:
    if (p.finance.ltv_usd or 0) > 0 and not p.finance.cac_usd:
        return Anomaly(
            "ltv_without_cac",
            "warning",
            "Provides a customer lifetime value but no acquisition cost, so unit economics cannot be verified.",
            ["finance.ltv_usd", "finance.cac_usd"],
        )
    return None


@rule
def negative_unit_economics(p: StartupProfile) -> Anomaly | None:
    cac, ltv = p.finance.cac_usd, p.finance.ltv_usd
    if cac and ltv is not None and ltv < cac:
        return Anomaly(
            "negative_unit_economics",
            "critical",
            "Customer acquisition cost exceeds lifetime value (LTV < CAC).",
            ["finance.ltv_usd", "finance.cac_usd"],
        )
    return None


@rule
def critical_runway(p: StartupProfile) -> Anomaly | None:
    if p.finance.runway_months is not None and p.finance.runway_months < 3:
        return Anomaly(
            "critical_runway",
            "critical",
            "Cash runway is below three months.",
            ["finance.runway_months"],
        )
    return None


@rule
def ai_act_applicable_not_compliant(p: StartupProfile) -> Anomaly | None:
    if p.legal.ai_act_applicable and not p.legal.ai_act_compliant:
        return Anomaly(
            "ai_act_noncompliance",
            "critical",
            "Product is in EU AI Act scope but no conformity assessment is completed.",
            ["legal.ai_act_applicable", "legal.ai_act_compliant"],
        )
    return None


@rule
def revenue_no_revenue_model(p: StartupProfile) -> Anomaly | None:
    if p.market.mrr_usd > 0 and p.market.revenue_model == "none":
        return Anomaly(
            "revenue_without_model",
            "warning",
            "Reports recurring revenue but the declared revenue model is 'none'.",
            ["market.mrr_usd", "market.revenue_model"],
        )
    return None


def detect(profile: StartupProfile) -> list[Anomaly]:
    """Run all rules and return the anomalies that fired."""
    found: list[Anomaly] = []
    for r in _RULES:
        a = r(profile)
        if a is not None:
            found.append(a)
    return found
