"""Composio-backed bidirectional tool integrations.

These mirror the hand-rolled tools (Notion, Slack, …) but use Composio's managed
OAuth instead of pasted credentials, and are ``direction="bidirectional"`` so the
same connection both receives triggers (inbound → re-run axes) and executes
actions (outbound → diagnostic summaries).

The ``config_schema`` is intentionally **empty**: there are no credential fields
to fill. ``config`` instead holds Composio identifiers managed by the connect
flow: ``{connection_id, account_id, connected, triggers}``.
"""
from __future__ import annotations

import logging

from ...base import TestResult, ToolIntegration
from ...registry import register
from . import client as composio

logger = logging.getLogger("moufida.tools.composio.tool")

# Empty schema → the Settings UI renders a Connect button instead of a form.
_NO_CREDENTIALS_SCHEMA = {"type": "object", "properties": {}, "required": []}

_SCORE_LABELS = {
    "market": "Marché",
    "commercial_offer": "Offre Commerciale",
    "innovation": "Innovation",
    "scalability": "Scalabilité",
    "green": "Green",
}


def _summary_lines(project_id: str, scores: dict, blockers: list, roadmap: dict | None) -> list[str]:
    """Shared markdown-ish summary used by every Composio outbound action."""
    lines = [f"Moufida — diagnostic ({project_id[:8]}…)", ""]
    for name, score in (scores or {}).items():
        bar = "🟢" if score >= 3.5 else ("🟡" if score >= 2.0 else "🔴")
        lines.append(f"{bar} {_SCORE_LABELS.get(name, name)}: {score:.1f}/5")
    critical = [b for b in (blockers or []) if b.get("severity") == "critical"]
    if critical:
        lines.append("")
        lines.append(f"🔴 {len(critical)} bloquant(s) critique(s):")
        for b in critical[:3]:
            lines.append(f"  • {b.get('description', '')}")
    if roadmap:
        immediate = roadmap.get("immediate") or []
        if immediate:
            lines.append("")
            lines.append(f"🚀 Action immédiate: {immediate[0].get('action', '')}")
    return lines


class ComposioTool(ToolIntegration):
    """Base for every Composio-managed tool. Subclasses set slug/label/domain."""

    direction = "bidirectional"
    config_schema = _NO_CREDENTIALS_SCHEMA

    async def test_connection(self, config: dict) -> TestResult:
        if not composio.is_available():
            return TestResult(ok=False, message="Composio non configuré (COMPOSIO_API_KEY manquant)")
        conn_id = (config or {}).get("connection_id")
        if not conn_id:
            return TestResult(ok=False, message="Non connecté — cliquez sur « Connecter »")
        try:
            status = composio.connection_status(conn_id)
        except composio.ComposioUnavailable as exc:
            return TestResult(ok=False, message=str(exc))
        if status["connected"]:
            return TestResult(ok=True, message="Connecté via Composio")
        return TestResult(ok=False, message=f"Connexion {status['status']} — autorisation en attente")

    # ---- outbound: route push hooks through Composio actions ----

    def _action_params(self, text: str, config: dict) -> dict:
        """Per-app param shape for the outbound action. Overridden per subclass."""
        return {"text": text}

    async def on_diagnostic_complete(self, project_id, profile, scores, blockers, roadmap, config):
        if not (config or {}).get("connected"):
            return
        text = "\n".join(_summary_lines(project_id, scores, blockers, roadmap))
        try:
            composio.execute_action(self.slug, self._action_params(text, config),
                                    connection_id=config.get("connection_id"))
        except composio.ComposioUnavailable as exc:
            logger.warning("%s outbound (diagnostic) skipped: %s", self.slug, exc)

    async def on_score_alert(self, project_id, alert, config):
        if not (config or {}).get("connected"):
            return
        sev = alert.get("severity", "info")
        emoji = {"critical": "🔴", "warning": "🟡"}.get(sev, "🔵")
        text = f"{emoji} {alert.get('title', 'Alerte')}\n{alert.get('body', '')}"
        try:
            composio.execute_action(self.slug, self._action_params(text, config),
                                    connection_id=config.get("connection_id"))
        except composio.ComposioUnavailable as exc:
            logger.warning("%s outbound (alert) skipped: %s", self.slug, exc)


@register
class ComposioNotionTool(ComposioTool):
    slug = "composio_notion"
    label = "Notion (Composio)"
    domain = "documentation"

    def _action_params(self, text: str, config: dict) -> dict:
        return {"title": "Moufida — diagnostic", "content": text}


@register
class ComposioSlackTool(ComposioTool):
    slug = "composio_slack"
    label = "Slack (Composio)"
    domain = "communication"

    def _action_params(self, text: str, config: dict) -> dict:
        params: dict = {"text": text}
        channel = (config or {}).get("channel")
        if channel:
            params["channel"] = channel
        return params


@register
class ComposioSheetsTool(ComposioTool):
    slug = "composio_sheets"
    label = "Google Sheets (Composio)"
    domain = "finance"

    def _action_params(self, text: str, config: dict) -> dict:
        return {"values": [[line] for line in text.split("\n")]}


@register
class ComposioGithubTool(ComposioTool):
    slug = "composio_github"
    label = "GitHub (Composio)"
    domain = "development"

    def _action_params(self, text: str, config: dict) -> dict:
        return {"title": "Moufida — diagnostic", "body": text}
