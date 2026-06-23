"""Abstract contract that every tool integration must satisfy."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TestResult:
    ok: bool
    message: str


@dataclass
class ProfilePatch:
    """Partial profile updates returned by pull tools before the scoring wave.

    Pull tools may boost evidence tiers (e.g. GitHub verifies product_stage → T3)
    or fill in blank numeric fields observed from the external service.
    Only unset fields should be written to avoid overriding user-supplied data.
    """
    evidence_tiers: dict[str, str] = field(default_factory=dict)  # field -> "T1"|"T2"|"T3"
    fields: dict[str, Any] = field(default_factory=dict)          # blank-only profile patches
    metadata: dict[str, Any] = field(default_factory=dict)        # tool-provided context (not scored)


class ToolIntegration(ABC):
    """Base class for every Moufida tool integration.

    Subclasses declare their identity via class attributes and override
    whichever lifecycle hooks are relevant for their direction:
    - push tools override on_diagnostic_complete / on_score_alert
    - pull tools override enrich_profile
    - bidirectional tools override all three
    """

    # ---- identity (must be overridden as class attributes) ----
    slug: str
    label: str
    domain: str
    direction: Literal["push", "pull", "bidirectional"]

    # JSON Schema for the config form (drives auto-generated UI fields).
    # Properties listed in "required" are mandatory before the tool can be saved.
    config_schema: dict

    # ---- lifecycle hooks ----

    @abstractmethod
    async def test_connection(self, config: dict) -> TestResult:
        """Validate credentials and reachability. Called before saving config."""

    async def on_diagnostic_complete(
        self,
        project_id: str,
        profile: dict,
        scores: dict[str, float],
        blockers: list[dict],
        roadmap: dict | None,
        config: dict,
    ) -> None:
        """Push tools: called after every successful diagnostic wave."""

    async def on_score_alert(
        self,
        project_id: str,
        alert: dict,
        config: dict,
    ) -> None:
        """Push tools: called when a daemon-triggered score alert fires."""

    async def enrich_profile(
        self,
        profile: dict,
        config: dict,
    ) -> ProfilePatch:
        """Pull tools: called before the scoring wave to inject live external data."""
        return ProfilePatch()
