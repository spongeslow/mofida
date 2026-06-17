"""Single source of truth for the axis topology: ports, compose hostnames, which
composite score each axis owns, and the Go-daemon metric -> axis routing table.

Used by the diagnostic runner (Phase 2) and the Redis consumer (Phase 5).
"""
from __future__ import annotations

import os

# slug -> (axis number, internal port, composite score owned or None)
AXES: dict[str, dict] = {
    "ideation": {"axis": 1, "port": 8101, "score": None, "compose_host": "ideation-service"},
    "market": {"axis": 2, "port": 8102, "score": "market", "compose_host": "market-intelligence-service"},
    "product": {"axis": 3, "port": 8103, "score": "commercial_offer", "compose_host": "product-offering-service"},
    "brand": {"axis": 4, "port": 8104, "score": "innovation", "compose_host": "brand-innovation-service"},
    "business-model": {"axis": 5, "port": 8105, "score": "scalability", "compose_host": "business-model-service"},
    "legal": {"axis": 6, "port": 8106, "score": "green", "compose_host": "legal-compliance-service"},
    "marketing": {"axis": 7, "port": 8107, "score": None, "compose_host": "marketing-service"},
    "sales": {"axis": 8, "port": 8108, "score": None, "compose_host": "sales-service"},
    "operations": {"axis": 9, "port": 8109, "score": "scalability", "compose_host": "operations-service"},
    "gtm": {"axis": 10, "port": 8110, "score": None, "compose_host": "go-to-market-service"},
}

# Go-daemon metric type -> axis slugs whose metric_update endpoint is invoked.
METRIC_ROUTES: dict[str, list[str]] = {
    "competitor": ["market"],
    "budget": ["business-model"],
    "legal": ["legal"],
    "milestone": ["ideation", "gtm"],
    "trend": ["market"],
}


def axis_host(slug: str) -> str:
    """Compose-internal base URL for an axis service."""
    info = AXES[slug]
    host = os.getenv(f"AXIS_{info['axis']:02d}_HOST", info["compose_host"])
    return f"http://{host}:{info['port']}"


def diagnostic_order() -> list[list[str]]:
    """Dependency-ordered waves for the STATE_EXISTING diagnostic pass.

    Wave 1 runs first (ideation/market/product), wave 2 (brand) consumes their
    outputs, wave 3 (the remaining scoring axes) runs in parallel.
    """
    return [
        ["ideation", "market", "product"],
        ["brand"],
        ["business-model", "legal", "operations", "marketing", "sales"],
    ]
