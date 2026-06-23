# 06 — Continuous Updates: Four Sources, Event Feed, "What's New?"

> Implements new-logic.md §5.1–5.4, §5.6–5.7. Every source funnels into the
> dependency engine (`05`) and writes an `events` row (`01 §3`). This is the
> "liveness" layer that makes a project never-static.

---

## 1. Shared pipeline

All four sources converge on one function:

```
signal → interpret() → {changed_axes, section_patches, summary, severity, suggestion}
       → apply patches to plan_sections (new versions, source=<src>)
       → dependency.rerun(project_id, changed_axes, mode)
       → write events row (diff, axes_affected, suggestion)
       → SSE push so the UI updates live
```

`interpret()` is source-specific (LLM for chat/daemon, schema-mapped for tools,
direct for manual edits). The tail (apply → rerun → event → SSE) is shared in
`backend/orchestrator/app/updates/pipeline.py`.

---

## 2. Source A — Manual UI edits (§5.1)

Already half-built via the plan document (`03 §5`).
- User edits section X in `PlanDocument.tsx` → `POST /project/{id}/section/{axis}`
  body `{content}` → persists new `plan_sections` version (`source='manual'`).
- Pipeline runs `dependency.rerun(changed={axis})`; affected axes return
  proposals into a review queue; user approves each.
- Event: `"You updated the budget — Business Model and Operations re-generated"`.

---

## 3. Source C — Tool integration signals (§5.3)

(Listed before B/D because it reuses existing tool infra.)

> **The real toolkit.** The shipped integrations are **Slack, Notion, Google
> Sheets, Google Analytics, GitHub** (`moufida-tools/toolkit/tools/`), not the
> Odoo/Twenty/Plane/Plausible/Frappe set sketched in `new-logic.md §5.3`. Each
> tool subclasses `ToolIntegration` and declares a `direction`:
> - **pull** (`github`, `google_analytics`) — override `enrich_profile()`, which
>   already runs *before* the scoring wave (`diagnostic_router.py:130`) and
>   upgrades **evidence tiers** (`mi`) + blank-fills profile fields.
> - **push** (`slack`, `notion`, `google_sheets`) — override
>   `on_diagnostic_complete()` / `on_score_alert()`; already fanned out after
>   scoring (`diagnostic_router.py:189`) and on daemon alerts
>   (`redis_consumer.py:77`).
>
> So "tool signals → re-run axes" is a **new capability layered on the pull
> path**: today pull tools only enrich at diagnostic time; they do not yet emit
> standalone signals that trigger a re-run between diagnostics.

- Existing `tools_router` + `tool_integrations` (global, one row per slug) handle
  CRUD + test + sync. Add: when a **pull** tool fetches data (in
  `enrich_profile`, or a new lightweight poll), write the salient deltas as rows
  to `tool_signals` (`01 §4`) so they can drive a re-run outside a full
  diagnostic.
- Signal→axis routing table in code, keyed by the **real tool slugs** + their
  signal types:

```python
TOOL_AXES = {
  # pull tools — emit signals that can trigger re-runs
  "github":           ["product", "operations"],   # commit/PR velocity, issue closure
  "google_analytics": ["product", "marketing"],    # traffic, conversion trends
  # push tools — receive outputs; not signal sources, but listed for completeness
  "slack":            [],
  "notion":           [],
  "google_sheets":    [],
}

# Finer routing by signal_type (what changed), used by interpret():
SIGNAL_AXES = {
  "commit_velocity":   ["product"],
  "pr_velocity":       ["product", "operations"],
  "issue_closure":     ["operations"],
  "traffic_spike":     ["marketing"],
  "conversion_change": ["product", "marketing"],
}
```
- `interpret()` for tools is mostly **structured**: map `signal_type` + payload
  to section patches (e.g. GitHub `commit_velocity` spike → bump
  `product.mvp_features` progress / evidence; GA `conversion_change` → update
  `marketing.channels` performance) then `rerun`. LLM only to phrase the summary.
- Reuse the existing **evidence-tier** semantics: a pull signal that *verifies*
  a field (e.g. GitHub confirms `product_stage`) upgrades its tier (never
  downgrades), exactly as `enrich_profile` does today.
- Tool updates may `auto_approve` structured patches but still surface a
  "Would you like to see the updated Business Model?" suggestion via the event.
- Mark `tool_signals.processed=true` after interpretation.
- **Push tools need no change here** — they already react to the re-run's new
  diagnostic via `on_diagnostic_complete` (Slack summary, Notion/Sheets export).

---

## 4. Source B — Chat-driven updates (§5.2)

- Chat HUD (`ChatPanel.tsx`) already exists. Add intent detection: a message
  that asserts a change ("I hired a CTO", "pivoted to B2B") vs. a question.
- `interpret()` = LLM call: given the message + current `plan_sections`, return
  `{changed_axes, section_patches, summary, suggested_extra_axes}`.
- Apply patches → `rerun` → event (`source='chat'`). Moufida replies with what
  changed **and** the suggested wider scope ("Product score may also be
  affected — re-run Product too?"). If the user agrees, run the extra axes.
- Scope confirmation is a follow-up chat turn, not a separate endpoint.

`POST /project/{id}/chat` returns `{reply, event_id, proposed_scope}`.

---

## 5. Source D — Go daemon events (§5.4)

- Daemon (`daemon/`) already watches sources → alerts → SSE. Extend: when a
  watcher detects a *significant* external change (regulation, competitor,
  market news, macro), it publishes a richer payload that the orchestrator's
  `redis_consumer` turns into an **interpreted event** with a `suggestion`.
- Orchestrator `interpret()` (LLM) maps the news to affected axes + a suggested
  action, writes an `events` row with `status='new'` and a `suggestion`.
- Frontend renders the **Event Card** (§5.4) with three actions:

| Action | Endpoint | Behaviour |
|--------|----------|-----------|
| **Act** | `POST /event/{id}/act` | pipeline applies suggested patches (`auto_approve`) + `rerun` + reports back; `status='acted'` |
| **Manual** | `POST /event/{id}/manual` | opens the named section(s) for the user to edit; `status='manual'` |
| **Ignore** | `POST /event/{id}/ignore` | `status='ignored'`; revisitable from the feed |

Daemon work is mostly orchestrator-side interpretation; the Go watcher only
needs to emit a structured "significant change" payload (sector, kind, text).

---

## 6. Event Feed UI (§5.6)

`EventFeed.tsx` (new, in dashboard): chronological, filterable list reading
`GET /project/{id}/events?source=&axis=&from=&to=&severity=`.

Each row: source icon (✎ manual / 💬 chat / 📡 tool / 🛰️ daemon), timestamp,
summary, `axes_affected` chips, Moufida's action, **View diff**, and Revisit for
ignored events.

**View diff** → `GET /event/{id}/diff` → `plan_sections` before/after per axis →
side-by-side `DiffView.tsx` (field-level, using the shallow `content` shapes
from `02 §3`). This diff component is reused by the history-compare view (`04 §5`).

---

## 7. "What's new?" query (§5.7)

- Voice/chat intent "what's new / what changed since X / roadmap updates" →
  `GET /project/{id}/whats-new?since=` → recent `events` ranked by severity.
- LLM summarises into the prioritised natural-language brief shown in §5.7.
- Drill-in: each summarised item links to its `event_id` (View diff).
- Wire into the existing voice pipeline + `ChatPanel`.

---

## 8. Checklist

- [ ] `updates/pipeline.py` shared apply→rerun→event→SSE tail
- [ ] Source A: `POST /section/{axis}` manual edit → pipeline
- [ ] Source C: pull tools (`github`, `google_analytics`) emit `tool_signals` → `TOOL_AXES`/`SIGNAL_AXES` + structured interpret (reuse evidence-tier upgrades)
- [ ] Source B: chat intent detection + `interpret()` + scope confirmation
- [ ] Source D: daemon significant-change payload + orchestrator interpret + Event Card endpoints (act/manual/ignore)
- [ ] `EventFeed.tsx` + filters + `GET /events`
- [ ] `DiffView.tsx` + `GET /event/{id}/diff` (shared with `04`)
- [ ] "What's new?" endpoint + voice/chat wiring
- [ ] i18n parity for all new strings
