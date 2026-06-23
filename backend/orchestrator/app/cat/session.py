"""Stateless adaptive-intake (CAT) session logic.

Mirrors the existing intake philosophy: there is **no** server-side session. The
client replays the full ``responses`` history on every turn and the server
recomputes the ability estimate (EAP) and selects the next item. This keeps the
orchestrator horizontally scalable and the flow resumable for free.

Two phases (see ``docs/research/computerized-adaptive-testing.md`` §4):

* **Phase 1 — Stage CAT.** Maximum-information item selection over the
  stage-discriminator pool until the posterior SE drops below ``SE_THRESHOLD``
  (or a hard ceiling). Produces θ̂ → maturity stage.
* **Phase 2 — Targeted axis assessment.** For each diagnostic axis, surface the
  questions whose difficulty is closest to θ̂ — stage-appropriate evidence the
  axis micro-services then score.
"""
from __future__ import annotations

from typing import Any, Optional

from . import irt

# Phase-1 stopping rule. Graded (multi-option) items carry less information than
# strict binary ones, so the SE floor is reached in ~6–10 items for a decisive
# founder and the ceiling guards the ambiguous, near-boundary cases.
SE_THRESHOLD = 0.40      # stop once the estimate is this precise …
MIN_PHASE1 = 5           # … but ask at least this many stage items first,
MAX_PHASE1 = 10          # and never more than this.

# Phase-2 plan. Order mirrors axis_registry.NETWORK_AXES diagnostic order. One
# stage-appropriate question per axis keeps the total intake ~15–18 items while
# giving every diagnostic axis a fresh, difficulty-matched piece of evidence.
PHASE2_AXES = [
    "ideation", "market", "product", "brand", "business_model",
    "legal", "operations", "marketing", "sales", "scalability",
]
PHASE2_PER_AXIS = 1

_PHASE1_POOL = "phase1"


# ---------------------------------------------------------------------------
# Response normalisation
# ---------------------------------------------------------------------------

def _normalise(responses: list[dict] | None) -> list[dict]:
    """Keep only responses to known items, in submission order."""
    out: list[dict] = []
    for r in responses or []:
        item_id = r.get("item_id")
        if item_id in irt.ITEMS:
            out.append(r)
    return out


def _pool_of(item_id: str) -> str:
    return irt.ITEMS[item_id]["pool"]


def _phase1_pairs(responses: list[dict]) -> list[tuple[str, float]]:
    """(item_id, credit) for answered Phase-1 items — the only ones that move θ."""
    pairs: list[tuple[str, float]] = []
    for r in responses:
        item_id = r["item_id"]
        if _pool_of(item_id) == _PHASE1_POOL and r.get("credit") is not None:
            pairs.append((item_id, float(r["credit"])))
    return pairs


# ---------------------------------------------------------------------------
# Core: replay history → derived state
# ---------------------------------------------------------------------------

def evaluate(responses: list[dict] | None) -> dict[str, Any]:
    """Replay the response history into the current CAT state (no next item)."""
    responses = _normalise(responses)
    phase1 = _phase1_pairs(responses)
    theta_hat, se, weights = irt.eap_estimate(phase1)
    stage = irt.theta_to_stage(theta_hat)

    answered = {r["item_id"] for r in responses}
    phase1_count = sum(1 for iid in answered if _pool_of(iid) == _PHASE1_POOL)
    phase1_done = phase1_count >= MAX_PHASE1 or (
        phase1_count >= MIN_PHASE1 and se < SE_THRESHOLD
    )

    return {
        "responses": responses,
        "answered": answered,
        "theta_hat": round(theta_hat, 3),
        "se": round(se, 3),
        "stage": stage,
        "stage_label": irt.stage_label(stage),
        "posterior": weights,
        "stage_posterior": irt.stage_posterior(weights),
        "phase1_count": phase1_count,
        "phase1_done": phase1_done,
        "phase": 2 if phase1_done else 1,
    }


def _next_item_id(state: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """Return ``(item_id, axis)`` for the next question, or ``(None, None)`` when
    the intake is complete. ``axis`` is set only in Phase 2."""
    answered: set[str] = state["answered"]
    theta = state["theta_hat"]

    if not state["phase1_done"]:
        pool = [iid for iid, it in irt.ITEMS.items() if it["pool"] == _PHASE1_POOL]
        return irt.select_max_information(pool, theta, answered), None

    # Phase 2: serve the axis with the fewest answered items, then the item
    # whose difficulty best matches the estimated stage.
    for axis in PHASE2_AXES:
        count = sum(1 for iid in answered if _pool_of(iid) == axis)
        if count >= PHASE2_PER_AXIS:
            continue
        pool = [iid for iid, it in irt.ITEMS.items() if it["pool"] == axis]
        chosen = irt.select_closest_difficulty(pool, theta, answered)
        if chosen:
            return chosen, axis
    return None, None


# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------

def _translate(item_id: str, language: str, axis: Optional[str]) -> dict:
    """Render an item for the client in the requested language (fr default; ar
    when ``language`` starts with 'ar')."""
    item = irt.ITEMS[item_id]
    is_ar = language.lower().startswith("ar")
    suffix = "ar" if is_ar else "fr"
    options = None
    if item["type"] == "select":
        options = [
            {
                "label": opt[f"label_{suffix}"],
                "credit": opt["credit"],
                "value": opt["value"],
            }
            for opt in item["options"]
        ]
    return {
        "item_id": item_id,
        "field": item["field"],
        "type": item["type"],
        "axis": axis,
        "question": item[f"question_{suffix}"],
        "options": options,
        "lang": "ar" if is_ar else "fr",
    }


def next_question(responses: list[dict] | None, language: str = "fr") -> dict:
    """The public stateless turn: given the answers so far, return the next
    question (with live stage posterior) or the completion payload."""
    state = evaluate(responses)
    item_id, axis = _next_item_id(state)

    progress = {
        "phase": state["phase"],
        "theta_hat": state["theta_hat"],
        "se": state["se"],
        "stage": state["stage"],
        "stage_label": state["stage_label"],
        "stage_posterior": [round(p, 4) for p in state["stage_posterior"]],
        "stage_names": irt.STAGE_NAMES,
        "items_answered": len(state["answered"]),
    }

    if item_id is None:
        return {
            "done": True,
            "progress": progress,
            "profile_patch": build_profile_patch(state),
        }

    # The phase-1→2 reveal fires exactly once: when the first Phase-2 question is
    # served (we are in Phase 2 but no axis item has been answered yet).
    phase2_answered = any(_pool_of(iid) in PHASE2_AXES for iid in state["answered"])
    phase_transition = axis is not None and not phase2_answered

    return {
        "done": False,
        "question": _translate(item_id, language, axis),
        "progress": progress,
        "phase_transition": phase_transition,
    }


# ---------------------------------------------------------------------------
# Completion → StartupProfile patch
# ---------------------------------------------------------------------------

def _coerce(qtype: str, raw: Any) -> Any:
    if qtype == "number":
        try:
            num = float(raw)
            return int(num) if num.is_integer() else num
        except (TypeError, ValueError):
            return raw
    if qtype == "boolean":
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in {"true", "1", "yes", "oui", "نعم"}
    return raw


def _set_dotted(target: dict, dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def build_profile_patch(state: dict[str, Any]) -> dict:
    """Fold the gathered answers into a nested StartupProfile patch, plus a
    ``cat`` block capturing the latent-stage estimate for the diagnostic and the
    perception-gap analysis."""
    patch: dict = {}
    for r in state["responses"]:
        item = irt.ITEMS[r["item_id"]]
        # `value` (the option's mapped value, or the raw text) lands in the profile.
        raw = r.get("value")
        if raw is None:
            raw = r.get("credit")
        if raw is None:
            continue
        _set_dotted(patch, item["field"], _coerce(item["type"], raw))

    stage = state["stage"]
    patch["maturity_stage_cat"] = irt.stage_label(stage)
    patch["cat"] = {
        "theta": state["theta_hat"],
        "se": state["se"],
        "stage": stage,
        "stage_label": irt.stage_label(stage),
        "stage_posterior": [round(p, 4) for p in state["stage_posterior"]],
        "items_answered": len(state["answered"]),
    }
    return patch
