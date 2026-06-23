"""ToolManager — orchestrates all tool integrations.

The manager is the single point of contact for the orchestrator:
  - list_states()           → current enabled/config for every registered tool
  - save()                  → persist a user config change to DB
  - test()                  → proxy to tool.test_connection()
  - enrich_profile()        → merge pull-tool ProfilePatches before scoring
  - dispatch_diagnostic()   → fan push-tool notifications after scoring
  - dispatch_alert()        → fan push-tool alert notifications from Redis consumer
"""
from __future__ import annotations

import json
import logging
from typing import Any

from .base import ProfilePatch
from .config import ToolState

# Trigger lazy registration of all tools at import time.
# Each tool module calls @register inside toolkit.tools.*
from .tools import _load_all_tools

_load_all_tools()

from . import registry as _registry  # noqa: E402 (after tools loaded)

logger = logging.getLogger("moufida.tools.manager")


class ToolManager:
    """Stateless façade — all state lives in PostgreSQL."""

    # ------------------------------------------------------------------ #
    # Queries                                                              #
    # ------------------------------------------------------------------ #

    async def list_states(self, pool) -> list[ToolState]:
        """Return the ToolState for every registered tool (DB row or defaults)."""
        rows = await pool.fetch("SELECT slug, enabled, config, last_sync_at, last_error FROM tool_integrations")
        db: dict[str, Any] = {r["slug"]: r for r in rows}
        states: list[ToolState] = []
        for cls in _registry.get_all():
            row = db.get(cls.slug)
            cfg = row["config"] if row else {}
            if isinstance(cfg, str):
                cfg = json.loads(cfg or "{}")
            states.append(
                ToolState(
                    slug=cls.slug,
                    label=cls.label,
                    domain=cls.domain,
                    direction=cls.direction,
                    enabled=row["enabled"] if row else False,
                    config=cfg,
                    config_schema=cls.config_schema,
                    last_sync_at=row["last_sync_at"] if row else None,
                    last_error=row["last_error"] if row else None,
                )
            )
        return states

    async def get_state(self, pool, slug: str) -> ToolState | None:
        cls = _registry.get(slug)
        if cls is None:
            return None
        row = await pool.fetchrow(
            "SELECT enabled, config, last_sync_at, last_error FROM tool_integrations WHERE slug = $1",
            slug,
        )
        cfg = row["config"] if row else {}
        if isinstance(cfg, str):
            cfg = json.loads(cfg or "{}")
        return ToolState(
            slug=cls.slug,
            label=cls.label,
            domain=cls.domain,
            direction=cls.direction,
            enabled=row["enabled"] if row else False,
            config=cfg,
            config_schema=cls.config_schema,
            last_sync_at=row["last_sync_at"] if row else None,
            last_error=row["last_error"] if row else None,
        )

    # ------------------------------------------------------------------ #
    # Mutations                                                            #
    # ------------------------------------------------------------------ #

    async def save(self, pool, slug: str, enabled: bool, config: dict) -> None:
        """Upsert tool config. Clears last_error on save."""
        await pool.execute(
            """
            INSERT INTO tool_integrations (slug, enabled, config)
            VALUES ($1, $2, $3::jsonb)
            ON CONFLICT (slug) DO UPDATE
               SET enabled = EXCLUDED.enabled,
                   config  = EXCLUDED.config,
                   last_error = NULL,
                   updated_at = now()
            """,
            slug,
            enabled,
            json.dumps(config),
        )

    async def record_sync(self, pool, slug: str, error: str | None = None) -> None:
        await pool.execute(
            """
            UPDATE tool_integrations
               SET last_sync_at = now(), last_error = $2
             WHERE slug = $1
            """,
            slug,
            error,
        )

    # ------------------------------------------------------------------ #
    # Test connection                                                      #
    # ------------------------------------------------------------------ #

    async def test(self, slug: str, config: dict):
        """Proxy to the tool's test_connection(); does not touch the DB."""
        cls = _registry.get(slug)
        if cls is None:
            return {"ok": False, "message": f"Unknown tool: {slug}"}
        result = await cls().test_connection(config)
        return {"ok": result.ok, "message": result.message}

    # ------------------------------------------------------------------ #
    # Profile enrichment (pull tools, runs before scoring wave)           #
    # ------------------------------------------------------------------ #

    async def enrich_profile(self, pool, profile: dict) -> dict:
        """Merge profile patches from all enabled pull tools and return the enriched profile."""
        rows = await pool.fetch(
            "SELECT slug, config FROM tool_integrations WHERE enabled = TRUE"
        )
        enriched = dict(profile)
        for row in rows:
            cls = _registry.get(row["slug"])
            if cls is None or cls.direction == "push":
                continue
            cfg = row["config"]
            if isinstance(cfg, str):
                cfg = json.loads(cfg or "{}")
            try:
                patch: ProfilePatch = await cls().enrich_profile(enriched, cfg)
                # Merge evidence tier upgrades (never downgrade existing tiers)
                tier_order = {"T1": 1, "T2": 2, "T3": 3}
                existing_tiers: dict = enriched.get("evidence_tiers") or {}
                for field_name, new_tier in patch.evidence_tiers.items():
                    current = existing_tiers.get(field_name, "T1")
                    if tier_order.get(new_tier, 0) > tier_order.get(current, 0):
                        existing_tiers[field_name] = new_tier
                if existing_tiers:
                    enriched["evidence_tiers"] = existing_tiers
                # Merge blank-only field patches
                for key, value in patch.fields.items():
                    if not enriched.get(key):
                        enriched[key] = value
                # Carry tool metadata through profile for downstream logging
                if patch.metadata:
                    tool_meta = enriched.get("_tool_metadata", {})
                    tool_meta[row["slug"]] = patch.metadata
                    enriched["_tool_metadata"] = tool_meta
            except Exception as exc:
                logger.warning("enrich_profile failed for tool=%s: %s", row["slug"], exc)
                await self.record_sync(pool, row["slug"], error=str(exc))
        return enriched

    # ------------------------------------------------------------------ #
    # Push dispatchers                                                     #
    # ------------------------------------------------------------------ #

    async def dispatch_diagnostic(
        self,
        pool,
        project_id: str,
        profile: dict,
        scores: dict[str, float],
        blockers: list[dict],
        roadmap: dict | None,
    ) -> None:
        """Fan out diagnostic-complete notification to all enabled push tools."""
        rows = await pool.fetch(
            "SELECT slug, config FROM tool_integrations WHERE enabled = TRUE"
        )
        for row in rows:
            cls = _registry.get(row["slug"])
            if cls is None or cls.direction == "pull":
                continue
            cfg = row["config"]
            if isinstance(cfg, str):
                cfg = json.loads(cfg or "{}")
            try:
                await cls().on_diagnostic_complete(project_id, profile, scores, blockers, roadmap, cfg)
                await self.record_sync(pool, row["slug"])
            except Exception as exc:
                logger.warning("dispatch_diagnostic failed for tool=%s: %s", row["slug"], exc)
                await self.record_sync(pool, row["slug"], error=str(exc))

    async def dispatch_alert(
        self,
        pool,
        project_id: str,
        alert: dict,
    ) -> None:
        """Fan out a score alert to all enabled push tools."""
        rows = await pool.fetch(
            "SELECT slug, config FROM tool_integrations WHERE enabled = TRUE"
        )
        for row in rows:
            cls = _registry.get(row["slug"])
            if cls is None or cls.direction == "pull":
                continue
            cfg = row["config"]
            if isinstance(cfg, str):
                cfg = json.loads(cfg or "{}")
            try:
                await cls().on_score_alert(project_id, alert, cfg)
            except Exception as exc:
                logger.warning("dispatch_alert failed for tool=%s: %s", row["slug"], exc)
