"""Item Response Theory numerics for the adaptive intake (CAT).

Pure-Python, no numpy — the grid is 81 points and a session answers at most ~30
items, so the whole EAP update is well under a millisecond. Keeping it
dependency-free means the intake never breaks if an optional service (numpy, the
Rust ``signal`` offload) is unavailable: this module is the authoritative engine.

The model is the 2-parameter logistic (2PL) of Lord (1977):

    P_j(θ) = 1 / (1 + exp(−a_j (θ − b_j)))

with a **graded extension** (Samejima-style) so an item can express a partial
response credit ``c ∈ [0, 1]`` rather than only a binary 0/1. The likelihood of a
graded response is the soft-Bernoulli ``P^c · (1−P)^(1−c)``, which collapses
exactly to the binary 2PL when ``c ∈ {0, 1}`` and lets a 3- or 4-option question
contribute proportional information. Ability is estimated with the Bayesian
Expected A Posteriori (EAP) rule of Bock & Mislevy (1982) over a fixed grid.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Grid + prior. θ is the latent startup maturity on a standardised scale; the
# prior is N(0, 1) centred on Stage 3 of 6.
# ---------------------------------------------------------------------------
_GRID_MIN, _GRID_MAX, _GRID_N = -4.0, 4.0, 81
_GRID_STEP = (_GRID_MAX - _GRID_MIN) / (_GRID_N - 1)
THETA_GRID: list[float] = [_GRID_MIN + k * _GRID_STEP for k in range(_GRID_N)]
_LOG_2PI = math.log(2.0 * math.pi)
LOG_PRIOR: list[float] = [-0.5 * t * t - 0.5 * _LOG_2PI for t in THETA_GRID]

# Stage taxonomy + boundaries (loaded from the bank's meta block).
_BANK_PATH = Path(__file__).parent / "item_bank.json"
_BANK: dict = json.loads(_BANK_PATH.read_text(encoding="utf-8"))
ITEMS: dict[str, dict] = _BANK["items"]
STAGE_NAMES: list[str] = _BANK["meta"]["stages"]
_STAGE_BOUNDARIES: list[float] = _BANK["meta"]["stage_boundaries"]

_EPS = 1e-9


def _sigmoid(x: float) -> float:
    # Numerically stable logistic.
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def prob_correct(theta: float, a: float, b: float) -> float:
    """2PL item response function P_j(θ)."""
    return _sigmoid(a * (theta - b))


def item_params(item_id: str) -> tuple[float, float] | None:
    """(a, b) for an item, or None if unknown."""
    item = ITEMS.get(item_id)
    if item is None:
        return None
    return float(item["a"]), float(item["b"])


def log_likelihood_grid(responses: Iterable[tuple[str, float]]) -> list[float]:
    """Σ over answered items of the graded soft-Bernoulli log-likelihood,
    evaluated at every grid point.

    ``responses`` is an iterable of ``(item_id, credit)`` with ``credit ∈ [0, 1]``.
    Items absent from the bank, or carrying ``credit is None`` (e.g. free-text
    Phase-2 items that don't inform θ), are skipped.
    """
    log_l = [0.0] * _GRID_N
    for item_id, credit in responses:
        params = item_params(item_id)
        if params is None or credit is None:
            continue
        a, b = params
        c = max(0.0, min(1.0, float(credit)))
        for k, theta in enumerate(THETA_GRID):
            p = prob_correct(theta, a, b)
            p = min(1.0 - _EPS, max(_EPS, p))
            log_l[k] += c * math.log(p) + (1.0 - c) * math.log(1.0 - p)
    return log_l


def posterior(responses: Iterable[tuple[str, float]]) -> list[float]:
    """Normalised posterior weights over THETA_GRID (sums to 1)."""
    log_w = [ll + lp for ll, lp in zip(log_likelihood_grid(responses), LOG_PRIOR)]
    m = max(log_w)
    exps = [math.exp(w - m) for w in log_w]
    z = sum(exps)
    return [e / z for e in exps]


def eap_estimate(responses: Iterable[tuple[str, float]]) -> tuple[float, float, list[float]]:
    """Return ``(theta_hat, se, posterior_weights)`` for the response history.

    ``theta_hat`` is the posterior mean; ``se`` its posterior standard deviation
    (the CAT precision used by the stopping rule).
    """
    weights = posterior(responses)
    theta_hat = sum(t * w for t, w in zip(THETA_GRID, weights))
    variance = sum(((t - theta_hat) ** 2) * w for t, w in zip(THETA_GRID, weights))
    return theta_hat, math.sqrt(max(0.0, variance)), weights


def item_information(item_id: str, theta: float) -> float:
    """Fisher information I_j(θ) = a²·P·(1−P) — maximised at θ = b_j."""
    params = item_params(item_id)
    if params is None:
        return 0.0
    a, b = params
    p = prob_correct(theta, a, b)
    return a * a * p * (1.0 - p)


def select_max_information(
    candidates: Iterable[str], theta: float, answered: set[str]
) -> str | None:
    """Maximum-information item selection: argmax_j I_j(θ) over unanswered
    candidates. The principled core of CAT — no hand-authored branching."""
    best_id, best_info = None, -1.0
    for item_id in candidates:
        if item_id in answered:
            continue
        info = item_information(item_id, theta)
        if info > best_info:
            best_id, best_info = item_id, info
    return best_id


def select_closest_difficulty(
    candidates: Iterable[str], theta: float, answered: set[str]
) -> str | None:
    """Pick the unanswered item whose difficulty b is closest to θ.

    Used in Phase 2 to surface stage-appropriate axis questions: an item is most
    informative — and most relevant — when its difficulty matches the founder's
    estimated maturity. Equivalent to max-information for items of similar
    discrimination, but robust for the free-text items that have no credit."""
    best_id, best_dist = None, math.inf
    for item_id in candidates:
        if item_id in answered:
            continue
        params = item_params(item_id)
        if params is None:
            continue
        dist = abs(params[1] - theta)
        if dist < best_dist:
            best_id, best_dist = item_id, dist
    return best_id


def theta_to_stage(theta: float) -> int:
    """Map continuous θ to a 1–6 stage index using the bank's boundaries."""
    for stage, boundary in enumerate(_STAGE_BOUNDARIES, start=1):
        if theta < boundary:
            return stage
    return len(_STAGE_BOUNDARIES) + 1


def stage_label(stage: int) -> str:
    """Human stage name for a 1-based stage index."""
    idx = max(1, min(len(STAGE_NAMES), stage)) - 1
    return STAGE_NAMES[idx]


def stage_posterior(weights: list[float]) -> list[float]:
    """Collapse the 81-point θ posterior into 6 stage-bucket probabilities."""
    buckets = [0.0] * (len(_STAGE_BOUNDARIES) + 1)
    for theta, w in zip(THETA_GRID, weights):
        buckets[theta_to_stage(theta) - 1] += w
    return buckets
