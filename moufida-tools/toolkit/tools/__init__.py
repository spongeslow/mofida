"""Lazy loader — imports every tool module so @register decorators fire."""
from __future__ import annotations


def _load_all_tools() -> None:
    from . import slack       # noqa: F401
    from . import notion      # noqa: F401
    from . import google_sheets  # noqa: F401
    from . import google_analytics  # noqa: F401
    from . import github      # noqa: F401
    # Composio-backed bidirectional adapters (Phase G). Import is guarded so a
    # missing composio SDK never blocks loading the hand-rolled tools.
    try:
        from .composio import tool as _composio_tool  # noqa: F401
    except Exception:  # pragma: no cover - defensive
        import logging
        logging.getLogger("moufida.tools").warning("composio tools not loaded", exc_info=True)
