"""Thin, defensive wrapper around the Composio SDK.

Everything Composio-specific is isolated here so the rest of Moufida talks to a
small, stable interface and so the app degrades gracefully when:
  - the ``composio`` SDK is not installed, or
  - ``COMPOSIO_API_KEY`` is unset, or
  - a remote call fails / the SDK surface differs by version.

In all those cases methods raise :class:`ComposioUnavailable` (for explicit
caller handling) or return safe empties — they never crash the process. The
hand-rolled token tools are unaffected by Composio being absent.

> SDK-version note: this targets the ``composio`` package's ``ComposioToolSet``
> facade (initiate_connection / get_connected_account / execute_action /
> create_trigger). If you pin a different Composio major, adjust the calls here
> only — nothing else imports the SDK.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("moufida.tools.composio")

# Composio app names per Moufida slug. The "composio_" prefix keeps the slugs
# distinct from the hand-rolled tools while mirroring them for the UI.
APP_BY_SLUG: dict[str, str] = {
    "composio_notion": "NOTION",
    "composio_slack":  "SLACK",
    "composio_sheets": "GOOGLESHEETS",
    "composio_github": "GITHUB",
}

# Inbound triggers registered per app on connect (trigger name → nothing fancy).
TRIGGERS_BY_SLUG: dict[str, list[str]] = {
    "composio_notion": ["NOTION_PAGE_UPDATED"],
    "composio_slack":  ["SLACK_RECEIVE_MESSAGE"],
    "composio_sheets": ["GOOGLESHEETS_ROW_ADDED"],
    "composio_github": ["GITHUB_COMMIT_EVENT"],
}

# Outbound action per app for push notifications (diagnostic summary / alert).
ACTION_BY_SLUG: dict[str, str] = {
    "composio_notion": "NOTION_CREATE_NOTION_PAGE",
    "composio_slack":  "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL",
    "composio_sheets": "GOOGLESHEETS_BATCH_UPDATE",
    "composio_github": "GITHUB_CREATE_AN_ISSUE",
}

# Single shared entity id for the single-user desktop deployment.
ENTITY_ID = os.getenv("COMPOSIO_ENTITY_ID", "default")


class ComposioUnavailable(RuntimeError):
    """Raised when Composio cannot service a request (no key / SDK / remote err)."""


def is_available() -> bool:
    """True when an API key is set and the SDK imports."""
    if not os.getenv("COMPOSIO_API_KEY"):
        return False
    try:
        import composio  # noqa: F401
    except Exception:
        return False
    return True


def _toolset():
    """Lazily build a ComposioToolSet, or raise ComposioUnavailable."""
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        raise ComposioUnavailable("COMPOSIO_API_KEY is not set")
    try:
        from composio import ComposioToolSet  # type: ignore
    except Exception as exc:  # pragma: no cover - import guard
        raise ComposioUnavailable(f"composio SDK not importable: {exc}")
    try:
        return ComposioToolSet(api_key=api_key, entity_id=ENTITY_ID)
    except TypeError:
        # Older/newer signatures may not accept entity_id in the ctor.
        return ComposioToolSet(api_key=api_key)


def app_for(slug: str) -> str | None:
    return APP_BY_SLUG.get(slug)


def slug_for_app(app: str) -> str | None:
    app_up = (app or "").upper()
    for slug, name in APP_BY_SLUG.items():
        if name == app_up:
            return slug
    return None


# --------------------------------------------------------------------------- #
# OAuth connection lifecycle                                                   #
# --------------------------------------------------------------------------- #

def initiate_connection(slug: str, redirect_url: str) -> dict:
    """Start a managed-OAuth connection; returns {redirect_url, connection_id}."""
    app = app_for(slug)
    if app is None:
        raise ComposioUnavailable(f"no Composio app mapped for slug {slug!r}")
    ts = _toolset()
    try:
        req = ts.initiate_connection(app=app, redirect_url=redirect_url, entity_id=ENTITY_ID)
    except TypeError:
        req = ts.initiate_connection(app=app, redirect_url=redirect_url)
    # The request object exposes the hosted OAuth URL + pending account id.
    redirect = (
        getattr(req, "redirectUrl", None)
        or getattr(req, "redirect_url", None)
        or (req.get("redirectUrl") if isinstance(req, dict) else None)
    )
    conn_id = (
        getattr(req, "connectedAccountId", None)
        or getattr(req, "connected_account_id", None)
        or (req.get("connectedAccountId") if isinstance(req, dict) else None)
    )
    if not redirect or not conn_id:
        raise ComposioUnavailable("Composio did not return a redirect URL / connection id")
    return {"redirect_url": redirect, "connection_id": str(conn_id)}


def connection_status(connection_id: str) -> dict:
    """Return {connected, status, account_id} for a pending/active connection."""
    ts = _toolset()
    try:
        acct = ts.get_connected_account(connection_id)
    except Exception as exc:
        raise ComposioUnavailable(f"status query failed: {exc}")
    status = (
        getattr(acct, "status", None)
        or (acct.get("status") if isinstance(acct, dict) else None)
        or "UNKNOWN"
    )
    account_id = (
        getattr(acct, "id", None)
        or (acct.get("id") if isinstance(acct, dict) else None)
        or connection_id
    )
    return {
        "connected": str(status).upper() == "ACTIVE",
        "status": str(status),
        "account_id": str(account_id),
    }


# --------------------------------------------------------------------------- #
# Triggers (inbound)                                                          #
# --------------------------------------------------------------------------- #

def enable_triggers(slug: str, connection_id: str) -> list[str]:
    """Register inbound triggers for a connection; returns enabled trigger ids."""
    triggers = TRIGGERS_BY_SLUG.get(slug, [])
    if not triggers:
        return []
    ts = _toolset()
    enabled: list[str] = []
    for name in triggers:
        try:
            res = ts.create_trigger(
                connected_account_id=connection_id,
                trigger_name=name,
                config={},
            )
            tid = (
                getattr(res, "triggerId", None)
                or (res.get("triggerId") if isinstance(res, dict) else None)
                or name
            )
            enabled.append(str(tid))
        except Exception as exc:
            logger.warning("enable trigger %s for %s failed: %s", name, slug, exc)
    return enabled


def fetch_recent_trigger_events(limit: int = 50) -> list[dict]:
    """Pull recent trigger events for the desktop poll fallback (NAT'd hosts).

    Returns a list of normalised dicts:
        {event_id, app, trigger_name, payload}
    Best-effort: returns [] when unavailable or unsupported by the SDK version.
    """
    if not is_available():
        return []
    try:
        ts = _toolset()
        client = getattr(ts, "client", None)
        if client is None:
            return []
        triggers = getattr(client, "triggers", None)
        if triggers is None:
            return []
        # The exact method name varies across SDK minors; try the common ones.
        getter = getattr(triggers, "get_trigger_logs", None) or getattr(triggers, "list_events", None)
        if getter is None:
            return []
        raw = getter()
        items = raw if isinstance(raw, list) else getattr(raw, "data", []) or []
    except Exception as exc:
        logger.info("fetch_recent_trigger_events unavailable: %s", exc)
        return []

    out: list[dict] = []
    for it in items[:limit]:
        d = it if isinstance(it, dict) else getattr(it, "__dict__", {})
        out.append({
            "event_id":     str(d.get("id") or d.get("eventId") or ""),
            "app":          str(d.get("appName") or d.get("app") or ""),
            "trigger_name": str(d.get("triggerName") or d.get("trigger") or ""),
            "payload":      d.get("payload") or d,
        })
    return out


# --------------------------------------------------------------------------- #
# Actions (outbound)                                                          #
# --------------------------------------------------------------------------- #

def execute_action(slug: str, params: dict, connection_id: str | None = None) -> dict:
    """Execute the push action for a slug with the given params."""
    action = ACTION_BY_SLUG.get(slug)
    if action is None:
        raise ComposioUnavailable(f"no Composio action mapped for slug {slug!r}")
    ts = _toolset()
    try:
        if connection_id:
            return ts.execute_action(action=action, params=params, connected_account_id=connection_id)
        return ts.execute_action(action=action, params=params, entity_id=ENTITY_ID)
    except TypeError:
        # Fall back to the minimal signature.
        return ts.execute_action(action=action, params=params)
