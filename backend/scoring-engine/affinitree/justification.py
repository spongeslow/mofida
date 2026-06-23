"""Natural-language score justification.

After Affinitree returns a ScoreResult, this module calls the LLM to generate
a 2–3 sentence plain-language explanation of what drove the score, written in
the startup's language. Designed to degrade gracefully: if the LLM is
unavailable, returns None so the service response is still valid.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .scorer import ScoreResult

if TYPE_CHECKING:
    from .rubric import OllamaClient

logger = logging.getLogger("affinitree.justification")

_LANG_NAMES: dict[str, str] = {
    "fr": "French",
    "en": "English",
    "ar": "French",      # Derja/Arabic → respond in French (documented limitation)
    "ar-TN": "French",
}

_SCORE_LABELS: dict[str, str] = {
    "market": "Market Score",
    "commercial_offer": "Commercial Offer Score",
    "innovation": "Innovation Score",
    "scalability": "Scalability Score",
    "green": "Green Score",
    "marketing_readiness": "Marketing Readiness",
    "sales_readiness": "Sales Readiness",
}


def generate_justification(
    result: ScoreResult,
    client: "OllamaClient",
    language: str = "fr",
) -> str | None:
    """Generate a 2–3 sentence NL justification for a ScoreResult.

    Returns None (and logs a warning) if the LLM call fails or times out.
    """
    try:
        sorted_by_contribution = sorted(
            result.components, key=lambda c: c.contribution, reverse=True
        )
        top = sorted_by_contribution[:2]
        gaps = sorted(
            [c for c in result.components if c.raw_value < 0.5],
            key=lambda c: c.raw_value,
        )[:1]

        lang_name = _LANG_NAMES.get(language, "French")
        score_label = _SCORE_LABELS.get(result.score_name, result.score_name.replace("_", " ").title())

        strengths = ", ".join(
            f"{c.name.replace('_', ' ')} (contribution {c.contribution:.2f})" for c in top
        )
        gap_text = (
            ", ".join(
                f"{c.name.replace('_', ' ')} (value {c.raw_value:.2f}/1.0)" for c in gaps
            )
            if gaps else "none identified"
        )

        prompt = (
            f"You are an entrepreneurship advisor writing in {lang_name}. "
            f"Write exactly 2-3 sentences explaining a startup's {score_label} "
            f"of {result.score:.2f} out of 5. "
            f"Be specific and actionable. Do not give generic advice. "
            f"Do not start with 'Based on' or restate the score number.\n\n"
            f"Key strengths driving the score: {strengths}.\n"
            f"Main gap dragging the score down: {gap_text}.\n\n"
            f"Write only the explanation — no preamble, no JSON."
        )

        return client.generate_text(prompt, seed=42, timeout=45.0)

    except Exception as exc:
        logger.warning("justification failed for '%s': %s", result.score_name, exc)
        return None
