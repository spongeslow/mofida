"""Unit tests for the Computerized Adaptive Testing (CAT) intake engine.

Covers the pure IRT numerics (``app.cat.irt``) and the stateless two-phase
session logic (``app.cat.session``). The reference for the expected behaviour is
``docs/research/computerized-adaptive-testing.md``.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.cat import irt, session


# ---------------------------------------------------------------------------
# Item bank integrity
# ---------------------------------------------------------------------------

def test_bank_meta_shape():
    assert len(irt.STAGE_NAMES) == 6
    # 6 stages ⇒ 5 internal boundaries.
    assert len(irt._STAGE_BOUNDARIES) == 5
    # Boundaries strictly increasing.
    assert irt._STAGE_BOUNDARIES == sorted(irt._STAGE_BOUNDARIES)


def test_every_item_is_wellformed():
    for iid, it in irt.ITEMS.items():
        assert it["a"] > 0, f"{iid}: discrimination must be positive"
        assert isinstance(it["b"], (int, float)), iid
        assert it["field"], f"{iid}: needs a profile field"
        assert it["pool"], f"{iid}: needs a pool"
        assert it["type"] in ("select", "text"), f"{iid}: bad type {it['type']}"
        assert it["question_fr"] and it["question_ar"], f"{iid}: missing translation"
        if it["type"] == "select":
            assert it["options"], f"{iid}: select item needs options"
            for opt in it["options"]:
                assert 0.0 <= opt["credit"] <= 1.0, f"{iid}: credit out of range"
                assert "label_fr" in opt and "label_ar" in opt
                assert "value" in opt


def test_pools_cover_phase1_and_every_axis():
    pools = {it["pool"] for it in irt.ITEMS.values()}
    assert "phase1" in pools
    # Every Phase-2 axis has its own pool of items.
    for axis in session.PHASE2_AXES:
        assert axis in pools, f"no item pool for axis '{axis}'"


def test_phase1_pool_has_enough_items_for_ceiling():
    phase1 = [iid for iid, it in irt.ITEMS.items() if it["pool"] == "phase1"]
    # Must be able to satisfy the hard Phase-1 ceiling.
    assert len(phase1) >= session.MAX_PHASE1


# ---------------------------------------------------------------------------
# 2PL item response function
# ---------------------------------------------------------------------------

def test_prob_is_half_at_difficulty():
    # P_j(θ) = 0.5 exactly when θ == b_j.
    assert abs(irt.prob_correct(theta=0.7, a=1.5, b=0.7) - 0.5) < 1e-12


def test_prob_monotonic_in_theta():
    a, b = 1.5, 0.0
    lo = irt.prob_correct(-2.0, a, b)
    mid = irt.prob_correct(0.0, a, b)
    hi = irt.prob_correct(2.0, a, b)
    assert lo < mid < hi
    assert lo < 0.5 < hi


def test_higher_discrimination_is_steeper():
    # A more discriminating item separates above/below its difficulty harder.
    b = 0.0
    sharp = irt.prob_correct(0.5, a=2.5, b=b)
    flat = irt.prob_correct(0.5, a=0.5, b=b)
    assert sharp > flat  # both above b, sharper item climbs faster


# ---------------------------------------------------------------------------
# Fisher information
# ---------------------------------------------------------------------------

def test_information_peaks_at_difficulty():
    # I_j(θ) is maximised at θ = b_j.
    iid = next(i for i, it in irt.ITEMS.items() if it["pool"] == "phase1")
    b = irt.ITEMS[iid]["b"]
    at_b = irt.item_information(iid, b)
    assert at_b > irt.item_information(iid, b + 1.5)
    assert at_b > irt.item_information(iid, b - 1.5)


def test_information_zero_for_unknown_item():
    assert irt.item_information("does_not_exist", 0.0) == 0.0


# ---------------------------------------------------------------------------
# EAP estimator
# ---------------------------------------------------------------------------

def test_empty_history_returns_prior():
    theta, se, weights = irt.eap_estimate([])
    # Posterior == N(0, 1) prior.
    assert abs(theta) < 1e-6
    assert abs(se - 1.0) < 0.02
    assert abs(sum(weights) - 1.0) < 1e-9


def test_strong_hard_answers_push_theta_up_and_shrink_se():
    # Credit 1.0 on high-difficulty items ⇒ high maturity, lower uncertainty.
    resp = [("p1_external_funding", 1.0), ("p1_signed_customers", 1.0),
            ("p1_pmf_evidence", 1.0)]
    theta, se, _ = irt.eap_estimate(resp)
    assert theta > 1.0
    assert se < 0.9  # below prior SE


def test_weak_easy_answers_push_theta_down():
    resp = [("p1_customer_interviews", 0.0), ("p1_wtp_signal", 0.0),
            ("p1_mvp_exists", 0.0)]
    theta, _, _ = irt.eap_estimate(resp)
    assert theta < -0.5


def test_graded_credit_is_monotonic():
    # Same item, larger credit ⇒ larger θ̂.
    low, _, _ = irt.eap_estimate([("p1_revenue_model", 0.0)])
    mid, _, _ = irt.eap_estimate([("p1_revenue_model", 0.5)])
    high, _, _ = irt.eap_estimate([("p1_revenue_model", 1.0)])
    assert low < mid < high


def test_more_consistent_answers_reduce_se():
    one = irt.eap_estimate([("p1_external_funding", 1.0)])[1]
    many = irt.eap_estimate([("p1_external_funding", 1.0)] * 4)[1]
    assert many < one


def test_unknown_and_none_responses_are_ignored():
    base = irt.eap_estimate([("p1_revenue_model", 1.0)])
    noisy = irt.eap_estimate([
        ("p1_revenue_model", 1.0),
        ("not_in_bank", 1.0),
        ("p1_revenue_model", None),
    ])
    assert base[0] == noisy[0]
    assert base[1] == noisy[1]


# ---------------------------------------------------------------------------
# Stage mapping
# ---------------------------------------------------------------------------

def test_theta_to_stage_boundaries():
    assert irt.theta_to_stage(-3.0) == 1
    assert irt.theta_to_stage(-1.0) == 2
    assert irt.theta_to_stage(0.0) == 3
    assert irt.theta_to_stage(1.0) == 4
    assert irt.theta_to_stage(2.0) == 5
    assert irt.theta_to_stage(3.0) == 6


def test_stage_boundary_is_left_closed():
    # boundary value belongs to the higher stage (θ < boundary ⇒ lower).
    b0 = irt._STAGE_BOUNDARIES[0]
    assert irt.theta_to_stage(b0 - 1e-6) == 1
    assert irt.theta_to_stage(b0) == 2


def test_stage_label_clamps():
    assert irt.stage_label(1) == irt.STAGE_NAMES[0]
    assert irt.stage_label(6) == irt.STAGE_NAMES[-1]
    # Out-of-range indices clamp rather than raise.
    assert irt.stage_label(0) == irt.STAGE_NAMES[0]
    assert irt.stage_label(99) == irt.STAGE_NAMES[-1]


def test_stage_posterior_sums_to_one_and_has_six_buckets():
    _, _, weights = irt.eap_estimate([("p1_revenue_model", 1.0)])
    buckets = irt.stage_posterior(weights)
    assert len(buckets) == 6
    assert abs(sum(buckets) - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Item selection
# ---------------------------------------------------------------------------

def test_max_information_excludes_answered():
    phase1 = [iid for iid, it in irt.ITEMS.items() if it["pool"] == "phase1"]
    first = irt.select_max_information(phase1, 0.0, answered=set())
    assert first in phase1
    second = irt.select_max_information(phase1, 0.0, answered={first})
    assert second != first


def test_max_information_targets_difficulty_near_theta():
    phase1 = [iid for iid, it in irt.ITEMS.items() if it["pool"] == "phase1"]
    chosen = irt.select_max_information(phase1, 1.2, answered=set())
    # The chosen item's difficulty should be among those closest to θ.
    b = irt.ITEMS[chosen]["b"]
    assert abs(b - 1.2) < 1.0


def test_closest_difficulty_picks_nearest_b():
    market = [iid for iid, it in irt.ITEMS.items() if it["pool"] == "market"]
    chosen = irt.select_closest_difficulty(market, -2.0, answered=set())
    nearest = min(market, key=lambda i: abs(irt.ITEMS[i]["b"] - (-2.0)))
    assert chosen == nearest


def test_selection_returns_none_when_exhausted():
    assert irt.select_max_information(["p1_revenue_model"], 0.0,
                                      answered={"p1_revenue_model"}) is None


# ---------------------------------------------------------------------------
# Session: phase logic
# ---------------------------------------------------------------------------

def _answer_strong(question):
    """Pick the strongest select option / dummy text for a question payload."""
    if question["type"] == "select":
        opt = max(question["options"], key=lambda o: o["credit"])
        return {"item_id": question["item_id"], "credit": opt["credit"],
                "value": opt["value"]}
    return {"item_id": question["item_id"], "credit": None, "value": "text"}


def _answer_with(question, picker):
    if question["type"] == "select":
        opt = picker(question["options"])
        return {"item_id": question["item_id"], "credit": opt["credit"],
                "value": opt["value"]}
    return {"item_id": question["item_id"], "credit": None, "value": "text"}


def _run_session(picker, max_turns=60):
    """Drive a full session with a fixed option-picking strategy.

    Returns (responses, final_payload, transcript)."""
    responses, transcript = [], []
    for _ in range(max_turns):
        out = session.next_question(responses, "fr")
        transcript.append(out)
        if out["done"]:
            return responses, out, transcript
        responses.append(_answer_with(out["question"], picker))
    raise AssertionError("session did not terminate")


def test_first_question_is_phase1():
    out = session.next_question([], "fr")
    assert not out["done"]
    assert out["progress"]["phase"] == 1
    assert out["question"]["axis"] is None
    assert irt.ITEMS[out["question"]["item_id"]]["pool"] == "phase1"


def test_phase1_respects_minimum_items():
    # Even a perfectly decisive founder answers at least MIN_PHASE1 stage items
    # before the engine is allowed to move to Phase 2.
    responses = []
    for _ in range(session.MIN_PHASE1 - 1):
        out = session.next_question(responses, "fr")
        assert out["progress"]["phase"] == 1, "left Phase 1 before the minimum"
        responses.append(_answer_strong(out["question"]))


def test_phase1_terminates_by_ceiling():
    # A founder pinned at the grid edge never reaches the SE floor, so the hard
    # ceiling must bound Phase 1.
    _, _, transcript = _run_session(lambda opts: max(opts, key=lambda o: o["credit"]))
    phase1_items = [t for t in transcript
                    if not t["done"] and t["progress"]["phase"] == 1]
    assert len(phase1_items) <= session.MAX_PHASE1


def test_mid_founder_converges_before_ceiling():
    # A clearly mid-stage founder (always the middle option) should trip the SE
    # threshold and leave Phase 1 before exhausting the ceiling — the whole point
    # of adaptivity.
    _, _, transcript = _run_session(lambda opts: opts[len(opts) // 2])
    phase1_count = sum(1 for t in transcript
                       if not t["done"] and t["progress"]["phase"] == 1)
    assert session.MIN_PHASE1 <= phase1_count < session.MAX_PHASE1


def test_phase_transition_flag_fires_once():
    _, _, transcript = _run_session(lambda opts: opts[len(opts) // 2])
    transitions = [t for t in transcript
                   if not t["done"] and t.get("phase_transition")]
    assert len(transitions) == 1
    # It fires on the first Phase-2 question.
    assert transitions[0]["question"]["axis"] is not None


def test_phase2_asks_each_axis_the_configured_count():
    responses, final, _ = _run_session(lambda opts: opts[len(opts) // 2])
    counts = {axis: 0 for axis in session.PHASE2_AXES}
    for r in responses:
        pool = irt.ITEMS[r["item_id"]]["pool"]
        if pool in counts:
            counts[pool] += 1
    for axis, n in counts.items():
        assert n == session.PHASE2_PER_AXIS, f"{axis} got {n} items"


def test_session_completes_with_profile_patch():
    _, final, _ = _run_session(lambda opts: opts[len(opts) // 2])
    assert final["done"] is True
    patch = final["profile_patch"]
    assert "cat" in patch
    cat = patch["cat"]
    assert cat["stage"] in range(1, 7)
    assert cat["stage_label"] in irt.STAGE_NAMES
    assert len(cat["stage_posterior"]) == 6
    assert patch["maturity_stage_cat"] == cat["stage_label"]


# ---------------------------------------------------------------------------
# Session: statelessness & rendering
# ---------------------------------------------------------------------------

def test_replay_is_deterministic():
    # The flow is stateless: replaying the same history yields the same question.
    out_a = session.next_question([], "fr")
    answer = _answer_strong(out_a["question"])
    first = session.next_question([answer], "fr")
    second = session.next_question([answer], "fr")
    assert first["question"]["item_id"] == second["question"]["item_id"]
    assert first["progress"]["theta_hat"] == second["progress"]["theta_hat"]


def test_language_switches_to_arabic():
    out = session.next_question([], "ar")
    q = out["question"]
    assert q["lang"] == "ar"
    expected = irt.ITEMS[q["item_id"]]["question_ar"]
    assert q["question"] == expected
    if q["type"] == "select":
        assert q["options"][0]["label"] == irt.ITEMS[q["item_id"]]["options"][0]["label_ar"]


def test_progress_posterior_tracks_six_stages():
    out = session.next_question([], "fr")
    prog = out["progress"]
    assert len(prog["stage_posterior"]) == 6
    assert len(prog["stage_names"]) == 6
    assert abs(sum(prog["stage_posterior"]) - 1.0) < 1e-3


def test_high_stage_founder_lands_in_upper_stages():
    _, final, _ = _run_session(lambda opts: max(opts, key=lambda o: o["credit"]))
    assert final["profile_patch"]["cat"]["stage"] >= 4


def test_low_stage_founder_lands_in_lower_stages():
    _, final, _ = _run_session(lambda opts: min(opts, key=lambda o: o["credit"]))
    assert final["profile_patch"]["cat"]["stage"] <= 2


# ---------------------------------------------------------------------------
# Cross-engine parity with the Rust signal endpoint (same math, same grid)
# ---------------------------------------------------------------------------

def test_matches_independent_eap_reference():
    # Recompute EAP by brute force over the same 81-point grid and compare.
    resp = [("p1_external_funding", 1.0), ("p1_mvp_exists", 0.0),
            ("p1_revenue_model", 0.5)]
    theta, se, _ = irt.eap_estimate(resp)

    grid = irt.THETA_GRID
    log_w = []
    for t in grid:
        lw = -0.5 * t * t - 0.5 * math.log(2 * math.pi)
        for iid, c in resp:
            a, b = irt.item_params(iid)
            p = 1.0 / (1.0 + math.exp(-a * (t - b)))
            p = min(1 - 1e-9, max(1e-9, p))
            lw += c * math.log(p) + (1 - c) * math.log(1 - p)
        log_w.append(lw)
    m = max(log_w)
    exps = [math.exp(w - m) for w in log_w]
    z = sum(exps)
    weights = [e / z for e in exps]
    ref_theta = sum(t * w for t, w in zip(grid, weights))
    ref_var = sum((t - ref_theta) ** 2 * w for t, w in zip(grid, weights))
    assert abs(theta - ref_theta) < 1e-9
    assert abs(se - math.sqrt(ref_var)) < 1e-9
