"""Single source of truth for the axis topology: ports, compose hostnames, which
composite score each axis owns, and the Go-daemon metric -> axis routing table.

Used by the diagnostic runner, generation runner, dependency engine, and the
Redis consumer.

Axis 10 (gtm / go-to-market-service) is kept in AXES for health-check purposes
but is no longer routed in diagnostic or generation passes. Roadmap is the
virtual axis 10 produced by the RAG generator in the orchestrator, not a
network service.
"""
from __future__ import annotations

import os

# slug -> (axis number, internal port, composite score owned or None)
AXES: dict[str, dict] = {
    "ideation":       {"axis": 1,  "port": 8101, "score": None,             "compose_host": "ideation-service"},
    "market":         {"axis": 2,  "port": 8102, "score": "market",         "compose_host": "market-intelligence-service"},
    "product":        {"axis": 3,  "port": 8103, "score": "commercial_offer","compose_host": "product-offering-service"},
    "brand":          {"axis": 4,  "port": 8104, "score": "innovation",      "compose_host": "brand-innovation-service"},
    "business-model": {"axis": 5,  "port": 8105, "score": "scalability",     "compose_host": "business-model-service"},
    "legal":          {"axis": 6,  "port": 8106, "score": "green",           "compose_host": "legal-compliance-service"},
    "marketing":      {"axis": 7,  "port": 8107, "score": None,             "compose_host": "marketing-service"},
    "sales":          {"axis": 8,  "port": 8108, "score": None,             "compose_host": "sales-service"},
    "operations":     {"axis": 9,  "port": 8109, "score": "scalability",     "compose_host": "operations-service"},
    # gtm kept for container health-check; not routed in diagnostic/generation passes.
    "gtm":            {"axis": 10, "port": 8110, "score": None,             "compose_host": "go-to-market-service"},
}

# The nine network axes that participate in diagnostic and generation passes.
# roadmap is virtual (orchestrator RAG call), not in this list.
NETWORK_AXES: list[str] = [
    "ideation", "market", "product", "brand",
    "business-model", "legal", "operations", "marketing", "sales",
]

# Go-daemon metric type -> axis slugs whose metric_update endpoint is invoked.
METRIC_ROUTES: dict[str, list[str]] = {
    "competitor": ["market"],
    "budget":     ["business-model"],
    "legal":      ["legal"],
    "milestone":  ["ideation", "operations"],   # was ["ideation", "gtm"]
    "trend":      ["market"],
}

# Tool signal slug -> axis slugs to re-run when an inbound trigger fires
# (Phase G). Mirrors METRIC_ROUTES but for Composio/tool_signals, not the daemon.
TOOL_AXES: dict[str, list[str]] = {
    "notion":           ["ideation", "product"],     # spec / doc changes
    "slack":            ["operations"],              # team / ops signals
    "google_sheets":    ["business-model", "market"],
    "google_analytics": ["market", "marketing"],
    "github":           ["product", "operations"],
}

# Composio slugs mirror the hand-rolled ones with a prefix; normalise both to the
# canonical key used in TOOL_AXES.
_TOOL_SLUG_ALIASES = {
    "composio_notion": "notion",
    "composio_slack":  "slack",
    "composio_sheets": "google_sheets",
    "composio_github": "github",
    "sheets":          "google_sheets",
}


def axes_for_tool(slug: str) -> list[str]:
    """Resolve a tool/signal slug (hand-rolled or composio_*) to its re-run axes."""
    key = _TOOL_SLUG_ALIASES.get(slug, slug)
    return TOOL_AXES.get(key, [])


# Sequential order for the creation-mode generation loop (ideation first,
# roadmap last as a virtual step handled by the orchestrator).
GENERATION_ORDER: list[str] = [
    "ideation", "market", "product", "brand",
    "business-model", "legal", "operations", "marketing", "sales",
    # "roadmap" — virtual; run by orchestrator after all nine are approved
]


def axis_host(slug: str) -> str:
    """Compose-internal base URL for an axis service."""
    info = AXES[slug]
    host = os.getenv(f"AXIS_{info['axis']:02d}_HOST", info["compose_host"])
    return f"http://{host}:{info['port']}"


# Dependency-ordered waves for the STATE_EXISTING diagnostic pass.
#   Wave 0 runs first and in parallel;
#   Wave 1 (brand) consumes wave-0 outputs;
#   Wave 2 runs the remaining scoring axes in parallel.
# This order is consistent with dependency.py DEPENDS_ON — do not diverge.
DIAGNOSTIC_WAVES: list[list[str]] = [
    ["ideation", "market", "product"],
    ["brand"],
    ["business-model", "legal", "operations", "marketing", "sales"],
]


def diagnostic_order() -> list[list[str]]:
    """The dependency-ordered diagnostic waves (see ``DIAGNOSTIC_WAVES``)."""
    return DIAGNOSTIC_WAVES
