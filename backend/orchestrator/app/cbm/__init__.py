"""Concept Bottleneck Model layer (Phase H, paper 1).

See ``docs/research/concept-bottleneck-diagnostic-layer.md``.

Pipeline:  profile → LLM concept scoring (scorer.py) → linear bottleneck head
(the Rust ``moufida-signal`` service) → decomposed axis score + bottleneck.
"""
from .scorer import (  # noqa: F401
    CONCEPTS,
    concept_labels,
    profile_to_text,
    run_cbm_for_axes,
    score_concepts,
)
