"""Affinitree -- deterministic, explainable scoring engine for Moufida."""

from .anomaly import Anomaly, detect
from .blockers import derive_blockers
from .due_diligence import run_due_diligence
from .evidence import build_citations, format_evidence_block
from .justification import generate_justification
from .profile import StartupProfile
from .rubric import (
    RUBRICS,
    OllamaClient,
    score_profile_text_fields,
    score_profile_text_fields_detail,
)
from .scorer import (
    Affinitree,
    ComponentResult,
    ScoreResult,
    ScoringError,
    load_config,
    score,
)

__all__ = [
    "Affinitree",
    "Anomaly",
    "ComponentResult",
    "OllamaClient",
    "RUBRICS",
    "ScoreResult",
    "ScoringError",
    "StartupProfile",
    "build_citations",
    "derive_blockers",
    "detect",
    "format_evidence_block",
    "generate_justification",
    "load_config",
    "run_due_diligence",
    "score",
    "score_profile_text_fields",
    "score_profile_text_fields_detail",
]

__version__ = "0.2.0"
