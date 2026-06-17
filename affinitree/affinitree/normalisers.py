"""Pure, deterministic functions that map raw StartupProfile fields onto
normalised [0, 1] variables referenced by the formula strings in the JSON config.

Every function is total (handles ``None``) and side-effect free, which is what
makes the determinism guarantee (Tier 2a) hold.
"""

from __future__ import annotations

import math
from typing import Any, Callable


def _num(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def boolean(value: Any, **_: Any) -> float:
    """True -> 1.0, anything else -> 0.0."""
    return 1.0 if value else 0.0


def raw(value: Any, **_: Any) -> float:
    """Pass a numeric value through unchanged (used when a config formula does its
    own normalisation, e.g. the Listing 2 ``rubric_score / 4`` form)."""
    return _num(value, 0.0)


def normalise_range(value: Any, *, min: float, max: float, **_: Any) -> float:
    """Linearly map a numeric value within [min, max] onto [0, 1] (clamped)."""
    lo, hi = min, max
    v = _num(value, lo)
    if hi == lo:
        return 0.0
    return _clamp((v - lo) / (hi - lo))


def ordinal_map(value: Any, *, map: dict[str, float], default: float = 0.0, **_: Any) -> float:
    """Map an enum/ordinal value to a normalised score via an explicit table."""
    if value is None:
        return default
    return float(map.get(str(value), default))


def inverse_log_density(value: Any, **_: Any) -> float:
    """1 / (1 + ln(count + 1)) -- decays as a count grows. Used for competitive
    intensity (more competitors -> lower novelty/market score)."""
    count = max(0.0, _num(value, 0.0))
    return 1.0 / (1.0 + math.log(count + 1.0))


def saturating(value: Any, *, target: float, **_: Any) -> float:
    """value / target, clamped to [0, 1]. Reaches full credit at ``target``."""
    if target <= 0:
        return 0.0
    return _clamp(_num(value, 0.0) / target)


def ratio(numerator: Any, denominator: Any, *, target: float = 3.0, **_: Any) -> float:
    """Normalised ratio (e.g. LTV/CAC) credited fully at ``target``."""
    num = _num(numerator, 0.0)
    den = _num(denominator, 0.0)
    if den <= 0:
        return 0.0
    return _clamp((num / den) / target)


def rubric_normalised(value: Any, **_: Any) -> float:
    """A rubric integer (0-4) already resolved upstream, normalised to [0, 1]."""
    return _clamp(_num(value, 0.0) / 4.0)


def inverse_fraction(value: Any, **_: Any) -> float:
    """For a percentage field where lower is better (e.g. manual_steps_pct).
    100% manual -> 0.0, 0% manual -> 1.0."""
    pct = _clamp(_num(value, 100.0) / 100.0)
    return 1.0 - pct


def boolean_inverse(value: Any, **_: Any) -> float:
    """True is bad (e.g. single-point supply chain): True -> 0.0, False -> 1.0."""
    return 0.0 if value else 1.0


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


# Registry consulted by the scorer's `derive` step.
REGISTRY: dict[str, Callable[..., float]] = {
    "boolean": boolean,
    "raw": raw,
    "boolean_inverse": boolean_inverse,
    "normalise_range": normalise_range,
    "ordinal_map": ordinal_map,
    "inverse_log_density": inverse_log_density,
    "saturating": saturating,
    "ratio": ratio,
    "rubric_normalised": rubric_normalised,
    "inverse_fraction": inverse_fraction,
}
