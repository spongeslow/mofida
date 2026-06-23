# 11 — Phase F: Real 24/7 Daemon + 2D-Character Lifetime

> **Workstream:** turn the always-on Go daemon from a shallow alert emitter into
> a genuinely useful 24/7 background analyst, and wire its lifetime to the 2D
> companion character (stop icon = pause watching). Builds on the existing
> daemon (`daemon/`), Redis→SSE fan-out (`redis_consumer.py` → `sse.py`), and the
> Tauri companion window (`frontend/companion.html`, `components/companion/`).
>
> **Primary surfaces:** `daemon/`, `backend/orchestrator/app/`, `db/migrations/`,
> `frontend/src/components/`, `frontend/src-tauri/`.
> **Depends on:** Phase E (RAG evidence) is independent; F can start any time.
> **Source of truth for behaviour:** the master plan + `new-logic.md §5`.

---

## 1. Current state (verified against the repo)

**Daemon (`daemon/`)**
- `cmd/main.go` starts watchers as goroutines on fixed cadences; `MOUFIDA_PROJECT_ID`
  is optional (project watchers are skipped on nil UUID).
- `internal/watchers/`: `competitor.go` (MD5 page-diff + RSS keyword scan),
  `legal.go`, `budget.go`, `milestone.go`, `trend.go`, plus `kbstaleness`.
- `internal/watchers/base.go`: `tickLoop(ctx, name, interval, tick)`, `fetchPage`,
  `fetchProfile`, RSS/Atom `parseFeed`, JSON state-file helpers.
- `internal/watchers/derive.go`: pure profile→target mappers (`sectorNewsFeeds`,
  `sectorLegalSources`, `deriveLegalKeywords`, trend keywords) already key off
  `profile["sector"]` — so watchers are *partly* project-aware today.
- `internal/redis/publisher.go`: `Publish(ctx, projectID, metricType, value any)`
  publishes to the Redis metrics channel.
- Signals flow: daemon → Redis → orchestrator `redis_consumer.py` → axis
  `/metric_update` (routed by `axis_registry.METRIC_ROUTES`) → SSE alert.

**Limitations**
- Competitor watcher only detects *that* a page changed — no extracted data, no
  persistence, no analysis, no UI beyond a toast.
- No competitor/opportunity tables; nothing is rendered as a board.
- Daemon lifetime == container lifetime; no pause/resume; no link to the character.
- **Project is pinned at startup**: `cmd/main.go` reads `MOUFIDA_PROJECT_ID` from
  the env **once** and builds the project-scoped watchers from it. Switching the
  watched project means editing `.env` and restarting the container — there is no
  way to point the daemon at a project from the app.
- **Adaptation is coarse and static**: `derive.go` switches on a 4-value `sector`
  enum (`agri-food` / `digital-tech` / `industry` / `cross-sector`). Two
  agri-food projects get identical feeds/sources; the offer/innovation/market
  free-text in the profile is barely used to specialise targets.
- Companion (`components/companion/index.tsx`, `MoufidaCharacter`) reacts only to
  `voiceState` + critical `alerts`. There is a `set_companion_visible` Tauri
  command but no daemon control.

---

## 2. Target state

1. A **control plane**: the daemon polls a pause flag and emits a heartbeat; the
   orchestrator exposes endpoints + broadcasts `daemon_status` over SSE.
2. The **2D character is the switch**: a stop/play control on the companion
   toggles watching; the character animates `watching` ↔ `sleeping` from live
   daemon status.
3. **Competitor analysis board**: persisted competitors, LLM-extracted
   pricing/positioning, change diffs, SWOT, rendered as a comparison board.
4. **Grant/deadline radar**: a watcher matches Tunisian funding sources to the
   project and surfaces opportunity cards with apply-by dates.
5. **Market/trend digest**: existing trend/legal/milestone/budget signals are
   persisted and surfaced as a scored "what changed" digest in the existing feed.
6. **App-selected focus (no env project ID)**: the watched project is chosen from
   the project list in the UI ("Focus" button), carried in the same control-plane
   row, and the daemon **hot-swaps** its project-scoped watchers at runtime — no
   restart, no `MOUFIDA_PROJECT_ID`. (Env stays only as a dev fallback / seed.)
7. **Genuinely adaptive watchers**: each watcher derives its targets from the
   focused project's *full* profile (sector **and** offer/innovation/market
   text), so an agri-food project watches agri-food sources, competitors, and
   regulators specifically — not a coarse one-of-four bucket.

---

## F1. Daemon control + heartbeat + project focus (character = switch)

### Migration `013_daemon_control.sql`
```sql
-- Single-row control plane for the background daemon. id is pinned to TRUE so
-- there is always exactly one row (upsert on conflict).
CREATE TABLE IF NOT EXISTS daemon_control (
    id          BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (id),
    paused      BOOLEAN NOT NULL DEFAULT FALSE,
    focus_project_id UUID REFERENCES profiles(id) ON DELETE SET NULL, -- which project the daemon watches; chosen from the UI
    last_beat   TIMESTAMPTZ,                 -- updated by the daemon heartbeat
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO daemon_control (id, paused) VALUES (TRUE, FALSE)
    ON CONFLICT (id) DO NOTHING;
```

> `focus_project_id` is the single source of truth for *which* project the daemon
> watches, replacing the startup-only `MOUFIDA_PROJECT_ID`. `ON DELETE SET NULL`
> means deleting a project from the picker cleanly parks the daemon. On a fresh
> DB the value is `NULL` (daemon idle on project work) until the user picks one;
> a non-empty `MOUFIDA_PROJECT_ID` may be used once to seed it on first boot.

### Orchestrator — `app/daemon_router.py` (new), mounted under `/api/v1`
- `GET  /daemon/control` → `{ "paused": bool, "alive": bool, "last_beat": iso,
  "focus_project_id": uuid|null }`. `alive` = `now() - last_beat < 90s`. The
  daemon polls this for both the pause flag **and** which project to focus on.
- `POST /daemon/control` body `{ "paused"?: bool, "focus_project_id"?: uuid|null }`
  → partial upsert (only the provided fields), then
  `await sse.push_event("*", "daemon_status", {paused, alive, focus_project_id})`
  (broadcast). Validate `focus_project_id` exists in `profiles` (404 otherwise).
- `POST /daemon/heartbeat` → `UPDATE daemon_control SET last_beat = now()`; also
  pushes `daemon_status` so the UI sees liveness transitions promptly.

> Reuse `sse.push_event(project_id, event, payload)`; add a broadcast helper in
> `sse.py` that fans an event to every connected project channel (the companion
> window isn't project-scoped). Register the router in `app/main.py` next to the
> other `include_router` calls.

### Daemon changes
- `internal/control/control.go` (new): one call `Fetch(ctx, orchestratorURL)
  (Control, error)` where `Control{ Paused bool; FocusProjectID string }` GETs
  `/api/v1/daemon/control`; `Heartbeat(ctx, orchestratorURL)` POSTs
  `/api/v1/daemon/heartbeat`. Best-effort (network errors → treat as not paused,
  keep current focus).
- `internal/watchers/base.go` `tickLoop`: before each `tick`, check the cached
  pause flag; if paused, skip the work body but still loop. Always `Heartbeat`
  each iteration.

**Project hot-swap (replaces startup `MOUFIDA_PROJECT_ID` wiring):**
- `cmd/main.go` runs a **supervisor loop** (the heartbeat ticker, ~30s) that:
  1. `Heartbeat` + `Fetch` the control row.
  2. Caches `paused` for `tickLoop` to read.
  3. If `FocusProjectID` **changed** from the currently-running set: cancel the
     child `context` for the old project-scoped watchers (let goroutines drain),
     then, if the new ID is non-nil, start a fresh batch
     (`NewBudget/NewCompetitor/NewLegal/NewMilestone/NewTrend` + Phase F
     `grant.go`) bound to the new ID under a new child context. `kbstaleness`
     stays running across swaps (it is project-independent).
- This makes the project a **runtime input**, not a build/boot input.
  `MOUFIDA_PROJECT_ID` becomes an optional first-boot seed: if the control row's
  `focus_project_id` is NULL and the env is set, POST it once to `/daemon/control`.
- Watcher state files are keyed per project (e.g.
  `competitor_hashes.<project_id>.json`) so swapping focus doesn't cross-contaminate
  change-detection hashes.

### Frontend
- `frontend/src/sse/consumer.ts`: handle `daemon_status` → store
  `daemonPaused` / `daemonAlive` (add to `store.ts`).
- `frontend/src/components/companion/`: add a small play/stop affordance on the
  companion (e.g. a corner button or the existing dblclick) that calls
  `POST /daemon/control`. Extend `MoufidaCharacter` `CharacterState` with
  `"watching"` and `"sleeping"`; map from store: paused → `sleeping`, alive &&
  !paused → `watching` (falls back to existing voice/alert states when active).
- `frontend/src/api.ts`: `getDaemonControl()`, `setDaemonPaused(paused)`,
  `setDaemonFocus(projectId)` (POST `/daemon/control` with `focus_project_id`).
- **Focus button in the project list** — `App.tsx` `RecentProjectsPicker`: next to
  the existing per-project open/delete controls (the `projects.map(...)` row), add
  a "Focus" / 👁 button that calls `setDaemonFocus(p.project_id)`. Read
  `focus_project_id` from the store (set by the `daemon_status` consumer) to mark
  the currently-watched project (badge / filled icon) and make its button a
  no-op/"unfocus". This is how the user tells the daemon which project to watch —
  no env, no restart.
- `frontend/src/sse/consumer.ts`: extend the `daemon_status` handler to also store
  `daemonFocusProjectId`.
- i18n: `daemon_watching`, `daemon_paused`, `daemon_resume`, `daemon_pause`,
  `daemon_offline`, `daemon_focus`, `daemon_focused`, `daemon_unfocus`
  in `fr/en/ar.json`.

### Checklist
- [ ] `013_daemon_control.sql` with `focus_project_id` (idempotent; picked up by `db-migrate`)
- [ ] `daemon_router.py` (paused **+ focus_project_id**) + broadcast helper in `sse.py` + register in `main.py`
- [ ] `control.go` (`Fetch`/`Heartbeat`), `tickLoop` pause check, supervisor loop with project hot-swap in `main.go`
- [ ] per-project state-file keys; `MOUFIDA_PROJECT_ID` demoted to first-boot seed
- [ ] store fields (incl. `daemonFocusProjectId`) + `daemon_status` consumer + character states + companion control
- [ ] Focus button in `RecentProjectsPicker` (`setDaemonFocus`) with watched-project marker
- [ ] i18n keys at parity

---

## F2. Competitor analysis board

### Migration `014_competitors.sql`
```sql
CREATE TABLE IF NOT EXISTS competitors (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    url         TEXT,
    pricing     JSONB NOT NULL DEFAULT '{}'::jsonb,   -- {tiers:[{name,price,features}]}
    positioning TEXT,                                  -- LLM one-line positioning
    funding     JSONB NOT NULL DEFAULT '{}'::jsonb,    -- {stage,amount,investors}
    news        JSONB NOT NULL DEFAULT '[]'::jsonb,    -- [{headline,url,date}]
    swot        JSONB NOT NULL DEFAULT '{}'::jsonb,    -- {strengths,weaknesses,opportunities,threats}
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, name)
);
CREATE TABLE IF NOT EXISTS competitor_snapshots (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    captured_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw_excerpt   TEXT,                                -- trimmed page text
    diff          JSONB NOT NULL DEFAULT '{}'::jsonb   -- {field: {before, after}}
);
CREATE INDEX IF NOT EXISTS idx_competitors_project ON competitors(project_id);
```

### Daemon — extend `internal/watchers/competitor.go`
- Keep the MD5 change-detection. When a tracked competitor page **changes**,
  fetch + trim the page text (strip tags, cap ~6 KB) and POST it to the
  orchestrator rather than only publishing a one-line alert:
  ```
  POST /api/v1/project/{id}/competitor/observe
  { "name": "...", "url": "...", "raw_text": "...", "source": "page_changed" }
  ```
- The RSS `news_mention` path posts `source:"news_mention"` with the headline.
- This is a direct HTTP POST (reuse `fetchPage` patterns / `net/http`), not a
  Redis metric, because it carries a large payload and targets a new endpoint.

### Orchestrator — `app/competitor_router.py` (new)
- `POST /project/{id}/competitor/observe`:
  1. Upsert the `competitors` row (by `project_id`+`name`).
  2. LLM-extract structured data from `raw_text` (Ollama, `format:"json"`):
     pricing tiers, one-line positioning, any funding mention. Reuse the
     evidence/JSON-parse helpers pattern from axis services.
  3. Diff the new extraction vs the latest `competitor_snapshots` row; write a
     new snapshot with the `diff`.
  4. Regenerate `swot` via the LLM using the project profile + competitor data.
  5. Persist; `await sse.push_event(project_id, "competitor_update", {name, diff})`.
- `GET /project/{id}/competitors` → list rows for the board (also include the
  project's own positioning row synthesised from `plan_sections` market/product).

### Frontend — `components/dashboard/CompetitorBoard.tsx` (new)
- Comparison table: **You vs each competitor** across pricing, positioning,
  funding (columns = competitors, rows = dimensions).
- A change timeline from `competitor_snapshots` diffs (reuse `DiffView.tsx`).
- SWOT cards per competitor.
- Mount in `components/dashboard/index.tsx`; live-update on `competitor_update`
  SSE (consumer bumps a nonce → component refetches `GET /competitors`).
- i18n: `competitor_board_title`, `competitor_pricing`, `competitor_positioning`,
  `competitor_funding`, `competitor_swot_*`, `competitor_change`.

### Checklist
- [ ] `014_competitors.sql`
- [ ] competitor.go posts extracted page text to `/competitor/observe`
- [ ] competitor_router.py: extract + diff + SWOT + persist + SSE
- [ ] CompetitorBoard.tsx + dashboard mount + SSE refresh + i18n

---

## F3. Grant / deadline radar

### Migration `015_opportunities.sql`
```sql
CREATE TABLE IF NOT EXISTS opportunities (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id   UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    source       TEXT NOT NULL,               -- 'startup_act' | 'apii' | 'eu_calls' | ...
    url          TEXT,
    deadline     DATE,                         -- apply-by date (LLM-extracted)
    match_reason TEXT,                         -- why it fits this project
    match_score  REAL NOT NULL DEFAULT 0,      -- 0..1 profile fit
    dismissed    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, url)
);
CREATE INDEX IF NOT EXISTS idx_opportunities_active
    ON opportunities(project_id) WHERE dismissed = FALSE;
```

### Daemon — `internal/watchers/grant.go` (new)
- A curated list of Tunisian funding sources (Startup Act, APII, EU4Innovation,
  Horizon Europe calls) as RSS/HTML endpoints + the KB `financing` resources.
- On tick: fetch each source, parse entries (reuse `parseFeed`), and for each
  candidate POST to:
  ```
  POST /api/v1/project/{id}/opportunity/observe
  { "title": "...", "source": "...", "url": "...", "raw_text": "..." }
  ```
- Cadence ~24h; dedupe by URL in the state file.

### Orchestrator — endpoints in `app/opportunity_router.py` (new)
- `POST /project/{id}/opportunity/observe`: LLM match-scores the candidate
  against the project profile (stage/sector) and extracts the apply-by date;
  if `match_score ≥ 0.5`, upsert into `opportunities` and
  `sse.push_event(project_id, "opportunity_new", {title, deadline})`.
- `GET  /project/{id}/opportunities` → active (non-dismissed) rows, deadline asc.
- `POST /project/{id}/opportunity/{oid}/dismiss`.

### Frontend — `components/dashboard/OpportunityRadar.tsx` (new)
- Cards sorted by deadline; urgency colour when `deadline` is within 14 days;
  apply link (Tauri `open_url`); dismiss button.
- Mount in dashboard; refresh on `opportunity_new` SSE.
- i18n: `opportunity_radar_title`, `opportunity_deadline`, `opportunity_apply`,
  `opportunity_dismiss`, `opportunity_match`.

### Checklist
- [ ] `015_opportunities.sql`
- [ ] grant.go watcher + curated source list
- [ ] opportunity_router.py: match-score + deadline extract + persist + SSE
- [ ] OpportunityRadar.tsx + dashboard mount + i18n

---

## F4. Market / trend signal digest

- Reuse `trend.go`, `legal.go`, `milestone.go`, `budget.go` unchanged in their
  detection; **persist** their signals via the existing `tool_signals`/events
  path so they survive and can be scored.
- Add a scored "what changed" digest surfaced through the **existing**
  `WhatsNew` / `EventFeed` components (extend, do not replace). The digest groups
  recent signals by axis and ranks by severity.
- No new tables required if signals are written as `events` rows (Phase C
  `008_events.sql`); add a `digest`-style read query in `history_router` or the
  existing whats-new endpoint.

### Checklist
- [ ] persist daemon signals as events (not just transient SSE)
- [ ] digest read query + surface in WhatsNew/EventFeed
- [ ] i18n for digest grouping labels

---

## F5. Genuinely project-adaptive watchers

> Today `derive.go` adapts only on a 4-value `sector` enum, so every agri-food
> project watches the same handful of feeds. The goal: each watcher's targets are
> derived from the **focused project's full profile** — sector *plus* the
> offer / innovation / market / competitor free-text already returned by
> `fetchProfile`. An agri-food cold-chain project and an agri-food agri-tech SaaS
> should not watch identical sources.

### Where adaptation lives
- Keep all derivation **pure** in `internal/watchers/derive.go` (no I/O) so it
  stays testable; watchers call it with the profile dict from `fetchProfile`.
- The focused project comes from the control plane (F1), so "adaptive to the
  project it's working on" == "derive from the profile of `focus_project_id`".

### Migration `016_project_watch_targets.sql`
```sql
-- Per-project, LLM-derived watch targets so adaptation survives restarts and
-- doesn't re-hit the LLM every tick. Refreshed when the profile changes.
CREATE TABLE IF NOT EXISTS project_watch_targets (
    project_id   UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    feeds        JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{url, why}]
    legal_sources JSONB NOT NULL DEFAULT '[]'::jsonb, -- [{name, url}]
    keywords     JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [str]
    competitors  JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{name, url}]
    derived_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    profile_hash TEXT                                 -- skip re-derive when unchanged
);
```

### Two-tier derivation strategy
1. **Deterministic (no LLM)** — extend `derive.go`:
   - Keep the sector base lists, but **layer in** terms mined from the profile
     free-text: `deriveKeywords(profile)` already exists for trend; generalise it
     so `sectorNewsFeeds` / `sectorLegalSources` are *seeds*, and the watch
     keyword/competitor set is the union of (sector seed ∪ profile-mined terms).
   - Pull competitor names/URLs from `profile["market"]["competitors"]` (the
     competitor watcher already reads this) and feed them to trend/legal scans too.
   - Result: same project ⇒ same targets, fully offline; the always-on floor that
     the LLM tier enriches and that the daemon falls back to if the DB is empty.
2. **LLM-enriched (cached)** — the niche-specific tier; this is what makes an
   agri-food cold-chain project watch different sources than an agri-food SaaS.

### LLM tier — orchestrator `app/watch_targets_router.py` (new)
- `POST /project/{id}/watch-targets/refresh`:
  1. Load the profile; compute `profile_hash` (stable hash of the fields fed to
     the prompt — sector + offer/innovation/market/competitor text). If a
     `project_watch_targets` row exists with the same `profile_hash`, return it
     unchanged (no LLM call).
  2. Else prompt Ollama with `{"stream": false, "format": "json"}` (reuse the axis
     pattern in `backend/services/market-intelligence-service/app/main.py`: the
     `format:"json"` POST + the `_json.loads(raw)` → substring-fallback parser).
     Ask for **niche-specific** RSS/news feeds, regulators/standards bodies, and
     search keywords/competitor names tailored to *this* project, each with a short
     `why`. Constrain to a JSON schema matching the table columns; cap list sizes.
  3. Optionally ground candidate feeds/competitors with the existing
     `backend/rag/app/websearch.py` before persisting (validate URLs resolve).
  4. Upsert the `project_watch_targets` row (by `project_id`) with the new
     `profile_hash` + `derived_at`; broadcast `watch_targets_updated`
     `{project_id}` over SSE so the daemon (and any UI) can react promptly.
- `GET  /project/{id}/watch-targets` → the merged view the daemon consumes:
  deterministic `derive.go`-equivalent seeds **unioned with** the stored LLM
  targets (dedupe by URL/keyword). Returns the deterministic floor alone if no
  row exists yet, so the endpoint is always safe to call.
- Register the router in `app/main.py` next to the other `include_router` calls.
- Reuse `OLLAMA_TIMEOUT`; keep `temperature` low (targets should be stable).

### Daemon wiring
- `fetchWatchTargets(ctx, orchestratorURL, projectID)` (best-effort) in `base.go`
  GETs `/project/{id}/watch-targets`; each watcher merges the result with its
  `derive.go` seeds. If the call fails or returns empty, fall back to the pure
  `derive.go` output (no regression).
- Cache the fetched targets in the watcher and refresh on a slow cadence (e.g.
  alongside the existing tick) so a steady-state daemon isn't chatty.
- The supervisor (F1) triggers a refresh on two events: when it **focuses** a
  project (hot-swap) — POST `/watch-targets/refresh` for the new project before
  starting its watchers — and when a `profile_patch`/`watch_targets_updated`
  signal indicates the profile changed.

### Checklist
- [ ] generalise `derive.go` to union sector seeds with profile-mined keywords/competitors
- [ ] `016_project_watch_targets.sql`
- [ ] `watch_targets_router.py`: `refresh` (LLM + `profile_hash` cache + websearch grounding) and merged `GET`; register in `main.py`
- [ ] `watch_targets_updated` SSE event + consumer
- [ ] `fetchWatchTargets` merge in watchers with safe fallback to `derive.go`
- [ ] supervisor refresh-on-focus + refresh-on-profile-change triggers

---

## 3. SSE events introduced by Phase F

| Event | Payload | Consumer |
|-------|---------|----------|
| `daemon_status` | `{paused, alive, last_beat, focus_project_id}` | companion character + store + project picker marker |
| `competitor_update` | `{name, diff}` | CompetitorBoard refresh |
| `opportunity_new` | `{title, deadline}` | OpportunityRadar refresh |
| `watch_targets_updated` | `{project_id}` | daemon re-fetches `GET /watch-targets` |

Add each to `frontend/src/sse/consumer.ts` and the SSE event-type union.

---

## 4. Risks & notes

- **Broadcast SSE:** `daemon_status` isn't project-scoped. Add a broadcast helper
  rather than abusing a project channel; the companion window subscribes to it.
- **LLM cost on the daemon path:** competitor extraction/SWOT and opportunity
  matching call Ollama. Keep cadences conservative (6–24h) and cap payload sizes;
  reuse `OLLAMA_TIMEOUT`.
- **Pause semantics:** pausing stops *work*, not the process; heartbeats continue
  so the UI can distinguish "paused" from "offline".
- **Focus hot-swap:** changing `focus_project_id` cancels the old project's
  watcher goroutines via a child context and starts a new batch — never run two
  project batches at once, and let the old ones drain before reporting the switch.
  Key state files per project so a swap doesn't reset the other project's hashes.
- **Adaptation cost vs. freshness:** derive targets deterministically by default;
  gate any LLM enrichment behind `profile_hash` caching so re-derivation happens
  on focus/profile-change, not every tick (reuse `OLLAMA_TIMEOUT`).
- **Scraping politeness:** keep the `moufida-daemon/1.0` UA, honour failures
  quietly, and never hammer a source faster than its cadence.
- **Demo cut-line:** F1 (character switch) + F2 (competitor board) are the
  headline demo; F3/F4 can follow.
