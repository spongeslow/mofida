import json

import pytest

from affinitree import StartupProfile, detect, score
from affinitree.scorer import SCORE_CONFIGS, load_config

STRONG = StartupProfile(
    sector="digital-tech",
    market={"sam_usd": 30_000_000, "customer_interviews_count": 25, "paid_pilots_count": 4,
            "revenue_model": "subscription", "mrr_usd": 8000, "competitor_count": 3,
            "customer_interviews_doc": True},
    offer={"product_stage": "mvp", "pricing_model": "value-based"},
    innovation={"tech_readiness_level": 7, "ip_type": "patent-pending",
                "prior_art_search_done": True, "sector_first": True},
    finance={"cac_usd": 100, "ltv_usd": 500, "gross_margin_pct": 65,
             "runway_months": 10, "funding_stage": "seed"},
    ops={"manual_steps_pct": 30, "sop_documented": True, "supply_chain_single_point": False},
    legal={"gdpr_policy_exists": True, "tunisia_data_law_compliant": True,
           "ip_registered": True, "environmental_impact_assessed": True},
    rubric_scores={"offer.value_prop_text": 3, "offer.differentiation_text": 3,
                   "innovation.novelty_text": 3, "innovation.brand_distinctiveness_text": 2,
                   "legal.sdg_alignment_text": 3},
    evidence_tiers={"market.mrr_usd": "T2", "market.competitor_count": "T3"},
)


@pytest.mark.parametrize("name", list(SCORE_CONFIGS))
def test_score_in_range(name):
    r = score(STRONG, name)
    assert 0.0 <= r.score <= 5.0
    assert r.components, "every score must have components"


@pytest.mark.parametrize("name", list(SCORE_CONFIGS))
def test_determinism(name):
    runs = {json.dumps(score(STRONG, name).to_dict(), sort_keys=True) for _ in range(10)}
    assert len(runs) == 1


@pytest.mark.parametrize("name", list(SCORE_CONFIGS))
def test_weights_sum_to_one(name):
    cfg = load_config(name)
    total = sum(s["weight"] for s in cfg["sub_dimensions"])
    assert total == pytest.approx(1.0, abs=1e-9)


def test_evidence_tier_raises_score():
    """Same data, stronger evidence -> higher score (mi effect)."""
    base = StartupProfile(market={"sam_usd": 30_000_000, "mrr_usd": 5000,
                                  "revenue_model": "subscription"})
    verified = base.model_copy(update={"evidence_tiers": {
        "market.sam_usd": "T2", "market.mrr_usd": "T2"}})
    assert score(verified, "market").score > score(base, "market").score


def test_empty_profile_scores_low():
    empty = StartupProfile()
    for name in SCORE_CONFIGS:
        assert score(empty, name).score < 2.5


def test_innovation_matches_listing2_weights():
    cfg = load_config("innovation")
    weights = {s["id"]: s["weight"] for s in cfg["sub_dimensions"]}
    assert weights == {
        "product_novelty": 0.35,
        "market_novelty": 0.25,
        "brand_distinctiveness": 0.20,
        "value_creation_novelty": 0.20,
    }


def test_anomaly_clean_profile():
    assert detect(STRONG) == []
