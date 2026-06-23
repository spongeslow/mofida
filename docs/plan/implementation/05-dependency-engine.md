# 05 — Dependency Resolution Engine

> Implements new-logic.md §5.5. The shared brain that decides **what to re-run**
> when any source changes a section. Consumed by every flow in `06`, plus the
> manual-edit path in `03 §5`.

---

## 1. The graph (authoritative, in code)

New module `backend/orchestrator/app/dependency.py`. The graph is the design
doc's table verbatim:

```python
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
    "roadmap":        ["*"],   # depends on all
}
```

> **Cycle note:** `business-model ↔ operations` are mutually dependent in the
> doc's table (BM depends on Operations *and* Operations depends on BM). A naive
> forward walk + topo sort will not terminate. Handle explicitly — see §3.

This must agree with `axis_registry.DIAGNOSTIC_WAVES`. Reconcile both to one
source: derive the waves from `DEPENDS_ON` (topological levels) so there is no
drift. Mirror to the `dependency_graph` table (`01 §7`) on startup if that table
is kept.

---

## 2. Reverse edges (dependents)

Re-running propagates to **dependents** (who depends on X), the reverse of
`DEPENDS_ON`:

```python
def dependents_of(axis: str) -> set[str]:
    return {a for a, deps in DEPENDS_ON.items() if axis in deps}
```
`roadmap` (`["*"]`) is a dependent of everything, so any change marks roadmap
stale (matches §6.4 "flagged stale, user approves regen").

---

## 3. Affected-set computation

```python
def affected_axes(changed: set[str]) -> list[str]:
    """Transitive-closure of dependents of the changed axes, returned in a
    safe re-run order. Excludes the originally-changed axes themselves unless a
    cycle pulls them back in."""
```
Algorithm:
1. BFS forward over reverse edges from `changed` → `dirty` set (transitive
   dependents). Always include `roadmap` if anything changed.
2. **Break the BM↔Operations cycle:** treat that pair as a single SCC; when
   either is dirty, re-run both once, in the order BM→Operations (BM is the
   primary economic driver). Use Tarjan/condensation, or hard-code the one known
   SCC for the demo (simplest, documented).
3. Topologically order the dirty set over the **condensed** DAG so each axis runs
   after its dependencies' latest content is available.

Worked example from the doc (§5.5) must reproduce exactly:
```
change = {business-model}
→ dirty = {legal, operations, marketing, sales, roadmap}   # BM's dependents (+closure)
→ order = [operations, legal, marketing, sales, roadmap]
→ untouched: ideation, market, product, brand
```
Add this as a unit test fixture.

---

## 4. The re-run scheduler

```python
async def rerun(project_id, changed: set[str], mode: str, *, auto_approve=False):
    order = affected_axes(changed)
    for axis in order:
        if axis == "roadmap":
            mark_roadmap_stale(project_id)          # never auto-regen (§6.4)
            continue
        if mode == "creation":
            proposal = await run_generation_step(project_id, axis)   # 02 §6
            queue_for_review(project_id, axis, proposal)             # user approves
        else:  # diagnosis
            await rerun_axis_evaluate(project_id, axis)              # recompute score
    return order
```
- **Creation-mode** re-runs produce **proposals the user reviews** (never silent
  overwrites) — except when a source explicitly says "Act" with `auto_approve`
  (daemon/tool can auto-apply structured updates per §5.3/§5.4, still logged).
- **Diagnosis-mode** re-runs recompute scores directly.
- Every scheduler invocation writes one `events` row with `axes_affected=order`
  and a `diff` (before/after live `plan_sections`), powering the Event Feed and
  "Business Model and Operations re-generated" messaging.

---

## 5. API surface

| Method & path | Purpose |
|---------------|---------|
| `POST /project/{id}/rerun` body `{changed:[...], reason}` | manual/test trigger of the scheduler |
| `GET  /project/{id}/dependencies` | the graph + which axes a given change would hit (UI "why re-run?") |

Sources in `06` (chat/tool/daemon) call `rerun()` internally rather than this
HTTP route; the route exists for the manual-edit path and testing.

---

## 6. Checklist

- [ ] `dependency.py` with `DEPENDS_ON`, `dependents_of`, `affected_axes`
- [ ] Reconcile `axis_registry.DIAGNOSTIC_WAVES` to derive from `DEPENDS_ON`
- [ ] SCC handling for `business-model ↔ operations` (documented)
- [ ] `rerun()` scheduler (creation → proposals, diagnosis → recompute)
- [ ] Emit one `events` row per scheduler run with diff + `axes_affected`
- [ ] Unit test reproducing the doc's §5.5 worked example
- [ ] `GET /dependencies` for the UI explainer
