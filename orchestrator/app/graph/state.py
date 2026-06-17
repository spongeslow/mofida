"""Shared LangGraph state for the Moufida orchestrator.

``MoufidaState`` is the single dict threaded through every node of the
conversation graph: adaptive intake, the diagnostic wave runner, the scoring
aggregation and the roadmap builder. It is intentionally a plain ``TypedDict``
of JSON-friendly values -- the strongly typed ``StartupProfile`` model lives in
the scoring-engine and is carried here as a plain ``dict`` so the graph stays
serialisable for checkpointing and SSE replay.
"""
from __future__ import annotations

from typing import Literal, Optional, TypedDict


class MoufidaState(TypedDict, total=False):
    project_id: str
    mode: Literal["STATE_NEW", "STATE_EXISTING"]

    # The StartupProfile as a plain dict; the typed model lives in scoring-engine.
    profile: dict

    # Conversation log: [{role, content, lang}].
    conversation_history: list[dict]
    active_lang: Literal["fr", "ar-TN", "other"]

    # Raw questionnaire answers before they are merged into ``profile``.
    intake_answers: dict

    # Diagnostic wave index: 0, 1 or 2 (see axis_registry.diagnostic_order).
    current_wave: int
    # service slug -> diagnose response.
    axis_outputs: dict

    maturity_stage: Optional[str]
    self_assessed_stage: Optional[str]
    perception_gap: Optional[bool]

    # [{domain, description, severity}]
    blockers: list[dict]
    anomalies: list[dict]

    # {"market": float, "commercial_offer": float, ...}
    scores: dict
    # Full explanation trees from affinitree, keyed by score name.
    score_breakdowns: dict

    roadmap: Optional[dict]

    # Pending SSE events awaiting emission to the client.
    sse_queue: list[dict]
