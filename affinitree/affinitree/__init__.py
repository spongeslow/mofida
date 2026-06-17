"""Affinitree -- deterministic, explainable scoring engine for Moufida."""

from .anomaly import Anomaly, detect
from .profile import StartupProfile
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
    "ScoreResult",
    "ScoringError",
    "StartupProfile",
    "detect",
    "load_config",
    "score",
]

__version__ = "0.1.0"
