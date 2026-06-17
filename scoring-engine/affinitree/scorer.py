"""Weighted-sum scoring engine.

For a given profile and score name it:
  1. loads the JSON config,
  2. validates that the required input fields are present,
  3. for each sub-dimension, derives its normalised variables, evaluates the
     formula -> ``vi`` in [0, 1], reads the confidence multiplier ``mi`` from the
     governing evidence tier, and computes ``ci = wi * vi * mi``,
  4. aggregates the contributions and normalises onto the configured scale,
  5. returns a fully serialisable result with a per-component explanation tree.

No LLM is involved here. Free-text fields enter only as pre-computed rubric
integers carried on ``profile.rubric_scores`` (see rubric.py).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from . import formula, normalisers
from .profile import TIER_MULTIPLIER, StartupProfile

CONFIG_DIR = Path(__file__).parent / "config"

# Maps a public score name to its config file stem.
SCORE_CONFIGS = {
    "market": "market",
    "commercial_offer": "commercial_offer",
    "innovation": "innovation",
    "scalability": "scalability",
    "green": "green",
}


class ScoringError(ValueError):
    pass


@dataclass
class ComponentResult:
    name: str
    weight: float
    raw_value: float  # normalised vi in [0, 1]
    evidence_tier: str
    multiplier: float
    contribution: float  # ci = wi * vi * mi
    citation: str
    derived: dict[str, float] = field(default_factory=dict)
    formula: str = ""


@dataclass
class ScoreResult:
    score_name: str
    score: float  # normalised onto config scale (default 0-5)
    scale: tuple[float, float]
    components: list[ComponentResult]
    missing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["scale"] = list(self.scale)
        return d

    def explanation_tree(self) -> dict[str, Any]:
        """A nested, serialisable view used by the natural-language justifier
        and the dashboard's expandable sub-score table."""
        return {
            "score_name": self.score_name,
            "score": round(self.score, 4),
            "scale": list(self.scale),
            "components": [
                {
                    "name": c.name,
                    "contribution": round(c.contribution, 4),
                    "weight": c.weight,
                    "normalised_value": round(c.raw_value, 4),
                    "evidence_tier": c.evidence_tier,
                    "multiplier": c.multiplier,
                    "formula": c.formula,
                    "derived": {k: round(v, 4) for k, v in c.derived.items()},
                    "citation": c.citation,
                }
                for c in self.components
            ],
        }


@lru_cache(maxsize=None)
def load_config(score_name: str) -> dict[str, Any]:
    stem = SCORE_CONFIGS.get(score_name)
    if stem is None:
        raise ScoringError(f"unknown score: {score_name!r}")
    path = CONFIG_DIR / f"{stem}.json"
    if not path.exists():
        raise ScoringError(f"missing config file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_input(profile: StartupProfile, dotted: str) -> Any:
    """Resolve an input reference. ``rubric:`` prefix reads a cached rubric score."""
    if dotted.startswith("rubric:"):
        field_path = dotted.split(":", 1)[1]
        return profile.rubric_scores.get(field_path, 0)
    return profile.get(dotted)


def _derive(profile: StartupProfile, derive_spec: dict[str, Any]) -> dict[str, float]:
    """Compute the normalised variables a sub-dimension formula refers to."""
    out: dict[str, float] = {}
    for var_name, spec in derive_spec.items():
        fn_name = spec["fn"]
        fn = normalisers.REGISTRY.get(fn_name)
        if fn is None:
            raise ScoringError(f"unknown normaliser: {fn_name!r}")
        kwargs = {k: v for k, v in spec.items() if k not in ("fn", "field", "fields")}
        if "fields" in spec:  # multi-argument normaliser (e.g. ratio)
            args = [_resolve_input(profile, f) for f in spec["fields"]]
            out[var_name] = float(fn(*args, **kwargs))
        else:
            value = _resolve_input(profile, spec["field"])
            out[var_name] = float(fn(value, **kwargs))
    return out


def _governing_tier(profile: StartupProfile, sub: dict[str, Any]) -> str:
    """Tier whose multiplier governs this sub-dimension. Explicit ``evidence_field``
    wins; otherwise take the strongest tier among the structured inputs (verified
    evidence on any input lifts confidence). Rubric/text-only inputs stay T1."""
    if "evidence_field" in sub:
        return profile.tier(sub["evidence_field"])
    best = "T1"
    order = {"T1": 0, "T2": 1, "T3": 2}
    for ref in sub.get("inputs", []):
        if ref.startswith("rubric:"):
            continue
        t = profile.tier(ref)
        if order[t] > order[best]:
            best = t
    return best


def _missing_fields(profile: StartupProfile, config: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for ref in config.get("required_fields", []):
        try:
            value = _resolve_input(profile, ref)
        except AttributeError:
            missing.append(ref)
            continue
        if value is None:
            missing.append(ref)
    return missing


def score(
    profile: StartupProfile,
    score_name: str,
    *,
    strict: bool = False,
) -> ScoreResult:
    """Compute a composite score. With ``strict`` a missing required field raises;
    otherwise missing fields are reported on the result and scored as their
    neutral default."""
    config = load_config(score_name)
    missing = _missing_fields(profile, config)
    if missing and strict:
        raise ScoringError(f"{score_name}: missing required fields {missing}")

    aggregation = config.get("aggregation", "weighted_sum")
    lo, hi = config.get("normalise_to", [0, 5])

    components: list[ComponentResult] = []
    for sub in config["sub_dimensions"]:
        derived = _derive(profile, sub.get("derive", {}))
        vi = formula.evaluate(sub["formula"], derived)
        vi = max(0.0, min(1.0, vi))
        tier = _governing_tier(profile, sub)
        mi = TIER_MULTIPLIER[tier]
        wi = float(sub["weight"])
        ci = wi * vi * mi
        components.append(
            ComponentResult(
                name=sub["id"],
                weight=wi,
                raw_value=vi,
                evidence_tier=tier,
                multiplier=mi,
                contribution=ci,
                citation=sub.get("citation", ""),
                derived=derived,
                formula=sub["formula"],
            )
        )

    composite_unit = _aggregate(components, aggregation)
    # composite_unit is in [0, ~1.2]; clamp to [0,1] before mapping onto scale so
    # T2-complete evidence reaches the top of the scale and the T3 bonus saturates.
    normalised = max(0.0, min(1.0, composite_unit))
    final = lo + normalised * (hi - lo)

    return ScoreResult(
        score_name=score_name,
        score=final,
        scale=(lo, hi),
        components=components,
        missing_fields=missing,
    )


def _aggregate(components: list[ComponentResult], method: str) -> float:
    if not components:
        return 0.0
    if method == "weighted_sum":
        return sum(c.contribution for c in components)
    if method == "geometric_mean":
        # Weighted geometric mean of (vi*mi) factors.
        total_w = sum(c.weight for c in components) or 1.0
        product = 1.0
        for c in components:
            base = max(1e-9, c.raw_value * c.multiplier)
            product *= base ** (c.weight / total_w)
        return product
    raise ScoringError(f"unknown aggregation method: {method!r}")


def Affinitree(profile: StartupProfile, score_name: str, **kwargs: Any) -> ScoreResult:
    """Spec-named entry point used by the axis services."""
    return score(profile, score_name, **kwargs)
