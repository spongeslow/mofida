"""StartupProfile schema (Table 1 field catalogue) and the three-tier evidence model.

Fields are grouped into the five domains read by Affinitree: market, offer,
innovation, finance, ops, legal. Each leaf field can carry an evidence tier that
determines its confidence multiplier ``mi`` during scoring:

    T1 -- Declared (self-reported)         -> x0.6
    T2 -- Artefact-backed (uploaded proof) -> x1.0
    T3 -- Daemon-observed (Go watcher)     -> x1.2
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

EvidenceTier = Literal["T1", "T2", "T3"]

TIER_MULTIPLIER: dict[str, float] = {"T1": 0.6, "T2": 1.0, "T3": 1.2}


class MarketFields(BaseModel):
    tam_usd: Optional[float] = None
    sam_usd: Optional[float] = None
    customer_interviews_count: int = 0
    paid_pilots_count: int = 0
    nps_score: Optional[float] = None
    revenue_model: Literal["none", "usage", "subscription", "transactional", "marketplace"] = "none"
    mrr_usd: float = 0.0
    competitor_count: int = 0
    competitor_funded_count: int = 0
    customer_interviews_doc: bool = False


class OfferFields(BaseModel):
    value_prop_text: str = ""
    product_stage: Literal["concept", "prototype", "mvp", "ga", "mature"] = "concept"
    pricing_model: Literal["undefined", "cost-plus", "value-based", "freemium", "other"] = "undefined"
    price_point_usd: Optional[float] = None
    differentiation_text: str = ""
    brand_name_registered: bool = False
    logo_exists: bool = False


class InnovationFields(BaseModel):
    tech_readiness_level: int = 1  # TRL 1-9
    ip_type: Literal["none", "trade-secret", "patent-pending", "patent-granted", "copyright"] = "none"
    prior_art_search_done: bool = False
    novelty_text: str = ""
    sector_first: bool = False
    brand_distinctiveness_text: str = ""


class FinanceFields(BaseModel):
    cac_usd: Optional[float] = None
    ltv_usd: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    runway_months: Optional[float] = None
    burn_rate_usd: Optional[float] = None
    funding_stage: Literal["bootstrapped", "pre-seed", "seed", "series-a", "series-b-plus"] = "bootstrapped"


class OpsFields(BaseModel):
    manual_steps_pct: Optional[float] = None
    sop_documented: bool = False
    supply_chain_single_point: bool = False


class LegalFields(BaseModel):
    gdpr_policy_exists: bool = False
    tunisia_data_law_compliant: bool = False
    ip_registered: bool = False
    sdg_alignment_text: str = ""
    environmental_impact_assessed: bool = False
    ai_act_applicable: bool = False
    ai_act_compliant: bool = False


class StartupProfile(BaseModel):
    """Full profile read by Affinitree. ``sector`` and ``self_assessed_stage`` are
    used by the diagnostic pipeline; the six domain blocks feed the scorer."""

    project_id: Optional[str] = None
    sector: Literal["agri-food", "digital-tech", "industry", "cross-sector"] = "cross-sector"
    self_assessed_stage: Optional[str] = None
    language: Literal["fr", "ar"] = "fr"

    market: MarketFields = Field(default_factory=MarketFields)
    offer: OfferFields = Field(default_factory=OfferFields)
    innovation: InnovationFields = Field(default_factory=InnovationFields)
    finance: FinanceFields = Field(default_factory=FinanceFields)
    ops: OpsFields = Field(default_factory=OpsFields)
    legal: LegalFields = Field(default_factory=LegalFields)

    # Explicit evidence-tier overrides keyed by dotted field path, e.g.
    # {"market.mrr_usd": "T2", "market.competitor_count": "T3"}. Anything absent
    # defaults to T1 (declared).
    evidence_tiers: dict[str, EvidenceTier] = Field(default_factory=dict)

    # Cached rubric scores (0-4 integers) for free-text fields, keyed by dotted
    # field path. Populated by rubric.py so the deterministic scorer never has to
    # call an LLM inline. e.g. {"offer.value_prop_text": 3}
    rubric_scores: dict[str, int] = Field(default_factory=dict)

    # ----- accessors ------------------------------------------------------

    def get(self, dotted_path: str):
        """Resolve a dotted field path like ``market.mrr_usd`` to its value."""
        obj = self
        for part in dotted_path.split("."):
            obj = getattr(obj, part)
        return obj

    def tier(self, dotted_path: str) -> EvidenceTier:
        """Evidence tier for a field. Doc-flag fields auto-upgrade their subject
        to T2 unless an explicit override says otherwise."""
        if dotted_path in self.evidence_tiers:
            return self.evidence_tiers[dotted_path]
        # Implicit upgrade: an uploaded interview doc backs the interview count.
        if dotted_path == "market.customer_interviews_count" and self.market.customer_interviews_doc:
            return "T2"
        return "T1"

    def tier_multiplier(self, dotted_path: str) -> float:
        return TIER_MULTIPLIER[self.tier(dotted_path)]
