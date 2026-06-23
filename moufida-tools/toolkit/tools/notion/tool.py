"""Notion integration — export StartupProfile as a Notion database page.

The tool creates one page per project in a user-specified Notion database.
Subsequent diagnostic runs update the existing page (tracked by project_id
stored as a rich_text property on the page).
"""
from __future__ import annotations

import logging
from datetime import datetime

from ...base import ProfilePatch, TestResult, ToolIntegration
from ...registry import register

logger = logging.getLogger("moufida.tools.notion")


@register
class NotionTool(ToolIntegration):
    slug = "notion"
    label = "Notion"
    domain = "documentation"
    direction = "push"

    config_schema = {
        "type": "object",
        "properties": {
            "integration_token": {
                "type": "string",
                "title": "Integration Token",
                "description": "Internal integration token from notion.so/my-integrations (starts with secret_)",
                "format": "password",
            },
            "database_id": {
                "type": "string",
                "title": "Database ID",
                "description": "ID of the Notion database to write to (copy from the database URL)",
            },
        },
        "required": ["integration_token", "database_id"],
    }

    async def test_connection(self, config: dict) -> TestResult:
        token = config.get("integration_token", "").strip()
        db_id = config.get("database_id", "").strip()
        if not token:
            return TestResult(ok=False, message="Integration token is required")
        if not db_id:
            return TestResult(ok=False, message="Database ID is required")
        try:
            from notion_client import AsyncClient
        except ImportError:
            return TestResult(ok=False, message="notion-client not installed (pip install notion-client)")
        try:
            client = AsyncClient(auth=token)
            db = await client.databases.retrieve(database_id=db_id)
            title = db.get("title", [{}])[0].get("plain_text", db_id)
            return TestResult(ok=True, message=f"Connected — database: «{title}»")
        except Exception as exc:
            return TestResult(ok=False, message=str(exc))

    async def on_diagnostic_complete(self, project_id, profile, scores, blockers, roadmap, config):
        token = config.get("integration_token", "").strip()
        db_id = config.get("database_id", "").strip()
        if not token or not db_id:
            return
        try:
            from notion_client import AsyncClient
        except ImportError:
            logger.warning("notion-client not installed — skipping Notion sync")
            return

        client = AsyncClient(auth=token)
        try:
            existing_page_id = await _find_existing_page(client, db_id, project_id)
            properties = _build_properties(project_id, profile, scores, blockers)
            children = _build_page_body(profile, scores, blockers, roadmap)

            if existing_page_id:
                await client.pages.update(page_id=existing_page_id, properties=properties)
                # Replace body blocks
                existing_blocks = await client.blocks.children.list(block_id=existing_page_id)
                for block in existing_blocks.get("results", []):
                    await client.blocks.delete(block_id=block["id"])
                await client.blocks.children.append(block_id=existing_page_id, children=children)
            else:
                await client.pages.create(
                    parent={"database_id": db_id},
                    properties=properties,
                    children=children,
                )
        except Exception as exc:
            logger.error("Notion sync failed for project=%s: %s", project_id, exc)
            raise


async def _find_existing_page(client, db_id: str, project_id: str) -> str | None:
    """Search for an existing page with matching project_id in the Moufida_ID field."""
    try:
        resp = await client.databases.query(
            database_id=db_id,
            filter={
                "property": "Moufida_ID",
                "rich_text": {"equals": project_id},
            },
        )
        results = resp.get("results", [])
        return results[0]["id"] if results else None
    except Exception:
        return None


def _build_properties(project_id: str, profile: dict, scores: dict, blockers: list) -> dict:
    sector = profile.get("sector", "cross-sector")
    stage = profile.get("self_assessed_stage", "Idéation")
    critical_count = sum(1 for b in blockers if b.get("severity") == "critical")

    avg_score = sum(scores.values()) / len(scores) if scores else 0

    return {
        "Name": {"title": [{"text": {"content": f"Moufida — {stage} ({sector})"}}]},
        "Moufida_ID": {"rich_text": [{"text": {"content": project_id}}]},
        "Sector": {"select": {"name": sector}},
        "Stage": {"select": {"name": stage}},
        "Average Score": {"number": round(avg_score, 2)},
        "Critical Blockers": {"number": critical_count},
        "Last Updated": {"date": {"start": datetime.utcnow().isoformat() + "Z"}},
    }


def _build_page_body(profile: dict, scores: dict, blockers: list, roadmap: dict | None) -> list:
    blocks: list[dict] = []

    # Scores section
    blocks.append(_heading2("Scores diagnostics"))
    score_labels = {
        "market": "Marché",
        "commercial_offer": "Offre Commerciale",
        "innovation": "Innovation",
        "scalability": "Scalabilité",
        "green": "Green",
    }
    for name, score in scores.items():
        label = score_labels.get(name, name)
        bar = "🟢" if score >= 3.5 else ("🟡" if score >= 2.0 else "🔴")
        blocks.append(_bullet(f"{bar} {label}: {score:.1f}/5"))

    # Blockers section
    critical = [b for b in blockers if b.get("severity") == "critical"]
    if critical:
        blocks.append(_heading2("Bloquants critiques"))
        for b in critical:
            blocks.append(_bullet(b.get("description", "")))

    # Roadmap section
    if roadmap:
        blocks.append(_heading2("Feuille de route"))
        for horizon, label in [
            ("immediate", "Immédiat (0–2 sem.)"),
            ("short_term", "Court terme (1–3 mois)"),
            ("medium_term", "Moyen terme (3–12 mois)"),
        ]:
            actions = roadmap.get(horizon) or []
            if actions:
                blocks.append(_heading3(label))
                for action in actions[:5]:
                    blocks.append(_bullet(action.get("action", "")))

    return blocks


def _heading2(text: str) -> dict:
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": text}}]}}


def _heading3(text: str) -> dict:
    return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": text}}]}}


def _bullet(text: str) -> dict:
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": text}}]}}
