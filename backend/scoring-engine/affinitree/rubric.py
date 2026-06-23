"""LLM-as-judge rubric scoring for the five free-text fields.

Each field has a 0-4 rubric with explicit level descriptors (stored here next to
the Affinitree config, per Section 3.3.3). Mistral 7B (via Ollama) is asked to
return ``{"score": int, "evidence_quote": str, "reasoning": str}``. To bound
variance the prompt is run twice; if the two scores differ by more than 1 a third
run is taken and the median is used.

The LLM call is injected (``LLMClient`` protocol) so the deterministic scorer and
its tests never depend on a live model.
"""

from __future__ import annotations

import json
import os
import statistics
from typing import Any, Optional, Protocol


# field key (dotted profile path) -> rubric definition
RUBRICS: dict[str, dict[str, Any]] = {
    "offer.value_prop_text": {
        "name": "Value proposition clarity",
        "levels": {
            0: "No value proposition stated, or completely generic (e.g. 'we improve efficiency').",
            1: "Problem identified but no solution differentiation.",
            2: "Problem and solution stated; customer segment vague.",
            3: "Clear problem, solution, and target segment; benefit quantified partially.",
            4: "Specific problem, measurable benefit, named segment, validated by at least one customer quote or data point.",
        },
    },
    "offer.differentiation_text": {
        "name": "Competitive differentiation",
        "levels": {
            0: "No differentiation stated or purely generic claims.",
            1: "Vague claim of being 'better' with no basis.",
            2: "States one differentiator but not defensible.",
            3: "Clear, credible differentiators relative to named competitors.",
            4: "Defensible, hard-to-copy differentiation backed by evidence (IP, data, exclusive partnerships).",
        },
    },
    "innovation.novelty_text": {
        "name": "Value-creation novelty",
        "levels": {
            0: "No novelty; an undifferentiated copy of existing solutions.",
            1: "Minor incremental improvement to an existing solution.",
            2: "Meaningful improvement addressing a known gap.",
            3: "Addresses an unmet need in a new way for the sector.",
            4: "Creates a genuinely new category or unlocks a previously unserved need.",
        },
    },
    "innovation.brand_distinctiveness_text": {
        "name": "Brand distinctiveness",
        "levels": {
            0: "No brand positioning, or indistinguishable from competitors.",
            1: "Generic positioning with weak identity.",
            2: "Some distinct positioning but inconsistently expressed.",
            3: "Clear, consistent positioning that stands apart from competitors.",
            4: "Highly distinctive, memorable positioning with a defensible identity.",
        },
    },
    "legal.sdg_alignment_text": {
        "name": "UN SDG alignment",
        "levels": {
            0: "No alignment with any Sustainable Development Goal.",
            1: "Vague claim of social/environmental benefit, no specific SDG.",
            2: "Tangential alignment with one SDG.",
            3: "Clear alignment with one or more specific SDGs with concrete actions.",
            4: "Core mission directly advances named SDGs with measurable impact targets.",
        },
    },
}

DEFAULT_MODEL = os.getenv("MOUFIDA_MODEL")
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL")


class LLMClient(Protocol):
    def generate_json(self, prompt: str, *, seed: int) -> dict[str, Any]:
        """Return a parsed JSON object with keys score / evidence_quote / reasoning."""
        ...


def build_prompt(field_key: str, text: str) -> str:
    rubric = RUBRICS[field_key]
    levels = "\n".join(f"  {k}: {v}" for k, v in rubric["levels"].items())
    return (
        f"You are a strict startup evaluator scoring the '{rubric['name']}' of a "
        f"venture on an integer scale from 0 to 4.\n\n"
        f"Rubric:\n{levels}\n\n"
        f"Text to evaluate (between triple backticks):\n```\n{text.strip()}\n```\n\n"
        "Respond with ONLY a JSON object of the form "
        '{"score": <int 0-4>, "evidence_quote": "<short quote from the text or empty>", '
        '"reasoning": "<one sentence>"}.'
    )


def score_field(
    text: str,
    field_key: str,
    client: LLMClient,
    *,
    runs: int = 2,
) -> dict[str, Any]:
    """Score one free-text field. Returns {score:int, evidence_quote, reasoning,
    runs:[...]} with the median-on-divergence policy applied."""
    if field_key not in RUBRICS:
        raise KeyError(f"no rubric for field {field_key!r}")
    if not text or not text.strip():
        return {"score": 0, "evidence_quote": "", "reasoning": "Empty field.", "runs": []}

    prompt = build_prompt(field_key, text)
    results = [_clamp_result(client.generate_json(prompt, seed=s)) for s in range(runs)]
    scores = [r["score"] for r in results]

    if len(scores) >= 2 and abs(scores[0] - scores[1]) > 1:
        third = _clamp_result(client.generate_json(prompt, seed=runs))
        results.append(third)
        scores.append(third["score"])

    median_score = int(round(statistics.median(scores)))
    # Pick the representative run closest to the median for the quote/reasoning.
    representative = min(results, key=lambda r: abs(r["score"] - median_score))
    return {
        "score": median_score,
        "evidence_quote": representative.get("evidence_quote", ""),
        "reasoning": representative.get("reasoning", ""),
        "runs": scores,
    }


def score_profile_text_fields(profile, client: LLMClient) -> dict[str, int]:
    """Score every populated rubric field on a profile and write the integer
    results back into ``profile.rubric_scores`` for the deterministic scorer."""
    out: dict[str, int] = {}
    for field_key in RUBRICS:
        text = profile.get(field_key)
        if isinstance(text, str) and text.strip():
            result = score_field(text, field_key, client)
            out[field_key] = result["score"]
            profile.rubric_scores[field_key] = result["score"]
    return out


def score_profile_text_fields_detail(profile, client: LLMClient) -> dict[str, dict]:
    """Score every populated rubric field and return full detail per field.

    Populates ``profile.rubric_scores`` as a side effect (same as
    ``score_profile_text_fields``). The returned dict maps field_key to
    ``{score, evidence_quote, reasoning, runs}`` for dashboard display.
    """
    out: dict[str, dict] = {}
    for field_key in RUBRICS:
        text = profile.get(field_key)
        if isinstance(text, str) and text.strip():
            result = score_field(text, field_key, client)
            out[field_key] = result
            profile.rubric_scores[field_key] = result["score"]
    return out


def _clamp_result(raw: dict[str, Any]) -> dict[str, Any]:
    try:
        score = int(round(float(raw.get("score", 0))))
    except (TypeError, ValueError):
        score = 0
    return {
        "score": max(0, min(4, score)),
        "evidence_quote": str(raw.get("evidence_quote", "")),
        "reasoning": str(raw.get("reasoning", "")),
    }


class OllamaClient:
    """LLMClient backed by a local Ollama server (used in production)."""

    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_OLLAMA_URL):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate_json(self, prompt: str, *, seed: int) -> dict[str, Any]:
        import httpx  # imported lazily so the core library has no hard dependency

        resp = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": {"seed": seed, "temperature": 0.2},
            },
            timeout=120,
        )
        resp.raise_for_status()
        body = resp.json()
        try:
            return json.loads(body["response"])
        except (KeyError, json.JSONDecodeError):
            return {"score": 0, "evidence_quote": "", "reasoning": "Unparseable model output."}

    def generate_text(self, prompt: str, *, seed: int = 42, timeout: float = 60.0) -> str:
        """Generate a plain-text (non-JSON) response."""
        import httpx

        resp = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"seed": seed, "temperature": 0.3},
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
