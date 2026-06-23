# 12 — Phase G: No-Code Bidirectional Tool Integrations (Composio)

> **Workstream:** let founders connect tools (Notion, Slack, Google Sheets,
> GitHub, …) **without touching credentials or code**, via Composio's managed
> OAuth, and make the link **bidirectional** — a change in Notion/Slack flows back
> into Moufida and re-runs the affected axes. Reuses the existing `toolkit`
> framework (`moufida-tools/toolkit/`), the `tool_integrations` / `tool_signals`
> tables, `tools_router.py`, and the dependency re-run engine.
>
> **Primary surfaces:** `moufida-tools/toolkit/`, `backend/orchestrator/app/`,
> `db/migrations/`, `frontend/src/components/settings/`, `.env` / compose.
> **Depends on:** independent of E/F. **Free:** Composio free tier; key in `.env`.
> **Source of truth for behaviour:** `new-logic.md §5.3` + the master plan.

---

## 1. Why Composio (the gap today)

The `toolkit` framework is solid but every tool makes the user **fetch and paste
credentials**:
- `tools/notion/tool.py` → `config_schema` requires an `integration_token` and a
  `database_id` the user must find manually.
- All five tools (`notion`, `slack`, `github`, `google_sheets`,
  `google_analytics`) are `direction="push"` — nothing flows **back** into Moufida.

Composio closes both gaps:
- **Managed OAuth** — the user clicks "Connect", authorises in a popup, and
  Composio stores/refreshes the tokens. No `config_schema` credential fields.
- **Triggers (webhooks)** — Composio pushes inbound events (Notion page updated,
  Slack message, new Sheet row) to a Moufida webhook → genuine bidirectionality.
- One SDK, 250+ apps, a **free tier**, and it is a hosted broker (the "middle
  party like Google" the product brief asked for).

> The existing hand-rolled tools stay as-is; Composio is added **alongside** them
> as bidirectional adapters on the same `ToolIntegration` contract.

---

## 2. Current state (verified against the repo)

- `toolkit/base.py`: `ToolIntegration` ABC with `slug/label/domain/direction`,
  `config_schema`, and hooks `test_connection`, `on_diagnostic_complete`,
  `on_score_alert`, `enrich_profile` (returns a `ProfilePatch`).
- `toolkit/manager.py` `ToolManager`: `list_states`, `get_state`, `save`,
  `test`, `enrich_profile`, `dispatch_diagnostic`, `dispatch_alert` — all keyed
  off `tool_integrations` rows where `enabled = TRUE`.
- `toolkit/registry.py`: `@register` decorator keyed by slug.
- `tools_router.py`: `GET/PUT /tools`, `/tools/{slug}`, `/tools/{slug}/test`,
  `/tools/{slug}/sync`.
- DB: `tool_integrations` (per-tool config/enabled), `tool_signals` (raw inbound
  data — **table exists but is not consumed yet**).
- `dependency.affected_axes(changed: set[str]) -> list[str]` schedules re-runs;
  `axis_registry.METRIC_ROUTES` routes daemon metrics → axes. There is **no**
  signal→axis routing table yet (the `009` migration comment references a
  `TOOL_AXES` that does not exist — Phase G adds it).

---

## 3. Target state

1. A founder opens Settings → clicks **Connect Notion** → OAuth popup → status
   flips to *Connected*. No tokens pasted.
2. Editing the connected Notion page (or posting in Slack) sends a Composio
   trigger to Moufida → a `tool_signals` row → routed to the affected axes →
   re-run proposals/score updates → SSE to the UI.
3. A diagnostic completing posts a formatted summary out to Slack/Notion through
   Composio actions (replacing per-tool SDK calls for OAuth-managed tools).

---

## G1. Composio adapter on the existing contract

### Dependencies & config
- Add `composio` (Python SDK) to `backend/orchestrator/Dockerfile`'s pip block
  (the orchestrator hosts `tools_router` and imports `toolkit`).
- `.env` / `.env.example`: `COMPOSIO_API_KEY=` (free tier). Pass it to the
  orchestrator service env in `docker-compose.yml`.

### New `toolkit/tools/composio/tool.py`
- A base `ComposioTool(ToolIntegration)` with `direction = "bidirectional"` and
  an **empty** `config_schema` (no credential fields — auth is OAuth-managed).
  `config` instead stores Composio identifiers: `{ connection_id, account_id,
  connected: bool }`.
- Per-app subclasses register slugs that mirror the existing ones so the UI and
  routing are uniform, e.g. `composio_notion`, `composio_slack`,
  `composio_sheets`. Each declares the Composio app + the actions/triggers it
  uses.
- `test_connection(config)` → query Composio for the connection status by
  `connection_id`; return `TestResult(ok=connected, message=...)`.
- `on_diagnostic_complete(...)` / `on_score_alert(...)` → execute a Composio
  **action** (e.g. `NOTION_CREATE_PAGE`, `SLACK_POST_MESSAGE`) with the same
  payloads the hand-rolled tools build today (reuse the Notion block-builder
  helpers as a formatting reference).

> Registration is automatic via `@register` once the module is imported by
> `toolkit/tools/_load_all_tools()`.

---

## G2. OAuth connect flow (no credentials pasted)

### Orchestrator — extend `tools_router.py`
- `POST /tools/{slug}/connect` →
  1. Call Composio to **initiate a connection** for the app, with a redirect/
     callback URL. Composio returns a hosted OAuth URL + a pending `connection_id`.
  2. Persist `{connection_id, connected: false}` into `tool_integrations.config`
     via `ToolManager.save(pool, slug, enabled=False, config=...)`.
  3. Return `{ "redirect_url": "..." }`.
- `GET /tools/{slug}/connection` → poll Composio for status; when active, set
  `enabled = TRUE`, `config.connected = TRUE`, `record_sync()`; return state.
- (Optional) `POST /api/v1/integrations/oauth/callback` if using a server-side
  redirect; for desktop, polling after opening the URL is simpler.

### Frontend — `components/settings/index.tsx`
- For Composio-backed tools, **replace the credential form** with a single
  **Connect** button that calls `POST /tools/{slug}/connect` then opens
  `redirect_url` via the Tauri `open_url` command (already used in
  `RoadmapTimeline`/`PlanSectionView`).
- After opening, poll `GET /tools/{slug}/connection` until `connected`, then show
  a *Connected* badge + a Disconnect action.
- `api.ts`: `connectTool(slug)`, `getToolConnection(slug)`.
- i18n: `tool_connect`, `tool_connecting`, `tool_connected`, `tool_disconnect`.

---

## G3. Inbound triggers — "change in Slack/Notion → Moufida knows"

### Register triggers on connect
- When a connection becomes active, register the relevant Composio **triggers**
  for that app (e.g. `NOTION_PAGE_UPDATED`, `SLACK_NEW_MESSAGE`,
  `GOOGLESHEETS_ROW_ADDED`), pointing their webhook at Moufida.

### Webhook endpoint — `app/integrations_router.py` (new)
- `POST /api/v1/integrations/webhook`:
  1. **Verify** the Composio signature (shared secret / signing header) — reject
     unsigned/invalid payloads.
  2. Map the trigger to `(tool_slug, signal_type)` and resolve the affected
     `project_id` (from the connection → project mapping; for the single-user
     desktop case, the active project).
  3. Insert a `tool_signals` row `(project_id, tool_slug, signal_type, payload,
     processed=false)` — the table already exists (`009`).
  4. Enqueue processing (below) and return `200` quickly.

### Signal processing → re-run affected axes
- Add the missing **signal→axis routing** as `TOOL_AXES` in `axis_registry.py`
  (mirrors `METRIC_ROUTES`), e.g.:
  ```python
  TOOL_AXES = {
      "notion":          ["ideation", "product"],   # spec/doc changes
      "slack":           ["operations"],             # team/ops signals
      "google_sheets":   ["business-model", "market"],
      "google_analytics":["market", "marketing"],
      "github":          ["product", "operations"],
  }
  ```
- A processor (new `app/signals.py` or extend `redis_consumer.py`) drains
  unprocessed `tool_signals`:
  1. Optionally apply a `ProfilePatch` (reuse `ToolManager.enrich_profile`
     semantics — blank-only fields, evidence-tier upgrades).
  2. Compute re-run set via `dependency.affected_axes(set(TOOL_AXES[slug]))`.
  3. In diagnosis mode → recompute those axis scores; in creation mode → produce
     review **proposals** (never silent overwrites — Phase C convention).
  4. Log an `events` row (source = `tool`) and `sse.push_event(project_id,
     "event_new", {...})` so the Event Feed shows it with a field-level diff.
  5. Mark the `tool_signals` row `processed = TRUE`.

> This finally makes `tool_signals` a live part of the pipeline and reuses the
> existing Event Feed / dependency machinery rather than inventing a new path.

---

## G4. Outbound via Composio actions

- Route the push hooks (`on_diagnostic_complete`, `on_score_alert`) for
  OAuth-managed tools through Composio **actions** instead of per-tool SDKs,
  while keeping the same `ToolManager.dispatch_diagnostic` / `dispatch_alert`
  fan-out (no change to the diagnostic router call sites).
- Keep the hand-rolled tools as a fallback for users who prefer manual tokens;
  the manager already iterates all enabled tools regardless of implementation.

---

## 4. Data, events, and routing summary

| Item | Where | New/Existing |
|------|-------|--------------|
| `tool_integrations.config` ← `{connection_id, connected}` | DB | existing table, new keys |
| `tool_signals` rows (inbound) | DB | **existing table, now consumed** |
| `TOOL_AXES` signal→axis routing | `axis_registry.py` | **new** |
| `/tools/{slug}/connect`, `/connection` | `tools_router.py` | new endpoints |
| `/api/v1/integrations/webhook` | `integrations_router.py` | new |
| `event_new` SSE (source=`tool`) | `sse.py` / consumer | existing event type |

---

## 5. Risks & notes

- **Hosted dependency / free-tier caps.** Composio is a third party; the OAuth
  popup needs connectivity. This is the one place the "100% local" principle is
  relaxed by design (the brief explicitly asked for a managed broker). The local
  diagnostic/scoring/RAG pipeline stays local; only the integration edge is
  remote. Document this trade-off in the README.
- **Webhook reachability.** A desktop app behind NAT can't receive inbound
  webhooks directly. Options: (a) use Composio's hosted trigger + a lightweight
  poll (`GET` recent trigger events on a daemon cadence) instead of an inbound
  webhook; (b) expose the orchestrator via a tunnel in dev. Prefer **polling**
  for the desktop case — add a `composio` poll to the Go daemon (every ~5 min)
  that pulls new trigger events and POSTs them to `/integrations/webhook`
  locally. This keeps everything working without public ingress.
- **Secret handling.** `COMPOSIO_API_KEY` lives in `.env` (OS-encrypted at rest
  on the single-user desktop, per the `004` migration note). Never log it.
- **Signature verification is mandatory** on the webhook before writing
  `tool_signals` — untrusted input otherwise drives axis re-runs.
- **Idempotency.** Dedupe inbound triggers by Composio event id to avoid
  double re-runs (unique constraint or a seen-set in `tool_signals.payload`).

---

## 6. Checklist

- [ ] `composio` SDK in orchestrator image; `COMPOSIO_API_KEY` in `.env`/compose
- [ ] `toolkit/tools/composio/tool.py` (+ per-app subclasses) on the `ToolIntegration` contract
- [ ] `tools_router.py`: `/connect` + `/connection` (managed OAuth, no pasted creds)
- [ ] Settings UI: Connect button + status polling + Disconnect; i18n at parity
- [ ] `integrations_router.py` webhook: verify signature → write `tool_signals`
- [ ] `TOOL_AXES` in `axis_registry.py` + signal processor reusing `affected_axes`
- [ ] inbound trigger → `events` row + `event_new` SSE (Event Feed shows the diff)
- [ ] daemon Composio **poll** fallback for NAT'd desktops
- [ ] outbound `on_diagnostic_complete`/`on_score_alert` via Composio actions
