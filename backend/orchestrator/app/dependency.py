"""Dependency resolution engine.

Decides what to re-run when any plan section changes. Called by every update
source (manual edit, chat, tool signal, daemon event).

The graph is the single source of truth in this module. axis_registry.py
DIAGNOSTIC_WAVES must stay consistent with it — they share the same topology.

Cycle note: business-model and operations are mutually dependent (each lists the
other as a dependency). They form the only SCC in the graph. This is handled
explicitly: when either is in the dirty set both are scheduled, always in the
order [business-model, operations].
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("moufida.dependency")

# ---------------------------------------------------------------------------
# The authoritative dependency graph
# ---------------------------------------------------------------------------

DEPENDS_ON: dict[str, list[str]] = {
    "ideation":       [],
    "market":         ["ideation"],
    "product":        ["market", "ideation"],
    "brand":          ["ideation", "product"],
    "business-model": ["product", "market", "operations"],
    "legal":          ["business-model", "ideation"],
    "operations":     ["business-model", "product"],
    "marketing":      ["product", "brand", "operations"],
    "sales":          ["marketing", "operations", "business-model"],
    "roadmap":        [],   # virtual; handled separately — depends on all
}

# The one known SCC: business-model ↔ operations.
_SCC_PAIR = frozenset({"business-model", "operations"})
# Canonical re-run order within the SCC (BM is the primary economic driver).
_SCC_ORDER = ["business-model", "operations"]

# ---------------------------------------------------------------------------
# Reverse graph helpers
# ---------------------------------------------------------------------------

def _build_reverse() -> dict[str, set[str]]:
    rev: dict[str, set[str]] = {ax: set() for ax in DEPENDS_ON}
    for ax, deps in DEPENDS_ON.items():
        for dep in deps:
            if dep in rev:
                rev[dep].add(ax)
    return rev


_REVERSE: dict[str, set[str]] = _build_reverse()


def dependents_of(axis: str) -> set[str]:
    """Return the set of axes that directly depend on *axis*."""
    return set(_REVERSE.get(axis, set()))


# ---------------------------------------------------------------------------
# Transitive affected-set computation
# ---------------------------------------------------------------------------

def affected_axes(changed: set[str]) -> list[str]:
    """Return axes to re-run (in safe order) when *changed* sections are dirty.

    The changed axes themselves are excluded unless the SCC cycle pulls them
    back in. roadmap is always appended last when any re-run occurs.

    Worked example (new-logic.md §5.5):
        changed = {"business-model"}
        → returns ["operations", "legal", "marketing", "sales", "roadmap"]
    """
    if not changed:
        return []

    # BFS forward over reverse edges to build the transitive dirty set.
    dirty: set[str] = set()
    queue = list(changed)
    while queue:
        ax = queue.pop()
        for dep in _REVERSE.get(ax, set()):
            if dep not in dirty and dep not in changed:
                dirty.add(dep)
                queue.append(dep)

    # If either SCC member is dirty, ensure both are scheduled (once each).
    if dirty & _SCC_PAIR:
        dirty |= _SCC_PAIR - changed   # add the other member if not already dirty

    # Remove the virtual roadmap — we handle it separately at the end.
    dirty.discard("roadmap")

    # Topological sort of the dirty set over the condensed DAG.
    # The SCC pair is treated as a single node and expanded in _SCC_ORDER.
    ordered: list[str] = _topo_sort(dirty)

    # roadmap is always last whenever anything re-runs.
    ordered.append("roadmap")
    return ordered


def _topo_sort(axes: set[str]) -> list[str]:
    """Kahn's algorithm over the dirty set, treating the SCC as a single node."""
    # Replace SCC members with a placeholder for the sort.
    scc_in_dirty = axes & _SCC_PAIR
    working: set[str] = (axes - _SCC_PAIR)
    if scc_in_dirty:
        working.add("__scc__")

    # Build in-degree counts within the working set.
    def _deps_of(node: str) -> list[str]:
        if node == "__scc__":
            # SCC depends on product and market (BM's non-SCC deps).
            return [d for d in ["product", "market"] if d in working]
        return [d for d in DEPENDS_ON.get(node, []) if d in working and d not in _SCC_PAIR]

    in_degree = {n: 0 for n in working}
    for n in working:
        for dep in _deps_of(n):
            in_degree[n] += 1

    result: list[str] = []
    queue = sorted(n for n, deg in in_degree.items() if deg == 0)
    while queue:
        node = queue.pop(0)
        if node == "__scc__":
            result.extend(ax for ax in _SCC_ORDER if ax in scc_in_dirty)
        else:
            result.append(node)
        for n in list(working):
            if n == node:
                continue
            if node in _deps_of(n):
                in_degree[n] -= 1
                if in_degree[n] == 0:
                    queue.append(n)
                    queue.sort()

    # Any remaining nodes (shouldn't happen with a correct graph) append last.
    scheduled = set(result) | (scc_in_dirty if scc_in_dirty else set())
    for ax in axes - scheduled:
        result.append(ax)

    return result


# ---------------------------------------------------------------------------
# Seed the dependency_graph mirror table on startup
# ---------------------------------------------------------------------------

async def seed_db_mirror(pool: Any) -> None:
    """Upsert the in-code graph into dependency_graph for traceability."""
    try:
        async with pool.acquire() as conn:
            for axis, deps in DEPENDS_ON.items():
                await conn.execute(
                    """
                    INSERT INTO dependency_graph (axis, depends_on, version)
                    VALUES ($1, $2, 1)
                    ON CONFLICT (axis, version) DO UPDATE
                       SET depends_on = EXCLUDED.depends_on
                    """,
                    axis,
                    deps,
                )
    except Exception as exc:
        logger.warning("dependency_graph mirror seed failed: %s", exc)
