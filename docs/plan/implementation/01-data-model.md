# 01 — Data Model & Migrations

> Implements new-logic.md §8. Adds the persistence needed for plan sections,
> events, tool signals, the versioned KB, and the dependency graph mirror.

Migrations are **additive**, numbered `006`+, in `db/migrations/`. Apply in
order. Existing tables (`profiles`, `diagnostic_history`, `alerts`,
`score_snapshots`, `roadmap_versions`, `tool_integrations`,
`roadmap_action_status`) are unchanged except where noted.

---

## 1. Decision: `profiles` IS the project (no new `projects` table)

The design doc lists a `projects` table, but `profiles` already is the project
row and is wired through intake/diagnostic. We **extend** it instead:

`006_project_meta.sql`
```sql
-- Map design-doc `mode` onto the existing NEW/EXISTING state, and add fields
-- the multi-project dashboard needs.
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS mode TEXT
    GENERATED ALWAYS AS (CASE state WHEN 'NEW' THEN 'creation' ELSE 'diagnosis' END) STORED;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS archived  BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS plan_complete BOOLEAN NOT NULL DEFAULT false;
```
`mode` is a generated column so the design-doc vocabulary works in queries
without a second source of truth. `state` remains the writable column.

> If the team prefers a literal `projects` table, it must back the existing
> `state_router` queries and intake — that is a larger refactor with no demo
> benefit. Recommended: keep `profiles`.

---

## 2. `plan_sections` — versioned per-axis plan content (§8)

The output of creation mode and the substrate for continuous updates.

`007_plan_sections.sql`
```sql
CREATE TABLE IF NOT EXISTS plan_sections (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    axis_slug   TEXT NOT NULL,          -- ideation, market, ... , roadmap
    version     INT  NOT NULL DEFAULT 1,
    content     JSONB NOT NULL,         -- structured proposal (axis-specific shape)
    summary     TEXT,                   -- one-line for the document view
    approved    BOOLEAN NOT NULL DEFAULT false,
    superseded  BOOLEAN NOT NULL DEFAULT false,  -- older versions flipped true
    source      TEXT NOT NULL DEFAULT 'generate'
        CHECK (source IN ('generate','manual','chat','tool','daemon')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- One "live" (latest, non-superseded) row per axis is the current plan.
CREATE UNIQUE INDEX IF NOT EXISTS uq_plan_live
    ON plan_sections(project_id, axis_slug) WHERE superseded = false;
CREATE INDEX IF NOT EXISTS idx_plan_project ON plan_sections(project_id, axis_slug, version DESC);
```
**Write rule:** producing a new version flips the prior live row
`superseded=true`, inserts the new row, `version = prev+1`. The live plan is the
set of `superseded=false` rows. History/diff reads all versions for an axis.

`content` shape is axis-specific and defined in `02-axis-dual-mode.md §3`.

---

## 3. `events` — every update from any source (§5.6)

`008_events.sql`
```sql
CREATE TABLE IF NOT EXISTS events (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    source        TEXT NOT NULL CHECK (source IN ('manual','chat','tool','daemon')),
    type          TEXT NOT NULL,        -- e.g. 'section_edit','signal','regulation'
    severity      TEXT NOT NULL DEFAULT 'info'
        CHECK (severity IN ('critical','warning','info')),
    summary       TEXT NOT NULL,        -- human-readable headline
    detail        TEXT,                 -- longer body (daemon event text, etc.)
    axes_affected TEXT[] NOT NULL DEFAULT '{}',
    diff          JSONB,                -- {axis: {before, after}} for View-diff
    suggestion    JSONB,                -- Moufida's proposed action (Act/Manual)
    status        TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new','acted','manual','ignored')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_events_project ON events(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_status  ON events(project_id, status);
```
The Event Feed (`06`), "What's new?" query, and the daemon Act/Manual/Ignore
card all read/write here. `alerts` stays as the raw daemon log; an `event` is
the *interpreted, actionable* record (one alert may yield one event).

---

## 4. `tool_signals` — raw structured data from integrations (§5.3, §8)

`009_tool_signals.sql`
```sql
CREATE TABLE IF NOT EXISTS tool_signals (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    tool_slug   TEXT NOT NULL,          -- github, google_analytics (pull tools; real toolkit slugs)
    signal_type TEXT NOT NULL,          -- revenue_change, new_deal, milestone...
    payload     JSONB NOT NULL,
    processed   BOOLEAN NOT NULL DEFAULT false,  -- interpreted into an event yet?
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_tool_signals_unproc
    ON tool_signals(project_id) WHERE processed = false;
```
The signal→axis routing (which tool affects which axes) lives in code
(`06-continuous-updates.md §3`), mirroring the doc's table.

---

## 5. `knowledge_base` — versioned RAG content (§6.1, §8)

`010_knowledge_base.sql`
```sql
CREATE TABLE IF NOT EXISTS knowledge_base (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID REFERENCES profiles(id) ON DELETE CASCADE,  -- NULL = global KB
    source      TEXT NOT NULL,          -- seed, tool, upload, manual, feed
    title       TEXT,
    content     TEXT NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,  -- url, sector, anonymised...
    kb_version  INT NOT NULL DEFAULT 1, -- monotonically bumped on KB change
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_kb_scope ON knowledge_base(project_id, kb_version DESC);
```
Postgres holds the *catalogue + versioning*; the embedding vectors live in
**Qdrant** keyed by `knowledge_base.id`. Each roadmap generation records the
`kb_version` it used (see §6 below). Detail in `07-roadmap-engine.md §3`.

---

## 6. Roadmap generation provenance

`roadmap_versions` already exists (migration 003). Extend it to record the KB
version and the trigger:

`011_roadmap_provenance.sql`
```sql
ALTER TABLE roadmap_versions ADD COLUMN IF NOT EXISTS kb_version INT;
ALTER TABLE roadmap_versions ADD COLUMN IF NOT EXISTS trigger TEXT;  -- on_demand, update, completion, score_drop
ALTER TABLE roadmap_versions ADD COLUMN IF NOT EXISTS stale BOOLEAN NOT NULL DEFAULT false;
```
"Roadmap flagged stale" (§6.4) sets `stale=true` on the live row; regeneration
inserts a fresh version and clears it.

---

## 7. `dependency_graph` mirror (optional, traceability) (§8)

The graph is authoritative **in code** (`05-dependency-engine.md`). This table
is a queryable/versioned mirror for the UI's "why did this re-run?" view.

`012_dependency_graph.sql`
```sql
CREATE TABLE IF NOT EXISTS dependency_graph (
    axis       TEXT NOT NULL,
    depends_on TEXT[] NOT NULL,
    version    INT NOT NULL DEFAULT 1,
    PRIMARY KEY (axis, version)
);
```
Seed it from the code graph on startup (idempotent upsert). If the team is time
constrained, **skip this table** — it is purely a mirror.

---

## 8. Checklist

- [ ] `006_project_meta.sql` — `mode` generated col, `archived`, `plan_complete`
- [ ] `007_plan_sections.sql` + live-row uniqueness rule documented in code
- [ ] `008_events.sql`
- [ ] `009_tool_signals.sql`
- [ ] `010_knowledge_base.sql` (+ Qdrant collection for KB vectors)
- [ ] `011_roadmap_provenance.sql`
- [ ] `012_dependency_graph.sql` (optional mirror)
- [ ] Apply all in the dev DB; update `scripts/` seed/reset if present
- [ ] Add asyncpg accessors in orchestrator (`state_router` pool is reused)
