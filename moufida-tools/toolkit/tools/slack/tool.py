"""Slack integration — push daily briefings and score alerts via incoming webhook."""
from __future__ import annotations

import httpx

from ...base import ProfilePatch, TestResult, ToolIntegration
from ...registry import register


@register
class SlackTool(ToolIntegration):
    slug = "slack"
    label = "Slack"
    domain = "communication"
    direction = "push"

    config_schema = {
        "type": "object",
        "properties": {
            "webhook_url": {
                "type": "string",
                "title": "Webhook URL",
                "description": "Incoming webhook URL from your Slack app (Apps → Incoming Webhooks)",
                "format": "uri",
            },
            "channel": {
                "type": "string",
                "title": "Channel override",
                "description": "Override the default channel, e.g. #moufida-alerts (optional)",
                "default": "",
            },
            "notify_on_diagnostic": {
                "type": "boolean",
                "title": "Send diagnostic summary",
                "description": "Post a score summary after every diagnostic run",
                "default": True,
            },
            "notify_on_alert": {
                "type": "boolean",
                "title": "Send score alerts",
                "description": "Forward critical and warning alerts triggered by the daemon",
                "default": True,
            },
        },
        "required": ["webhook_url"],
    }

    async def test_connection(self, config: dict) -> TestResult:
        url = config.get("webhook_url", "").strip()
        if not url:
            return TestResult(ok=False, message="Webhook URL is required")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"text": ":white_check_mark: Moufida — connexion réussie."})
        except httpx.HTTPError as exc:
            return TestResult(ok=False, message=f"HTTP error: {exc}")
        if resp.status_code == 200:
            return TestResult(ok=True, message="Connected — test message sent to Slack")
        return TestResult(ok=False, message=f"Slack returned {resp.status_code}: {resp.text[:200]}")

    async def on_diagnostic_complete(self, project_id, profile, scores, blockers, roadmap, config):
        if not config.get("notify_on_diagnostic", True):
            return
        url = config.get("webhook_url", "").strip()
        if not url:
            return

        lines = [f":bar_chart: *Moufida — Rapport de diagnostic* (`{project_id[:8]}…`)\n"]
        score_labels = {
            "market": "Marché",
            "commercial_offer": "Offre Commerciale",
            "innovation": "Innovation",
            "scalability": "Scalabilité",
            "green": "Green",
        }
        for name, score in scores.items():
            bar = _score_bar(score)
            label = score_labels.get(name, name)
            lines.append(f"{bar} *{label}*: {score:.1f}/5")

        critical = [b for b in blockers if b.get("severity") == "critical"]
        if critical:
            lines.append(f"\n:red_circle: *{len(critical)} bloquant(s) critique(s)*")
            for b in critical[:3]:
                lines.append(f"  • {b.get('description', '')}")

        if roadmap:
            immediate = roadmap.get("immediate") or []
            if immediate:
                lines.append(f"\n:rocket: *Action immédiate*: {immediate[0].get('action', '')}")

        payload: dict = {"text": "\n".join(lines)}
        if config.get("channel"):
            payload["channel"] = config["channel"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=payload)

    async def on_score_alert(self, project_id, alert, config):
        if not config.get("notify_on_alert", True):
            return
        url = config.get("webhook_url", "").strip()
        if not url:
            return

        sev = alert.get("severity", "info")
        emoji = {"critical": ":red_circle:", "warning": ":yellow_circle:"}.get(sev, ":blue_circle:")
        title = alert.get("title", "Alerte")
        body = alert.get("body", "")

        payload: dict = {"text": f"{emoji} *{title}*\n{body}"}
        if config.get("channel"):
            payload["channel"] = config["channel"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=payload)


def _score_bar(score: float) -> str:
    if score >= 3.5:
        return ":large_green_circle:"
    if score >= 2.0:
        return ":large_yellow_circle:"
    return ":red_circle:"
