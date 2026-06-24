"""Thin, defensive wrapper around the Composio SDK (v3 / ``composio>=0.7``).

Everything Composio-specific is isolated here so the rest of Moufida talks to a
small, stable interface and so the app degrades gracefully when:
  - the ``composio`` SDK is not installed, or
  - ``COMPOSIO_API_KEY`` is unset, or
  - a remote call fails / the SDK surface differs by version.

In all those cases methods raise :class:`ComposioUnavailable` (for explicit
caller handling) or return safe empties — they never crash the process. The
hand-rolled token tools are unaffected by Composio being absent.

> SDK-version note: this targets the **v3** ``composio`` package's ``Composio``
> client facade (``toolkits.authorize`` / ``connected_accounts.get`` /
> ``triggers.create`` / ``tools.execute``). The pre-0.8 ``ComposioToolSet``
> facade is gone. If you pin a different Composio major, adjust the calls here
> only — nothing else imports the SDK.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("moufida.tools.composio")

# Composio toolkit slugs per Moufida slug. v3 toolkit slugs are lowercase. The
# "composio_" prefix keeps the slugs distinct from the hand-rolled tools while
# mirroring them for the UI.
APP_BY_SLUG: dict[str, str] = {
    "composio_notion": "notion",
    "composio_slack":  "slack",
    "composio_sheets": "googlesheets",
    "composio_github": "github",
}

# Inbound trigger slugs registered per toolkit on connect.
TRIGGERS_BY_SLUG: dict[str, list[str]] = {
    "composio_notion": ["NOTION_PAGE_UPDATED"],
    "composio_slack":  ["SLACK_RECEIVE_MESSAGE"],
    "composio_sheets": ["GOOGLESHEETS_ROW_ADDED"],
    "composio_github": ["GITHUB_COMMIT_EVENT"],
}

# Outbound action (tool) slug per toolkit for push notifications.
ACTION_BY_SLUG: dict[str, str] = {
    "composio_notion": "NOTION_CREATE_NOTION_PAGE",
    "composio_slack":  "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL",
    "composio_sheets": "GOOGLESHEETS_BATCH_UPDATE",
    "composio_github": "GITHUB_CREATE_AN_ISSUE",
}

# Single shared user/entity id for the single-user desktop deployment. v3 calls
# this the ``user_id``; we keep the COMPOSIO_ENTITY_ID env name for continuity.
ENTITY_ID = os.getenv("COMPOSIO_ENTITY_ID", "default")


class ComposioUnavailable(RuntimeError):
    """Raised when Composio cannot service a request (no key / SDK / remote err)."""


def is_available() -> bool:
    """True when an API key is set and the v3 ``Composio`` client imports."""
    if not os.getenv("COMPOSIO_API_KEY"):
        return False
    try:
        from composio import Composio  # noqa: F401
    except Exception:
        return False
    return True


def _client():
    """Lazily build a ``Composio`` client, or raise ComposioUnavailable."""
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        raise ComposioUnavailable("COMPOSIO_API_KEY is not set")
    try:
        from composio import Composio  # type: ignore
    except Exception as exc:  # pragma: no cover - import guard
        raise ComposioUnavailable(f"composio SDK not importable: {exc}")
    try:
        return Composio(api_key=api_key)
    except Exception as exc:
        raise ComposioUnavailable(f"composio client init failed: {exc}")


def _attr(obj: Any, *names: str, default: Any = None) -> Any:
    """First present attribute/key from ``names`` (objects or dicts)."""
    for name in names:
        if isinstance(obj, dict):
            if name in obj:
                return obj[name]
        else:
            val = getattr(obj, name, None)
            if val is not None:
                return val
    return default


def _to_dict(obj: Any) -> dict:
    if isinstance(obj, dict):
        return obj
    for meth in ("model_dump", "dict", "to_dict"):
        fn = getattr(obj, meth, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    return getattr(obj, "__dict__", {}) or {}


def app_for(slug: str) -> str | None:
    return APP_BY_SLUG.get(slug)


def slug_for_app(app: str) -> str | None:
    app_lower = (app or "").lower()
    for slug, name in APP_BY_SLUG.items():
        if name == app_lower:
            return slug
    return None


# --------------------------------------------------------------------------- #
# OAuth connection lifecycle                                                   #
# --------------------------------------------------------------------------- #

def _managed_auth_config_id(client, toolkit: str) -> str:
    """Find (or create) a Composio-managed OAuth auth config for ``toolkit``.

    ``toolkits.authorize`` is no longer usable for managed OAuth on orgs past the
    legacy-endpoint cutover, so we resolve an ``auth_config_id`` ourselves and
    drive the connection through ``connected_accounts.link``.
    """
    try:
        res = client.auth_configs.list()
        items = _attr(res, "items", "data", default=[]) or []
    except Exception as exc:
        raise ComposioUnavailable(f"auth_configs.list failed: {exc}")
    for it in items:
        tk = _attr(it, "toolkit")
        tk_slug = _attr(tk, "slug") if tk is not None else _attr(it, "toolkit_slug")
        if str(tk_slug).lower() == toolkit:
            return str(_attr(it, "id"))
    # None yet — create a managed-OAuth config for this toolkit.
    try:
        created = client.auth_configs.create(
            toolkit=toolkit,
            options={"type": "use_composio_managed_auth"},
        )
    except Exception as exc:
        raise ComposioUnavailable(f"auth_configs.create failed for {toolkit}: {exc}")
    ac_id = _attr(created, "id")
    if not ac_id:
        raise ComposioUnavailable(f"auth_configs.create returned no id for {toolkit}")
    return str(ac_id)


def initiate_connection(slug: str, redirect_url: str) -> dict:
    """Start a managed-OAuth connection; returns {redirect_url, connection_id}.

    Resolves a Composio-managed auth config for the toolkit, then calls
    ``connected_accounts.link`` to get the hosted OAuth URL the user opens.
    ``redirect_url`` is forwarded as the post-OAuth ``callback_url``.
    """
    toolkit = app_for(slug)
    if toolkit is None:
        raise ComposioUnavailable(f"no Composio toolkit mapped for slug {slug!r}")
    client = _client()
    auth_config_id = _managed_auth_config_id(client, toolkit)
    try:
        req = client.connected_accounts.link(
            user_id=ENTITY_ID,
            auth_config_id=auth_config_id,
            callback_url=redirect_url or None,
        )
    except Exception as exc:
        raise ComposioUnavailable(f"connected_accounts.link failed: {exc}")
    redirect = _attr(req, "redirect_url", "redirectUrl")
    conn_id = _attr(req, "id", "connectedAccountId", "connected_account_id")
    if not redirect or not conn_id:
        raise ComposioUnavailable("Composio did not return a redirect URL / connection id")
    return {"redirect_url": redirect, "connection_id": str(conn_id)}


def connection_status(connection_id: str) -> dict:
    """Return {connected, status, account_id} for a pending/active connection."""
    client = _client()
    try:
        acct = client.connected_accounts.get(connection_id)
    except Exception as exc:
        raise ComposioUnavailable(f"status query failed: {exc}")
    status = _attr(acct, "status", default="UNKNOWN")
    account_id = _attr(acct, "id", default=connection_id)
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
    client = _client()
    enabled: list[str] = []
    for name in triggers:
        try:
            res = client.triggers.create(
                name,
                connected_account_id=connection_id,
                user_id=ENTITY_ID,
                trigger_config={},
            )
            tid = _attr(res, "trigger_id", "triggerId", "id", default=name)
            enabled.append(str(tid))
        except Exception as exc:
            logger.warning("enable trigger %s for %s failed: %s", name, slug, exc)
    return enabled


def fetch_recent_trigger_events(limit: int = 50) -> list[dict]:
    """Pull recent trigger events for the desktop poll fallback (NAT'd hosts).

    Returns a list of normalised dicts:
        {event_id, app, trigger_name, payload}
    Best-effort: returns [] when unavailable or unsupported by the SDK version.
    The v3 SDK favours realtime ``triggers.subscribe`` (websocket) over a
    pull-recent endpoint, so this stays a safe no-op unless a list method is
    exposed.
    """
    if not is_available():
        return []
    try:
        client = _client()
        triggers = getattr(client, "triggers", None)
        getter = getattr(triggers, "list_active", None) if triggers else None
        if getter is None:
            return []
        raw = getter()
        items = raw if isinstance(raw, list) else (_attr(raw, "items", "data", default=[]) or [])
    except Exception as exc:
        logger.info("fetch_recent_trigger_events unavailable: %s", exc)
        return []

    out: list[dict] = []
    for it in items[:limit]:
        d = _to_dict(it)
        out.append({
            "event_id":     str(d.get("id") or d.get("eventId") or ""),
            "app":          str(d.get("toolkit") or d.get("appName") or d.get("app") or ""),
            "trigger_name": str(d.get("triggerName") or d.get("trigger") or d.get("slug") or ""),
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
    client = _client()
    try:
        if connection_id:
            res = client.tools.execute(action, arguments=params, connected_account_id=connection_id)
        else:
            res = client.tools.execute(action, arguments=params, user_id=ENTITY_ID)
    except Exception as exc:
        raise ComposioUnavailable(f"action {action} failed: {exc}")
    return _to_dict(res)
