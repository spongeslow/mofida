"""Investor-grade due diligence checks per axis.

These are deterministic, rule-based checks that go beyond the Affinitree
score to surface concerns an investor or analyst would flag during a formal
due diligence review. They complement blockers (which derive from the scoring
model thresholds) with cross-field reasoning and investor-readiness assessment.

Each check returns a flag dict with:
  code          — machine-readable identifier
  category      — DD domain (e.g. competitive_landscape, unit_economics)
  severity      — critical | warning | info
  description   — what was found
  investor_concern — why this matters to an investor
  remediation   — the concrete next step

run_due_diligence(profile, axis_slug) returns:
  flags           — list of flag dicts
  readiness_score — 0.0–1.0 (1.0 = no flags)
  critical_count  — int
  warning_count   — int
  info_count      — int
"""
from __future__ import annotations

from typing import Callable

from .profile import StartupProfile

DDCheck = Callable[[StartupProfile], "dict | None"]

# axis_slug -> list of check functions
_AXIS_CHECKS: dict[str, list[DDCheck]] = {}

# Penalty per severity level toward the readiness_score
_PENALTY: dict[str, float] = {"critical": 0.30, "warning": 0.15, "info": 0.05}


def _register(*slugs: str):
    """Decorator: register a check for one or more axis slugs."""
    def decorator(fn: DDCheck) -> DDCheck:
        for slug in slugs:
            _AXIS_CHECKS.setdefault(slug, []).append(fn)
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Market (Axis 02) — Market Due Diligence
# ---------------------------------------------------------------------------

@_register("market")
def dd_market_no_competitor_analysis(p: StartupProfile) -> dict | None:
    if p.market.competitor_count == 0:
        return {
            "code": "market.no_competitor_analysis",
            "category": "competitive_landscape",
            "severity": "critical",
            "description": "Zero competitors declared — every market has direct or indirect alternatives.",
            "investor_concern": (
                "Claiming no competition is a classic red flag: it signals insufficient market research, "
                "not market leadership. Investors will probe this first."
            ),
            "remediation": "Map 3–5 direct and indirect competitors with names, funding status, and your differentiation gaps.",
        }
    return None


@_register("market")
def dd_market_no_market_size_data(p: StartupProfile) -> dict | None:
    if p.market.tam_usd is None and p.market.sam_usd is None:
        return {
            "code": "market.no_market_size_data",
            "category": "market_sizing",
            "severity": "critical",
            "description": "No TAM or SAM data provided — market opportunity is completely unquantified.",
            "investor_concern": (
                "VCs require a credible market-sizing model (TAM/SAM/SOM) to evaluate return potential. "
                "Without this, no investment thesis can be constructed."
            ),
            "remediation": "Build a bottom-up TAM/SAM/SOM model and document your assumptions and data sources.",
        }
    return None


@_register("market")
def dd_market_sam_without_tam(p: StartupProfile) -> dict | None:
    if p.market.sam_usd is not None and p.market.tam_usd is None:
        return {
            "code": "market.sam_without_tam",
            "category": "market_sizing",
            "severity": "warning",
            "description": "SAM provided without a TAM — market sizing methodology is incomplete.",
            "investor_concern": (
                "Investors expect a top-down TAM alongside the bottom-up SAM to triangulate market size."
            ),
            "remediation": "Add a TAM estimate with a credible source (industry report, regulatory body data).",
        }
    return None


@_register("market")
def dd_market_revenue_undocumented(p: StartupProfile) -> dict | None:
    if p.market.mrr_usd > 0 and not p.market.customer_interviews_doc:
        return {
            "code": "market.revenue_without_documentation",
            "category": "customer_validation",
            "severity": "warning",
            "description": "Revenue reported but no customer interview or contract documentation uploaded.",
            "investor_concern": (
                "Self-reported revenue without documentation is T1 evidence. "
                "Investors will require bank statements or signed contracts for verification."
            ),
            "remediation": "Upload customer contracts, receipts, or signed LOIs to upgrade to T2 evidence.",
        }
    return None


@_register("market")
def dd_market_high_funded_competition(p: StartupProfile) -> dict | None:
    if p.market.competitor_funded_count >= 3:
        return {
            "code": "market.high_funded_competition",
            "category": "competitive_landscape",
            "severity": "warning",
            "description": f"{p.market.competitor_funded_count} funded competitors identified — highly competitive market.",
            "investor_concern": (
                "Multiple funded competitors increase capital requirements and compress pricing power. "
                "Investors will ask why this venture wins."
            ),
            "remediation": "Articulate a specific, defensible moat: network effects, exclusive data, IP, or switching costs.",
        }
    return None


# ---------------------------------------------------------------------------
# Commercial Offer / Product (Axis 03) — Commercial Due Diligence
# ---------------------------------------------------------------------------

@_register("product")
def dd_product_no_value_proposition(p: StartupProfile) -> dict | None:
    if not p.offer.value_prop_text.strip():
        return {
            "code": "product.no_value_proposition",
            "category": "value_proposition",
            "severity": "critical",
            "description": "No value proposition text provided.",
            "investor_concern": (
                "A startup without a documented value proposition cannot explain why customers should choose it. "
                "This blocks all commercial due diligence."
            ),
            "remediation": (
                "Write a one-sentence value proposition: "
                "[Target segment] + [Problem solved] + [Measurable benefit]."
            ),
        }
    return None


@_register("product")
def dd_product_undefined_pricing_at_mvp(p: StartupProfile) -> dict | None:
    if p.offer.product_stage in ("mvp", "ga", "mature") and p.offer.pricing_model == "undefined":
        return {
            "code": "product.undefined_pricing_at_mvp",
            "category": "commercial_model",
            "severity": "critical",
            "description": f"Product is at '{p.offer.product_stage}' stage but pricing model is undefined.",
            "investor_concern": (
                "Undefined pricing at MVP+ indicates an unvalidated business model. "
                "Investors will not proceed without a clear monetisation path."
            ),
            "remediation": "Define and test a pricing model; value-based pricing is preferred for B2B SaaS.",
        }
    return None


@_register("product")
def dd_product_no_differentiation_documented(p: StartupProfile) -> dict | None:
    if not p.offer.differentiation_text.strip():
        return {
            "code": "product.no_differentiation_documented",
            "category": "competitive_positioning",
            "severity": "warning",
            "description": "No competitive differentiation documented.",
            "investor_concern": (
                "Without documented differentiation, an investor cannot assess the durability of the competitive position."
            ),
            "remediation": "Document 3 specific differentiators vs. named competitors, backed by evidence (IP, data, partnerships).",
        }
    return None


@_register("product")
def dd_product_concept_stage(p: StartupProfile) -> dict | None:
    if p.offer.product_stage == "concept":
        return {
            "code": "product.pre_mvp_stage",
            "category": "product_maturity",
            "severity": "warning",
            "description": "Product is still at concept stage — no functional artefact exists.",
            "investor_concern": (
                "Pre-MVP companies face maximum execution risk. "
                "Most seed investors require at least a functional prototype."
            ),
            "remediation": "Build a prototype or MVP to demonstrate technical feasibility before fundraising.",
        }
    return None


# ---------------------------------------------------------------------------
# Brand / Innovation (Axis 04) — Innovation & IP Due Diligence
# ---------------------------------------------------------------------------

@_register("brand")
def dd_innovation_no_ip_at_ga(p: StartupProfile) -> dict | None:
    if p.offer.product_stage in ("ga", "mature") and p.innovation.ip_type == "none":
        return {
            "code": "innovation.no_ip_at_market_stage",
            "category": "intellectual_property",
            "severity": "critical",
            "description": "Product is in GA/mature stage with no IP protection.",
            "investor_concern": (
                "A GA-stage product without IP protection is fully exposed to imitation. "
                "Investors require defensibility evidence before committing capital."
            ),
            "remediation": "File a patent, register a trademark, or document trade-secret protection via INNORPI.",
        }
    return None


@_register("brand")
def dd_innovation_high_trl_no_ip(p: StartupProfile) -> dict | None:
    if p.innovation.tech_readiness_level >= 6 and p.innovation.ip_type == "none":
        return {
            "code": "innovation.trl_6_plus_no_ip",
            "category": "intellectual_property",
            "severity": "warning",
            "description": f"Technology is at TRL {p.innovation.tech_readiness_level} but has no IP protection.",
            "investor_concern": (
                "Advanced technology without IP protection is exposed to copying once publicly demonstrated."
            ),
            "remediation": "Assess patentability of core technology and file a provisional application.",
        }
    return None


@_register("brand")
def dd_innovation_sector_first_no_ip(p: StartupProfile) -> dict | None:
    if p.innovation.sector_first and p.innovation.ip_type == "none":
        return {
            "code": "innovation.sector_first_no_ip",
            "category": "intellectual_property",
            "severity": "warning",
            "description": "Claims to be first-in-sector but has no IP protection.",
            "investor_concern": (
                "Being first without IP means competitors can follow immediately once the market is validated. "
                "First-mover advantage is temporary without barriers."
            ),
            "remediation": "Secure IP protection before announcing the sector-first position publicly.",
        }
    return None


@_register("brand")
def dd_innovation_patent_no_prior_art(p: StartupProfile) -> dict | None:
    if p.innovation.ip_type in ("patent-pending", "patent-granted") and not p.innovation.prior_art_search_done:
        return {
            "code": "innovation.patent_without_prior_art_search",
            "category": "intellectual_property",
            "severity": "warning",
            "description": "Patent claimed without a prior-art search.",
            "investor_concern": (
                "A patent filed without prior-art research risks invalidation. "
                "This signals IP management gaps that legal DD will surface."
            ),
            "remediation": "Conduct a formal prior-art search via INNORPI or a patent attorney.",
        }
    return None


@_register("brand")
def dd_innovation_no_brand_positioning(p: StartupProfile) -> dict | None:
    if not p.innovation.brand_distinctiveness_text.strip():
        return {
            "code": "innovation.no_brand_positioning",
            "category": "brand_identity",
            "severity": "info",
            "description": "No brand positioning statement documented.",
            "investor_concern": (
                "Brand positioning is essential for commercial and marketing DD, "
                "particularly in consumer-facing sectors."
            ),
            "remediation": "Write a brand positioning statement: target audience, core promise, and tone of voice.",
        }
    return None


# ---------------------------------------------------------------------------
# Business Model / Scalability (Axis 05) — Financial Due Diligence
# ---------------------------------------------------------------------------

@_register("business-model")
def dd_finance_no_unit_economics_at_mvp(p: StartupProfile) -> dict | None:
    if (
        p.offer.product_stage in ("mvp", "ga", "mature")
        and p.finance.cac_usd is None
        and p.finance.ltv_usd is None
    ):
        return {
            "code": "finance.no_unit_economics",
            "category": "unit_economics",
            "severity": "critical",
            "description": "No CAC or LTV data at MVP+ stage — unit economics completely unvalidated.",
            "investor_concern": (
                "Investors will not fund scaling without validated unit economics. "
                "This is a hard stop for Series A and beyond."
            ),
            "remediation": (
                "Measure CAC from your acquisition spend and estimate LTV "
                "from cohort data, contract value, or churn rate."
            ),
        }
    return None


@_register("business-model")
def dd_finance_negative_unit_economics(p: StartupProfile) -> dict | None:
    cac, ltv = p.finance.cac_usd, p.finance.ltv_usd
    if cac and ltv is not None and cac > 0 and ltv < cac:
        ratio = ltv / cac
        return {
            "code": "finance.negative_unit_economics",
            "category": "unit_economics",
            "severity": "critical",
            "description": f"LTV/CAC = {ratio:.2f} (< 1.0) — acquiring customers destroys value.",
            "investor_concern": (
                "A LTV/CAC ratio below 1.0 is a deal-breaker: the business loses money on every customer acquired. "
                "Scaling this model accelerates losses."
            ),
            "remediation": "Reduce CAC (improve conversion, lower ad spend) or increase LTV (upsell, reduce churn).",
        }
    return None


@_register("business-model")
def dd_finance_critical_runway(p: StartupProfile) -> dict | None:
    if p.finance.runway_months is not None and p.finance.runway_months < 3:
        return {
            "code": "finance.critical_runway",
            "category": "financial_health",
            "severity": "critical",
            "description": f"Cash runway is {p.finance.runway_months:.1f} months — existential risk.",
            "investor_concern": (
                "A runway under 3 months means the company may not survive due diligence. "
                "Most investors will not engage with a company in distress."
            ),
            "remediation": "Immediately cut non-essential burn and initiate emergency fundraising or revenue acceleration.",
        }
    return None


@_register("business-model")
def dd_finance_short_runway(p: StartupProfile) -> dict | None:
    if p.finance.runway_months is not None and 3 <= p.finance.runway_months < 6:
        return {
            "code": "finance.short_runway",
            "category": "financial_health",
            "severity": "warning",
            "description": f"Cash runway is {p.finance.runway_months:.1f} months (< 6 months).",
            "investor_concern": (
                "Runway under 6 months creates fundraising urgency that weakens negotiating position "
                "and signals poor financial planning."
            ),
            "remediation": "Raise a bridge round or extend runway to at least 12 months before a Series A process.",
        }
    return None


@_register("business-model")
def dd_finance_burn_not_tracked(p: StartupProfile) -> dict | None:
    if p.finance.funding_stage != "bootstrapped" and p.finance.burn_rate_usd is None:
        return {
            "code": "finance.burn_rate_not_tracked",
            "category": "financial_management",
            "severity": "warning",
            "description": "Funded startup has no burn rate data.",
            "investor_concern": (
                "Investors expect funded startups to track monthly burn precisely. "
                "Absence of this data suggests financial management gaps."
            ),
            "remediation": "Set up a monthly P&L tracker and document burn rate and cash position.",
        }
    return None


@_register("business-model")
def dd_finance_no_revenue_model_at_mvp(p: StartupProfile) -> dict | None:
    if p.offer.product_stage in ("mvp", "ga", "mature") and p.market.revenue_model == "none":
        return {
            "code": "finance.no_revenue_model_at_mvp",
            "category": "commercial_model",
            "severity": "critical",
            "description": "No revenue model defined at MVP+ stage.",
            "investor_concern": "A product in the market without a revenue model is not a business.",
            "remediation": (
                "Define how the venture monetises: subscription, transactional, marketplace, or usage-based."
            ),
        }
    return None


# ---------------------------------------------------------------------------
# Legal / Green (Axis 06) — Legal & ESG Due Diligence
# ---------------------------------------------------------------------------

@_register("legal")
def dd_legal_no_data_policy_digital(p: StartupProfile) -> dict | None:
    if p.sector == "digital-tech" and not p.legal.gdpr_policy_exists:
        return {
            "code": "legal.no_gdpr_policy_digital_product",
            "category": "regulatory_compliance",
            "severity": "critical",
            "description": "Digital-tech startup has no GDPR/data protection policy.",
            "investor_concern": (
                "GDPR non-compliance is a hard blocker for EU market access and most institutional investors. "
                "It creates material legal liability and can result in significant fines."
            ),
            "remediation": "Draft and publish a privacy policy; implement data processing agreements with all data processors.",
        }
    return None


@_register("legal")
def dd_legal_no_data_policy_with_customers(p: StartupProfile) -> dict | None:
    if not p.legal.gdpr_policy_exists and p.market.customer_interviews_count > 0:
        return {
            "code": "legal.no_data_policy_with_customer_data",
            "category": "regulatory_compliance",
            "severity": "warning",
            "description": "Collecting customer data (interviews/pilots) without a data protection policy.",
            "investor_concern": (
                "Any collection of personal data without a privacy policy creates legal exposure "
                "under Tunisian Law 2004-63 and GDPR for EU-linked operations."
            ),
            "remediation": "Implement a basic data protection policy aligned with Tunisian Organic Law 2004-63.",
        }
    return None


@_register("legal")
def dd_legal_ai_act_gap(p: StartupProfile) -> dict | None:
    if p.legal.ai_act_applicable and not p.legal.ai_act_compliant:
        return {
            "code": "legal.ai_act_compliance_gap",
            "category": "regulatory_compliance",
            "severity": "critical",
            "description": "Product falls under EU AI Act scope but conformity assessment not completed.",
            "investor_concern": (
                "EU AI Act non-compliance blocks EU market access entirely. "
                "EU-focused investors will not invest in non-compliant AI systems."
            ),
            "remediation": (
                "Engage an AI Act compliance specialist; complete system classification "
                "and conformity documentation before any EU launch."
            ),
        }
    return None


@_register("legal")
def dd_legal_ip_declared_not_registered(p: StartupProfile) -> dict | None:
    if p.innovation.ip_type != "none" and not p.legal.ip_registered:
        return {
            "code": "legal.ip_declared_but_not_registered",
            "category": "intellectual_property",
            "severity": "warning",
            "description": f"IP type declared as '{p.innovation.ip_type}' but formal registration not confirmed.",
            "investor_concern": (
                "Unregistered IP claims are legally unenforceable and will not survive legal DD. "
                "Investors will discount IP value to zero without registration evidence."
            ),
            "remediation": (
                "Complete IP registration via INNORPI (Tunisia) or file via PCT for international protection."
            ),
        }
    return None


@_register("legal")
def dd_legal_sdg_claims_no_measurement(p: StartupProfile) -> dict | None:
    if p.legal.sdg_alignment_text.strip() and not p.legal.environmental_impact_assessed:
        return {
            "code": "legal.sdg_claims_without_impact_measurement",
            "category": "esg_impact",
            "severity": "info",
            "description": "SDG alignment claimed but no environmental impact assessment conducted.",
            "investor_concern": (
                "ESG-focused investors require measurable impact evidence, not just claimed alignment. "
                "Unsubstantiated ESG claims risk greenwashing exposure."
            ),
            "remediation": (
                "Conduct an environmental/social impact assessment and define measurable KPIs per SDG."
            ),
        }
    return None


# ---------------------------------------------------------------------------
# Operations (Axis 09) — Operational Due Diligence
# ---------------------------------------------------------------------------

@_register("operations")
def dd_ops_single_supplier_dependency(p: StartupProfile) -> dict | None:
    if p.ops.supply_chain_single_point:
        return {
            "code": "ops.single_supplier_dependency",
            "category": "operational_resilience",
            "severity": "critical",
            "description": "Supply chain has a single point of failure — one supplier disruption halts operations.",
            "investor_concern": (
                "Single-supplier dependency is an operational risk that investors require documented mitigation for. "
                "It surfaces in operational DD and can block term sheets."
            ),
            "remediation": "Identify backup suppliers for all critical inputs and establish dual-sourcing agreements.",
        }
    return None


@_register("operations")
def dd_ops_no_sop(p: StartupProfile) -> dict | None:
    if not p.ops.sop_documented:
        return {
            "code": "ops.no_standard_operating_procedures",
            "category": "operational_maturity",
            "severity": "warning",
            "description": "No standard operating procedures documented.",
            "investor_concern": (
                "Without SOPs, operations depend entirely on key individuals. "
                "This is a key-person risk and a scalability ceiling that investors flag in operational DD."
            ),
            "remediation": "Document the 5 most critical operational processes to enable delegation and quality control.",
        }
    return None


@_register("operations")
def dd_ops_highly_manual(p: StartupProfile) -> dict | None:
    if p.ops.manual_steps_pct is not None and p.ops.manual_steps_pct > 80:
        return {
            "code": "ops.highly_manual_operations",
            "category": "scalability",
            "severity": "warning",
            "description": f"{p.ops.manual_steps_pct:.0f}% of operations are manual — not scalable.",
            "investor_concern": (
                "Highly manual operations cap growth at headcount and destroy unit economics at scale. "
                "Investors will require an automation roadmap."
            ),
            "remediation": "Map operational bottlenecks and implement automation for the highest-volume manual tasks.",
        }
    return None


# ---------------------------------------------------------------------------
# Marketing (Axis 07) — Commercial / Brand Readiness DD
# ---------------------------------------------------------------------------

@_register("marketing")
def dd_marketing_no_brand_identity(p: StartupProfile) -> dict | None:
    if not p.offer.brand_name_registered and not p.offer.logo_exists:
        return {
            "code": "marketing.no_brand_identity",
            "category": "brand_readiness",
            "severity": "warning",
            "description": "No registered brand name or logo — brand identity not established.",
            "investor_concern": (
                "A startup without basic brand assets cannot execute marketing campaigns effectively "
                "or protect its market position."
            ),
            "remediation": "Register a brand name and create a minimal visual identity (logo, colours, typography).",
        }
    return None


@_register("marketing")
def dd_marketing_revenue_no_marketing_infra(p: StartupProfile) -> dict | None:
    if p.market.mrr_usd > 0 and not p.offer.brand_name_registered and not p.offer.logo_exists:
        return {
            "code": "marketing.revenue_without_marketing_infrastructure",
            "category": "brand_readiness",
            "severity": "info",
            "description": "Generating revenue without a formal marketing infrastructure.",
            "investor_concern": (
                "Revenue driven purely by founder network is not scalable or repeatable. "
                "Investors will probe whether there is a marketing engine."
            ),
            "remediation": "Build a minimum marketing stack: brand, website, lead capture, and one repeatable acquisition channel.",
        }
    return None


# ---------------------------------------------------------------------------
# Sales (Axis 08) — Sales Due Diligence
# ---------------------------------------------------------------------------

@_register("sales")
def dd_sales_no_paying_customers_at_mvp(p: StartupProfile) -> dict | None:
    if (
        p.offer.product_stage in ("mvp", "ga", "mature")
        and p.market.paid_pilots_count == 0
        and p.market.mrr_usd == 0
    ):
        return {
            "code": "sales.no_paying_customers_at_mvp",
            "category": "sales_traction",
            "severity": "critical",
            "description": "No paying customers at MVP+ stage.",
            "investor_concern": (
                "Zero revenue at MVP is the primary indicator of product-market fit failure. "
                "Seed and later-stage investors will not proceed without traction evidence."
            ),
            "remediation": "Focus exclusively on closing the first 5 paying customers before further product development.",
        }
    return None


@_register("sales")
def dd_sales_pilots_without_cac(p: StartupProfile) -> dict | None:
    if p.market.paid_pilots_count > 0 and p.finance.cac_usd is None:
        return {
            "code": "sales.pilots_without_cac_tracking",
            "category": "sales_efficiency",
            "severity": "warning",
            "description": "Has paying pilots but CAC not tracked.",
            "investor_concern": (
                "Without CAC data, the sales efficiency and scalability of acquisition cannot be assessed."
            ),
            "remediation": (
                "Calculate acquisition cost per pilot: "
                "total sales + marketing spend ÷ number of pilots acquired."
            ),
        }
    return None


@_register("sales")
def dd_sales_no_customer_discovery(p: StartupProfile) -> dict | None:
    if p.market.customer_interviews_count == 0:
        return {
            "code": "sales.no_customer_discovery",
            "category": "customer_validation",
            "severity": "critical",
            "description": "No customer discovery interviews conducted.",
            "investor_concern": (
                "Zero customer interviews is the strongest signal of a solution in search of a problem. "
                "Investors see this as a fundamental product-market fit risk."
            ),
            "remediation": "Run at least 5 structured problem interviews with target customers.",
        }
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_due_diligence(profile: StartupProfile, axis_slug: str) -> dict:
    """Run all DD checks for the given axis and return a structured summary."""
    checks = _AXIS_CHECKS.get(axis_slug, [])
    flags: list[dict] = []
    for check in checks:
        result = check(profile)
        if result is not None:
            flags.append(result)

    penalty = sum(_PENALTY.get(f["severity"], 0.0) for f in flags)
    readiness = round(max(0.0, 1.0 - penalty), 2)

    return {
        "flags": flags,
        "readiness_score": readiness,
        "critical_count": sum(1 for f in flags if f["severity"] == "critical"),
        "warning_count": sum(1 for f in flags if f["severity"] == "warning"),
        "info_count": sum(1 for f in flags if f["severity"] == "info"),
    }
