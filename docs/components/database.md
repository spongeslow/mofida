# Database Schema

**Engine:** PostgreSQL 16 | **Migrations:** 20 SQL files in `db/migrations/`, auto-applied at startup by `db-migrate`

All migrations are idempotent (`CREATE TABLE IF NOT EXISTS`). A `_schema_migrations` table tracks applied files. Run manually with `./scripts/migrate.sh`.

---

## Core Tables

| Table | Purpose |
|---|---|
| `profiles` | One row per startup project; `profile` JSONB holds the full `StartupProfile` including evidence tiers and rubric scores |
| `diagnostic_history` | Append-only diagnostic runs; maturity stage, self-assessed stage, perception gap, confidence, evidence, blockers, anomalies |
| `score_snapshots` | Append-only per-axis scores; breakdown, justification, DD flags, `locked` flag (set after score debate) |
| `roadmap_versions` | Versioned roadmaps with `kb_version` provenance (hash of KB state at generation time) |
| `plan_sections` | Creation-mode approved axis content; `superseded=true` on old versions |

## Tool & Signal Tables

| Table | Purpose |
|---|---|
| `tool_integrations` | Per-project tool enable/config/last_sync/last_error |
| `tool_signals` | Inbound Composio triggers with `processed` flag; drained on orchestrator startup |

## Intelligence Tables

| Table | Purpose |
|---|---|
| `events` | Event feed: source (chat/daemon/tool/manual), severity, axes_affected, status (pending/acted/manual/ignored), diff JSONB |
| `competitors` | Competitor snapshots with SWOT and diff_html |
| `opportunities` | Funding call matches with match_score, deadline, apply_url |
| `project_watch_targets` | LLM-derived daemon targets cached by (project_id, profile_hash) |
| `concept_scores` | CBM concept activations + bottleneck per axis per diagnostic run |
| `pitch_sessions` | Full transcript + readiness report per investor simulator session |
| `customer_personas` | Generated personas with KB citations |
| `knowledge_base` | Per-project uploaded documents (source=upload) and their Qdrant point IDs |

## Infrastructure Tables

| Table | Purpose |
|---|---|
| `daemon_control` | **Single-row** (`id=TRUE`): paused, focus_project_id (`ON DELETE SET NULL`), last_beat |
| `dependency_graph` | Mirror of `dependency.py` graph seeded at orchestrator startup |

## Telemetry Tables (Migration 020)

Three append-only tables written by `TelemetryMiddleware`:

| Table | Key columns |
|---|---|
| `api_requests` | request_id, method, path, status, duration_ms, project_id |
| `llm_calls` | request_id (FK), axis, model, prompt_hash (SHA-256), prompt_preview (280 chars), duration_ms, input_tokens, output_tokens |
| `daemon_activities` | watcher, activity, detail JSONB |

The `request_id` ContextVar propagated through every `generate_json()` call creates a distributed trace from HTTP request to LLM call — surfaced in the admin panel's request-trace view.

---

## Key Design Decisions

**`score_snapshots.locked`** — set `TRUE` after a score debate update. Subsequent diagnostics skip locked scores, preserving the human override against regression.

**`daemon_control.focus_project_id ON DELETE SET NULL`** — if a focused project is deleted, the daemon gracefully parks itself without crashing.

**`roadmap_versions.kb_version`** — SHA-256 of KB state at generation time. Every roadmap action is traceable to the exact knowledge base version that produced it.

**Prompt hashing in `llm_calls`** — only the first 280 characters and a SHA-256 hash of the full prompt are stored, protecting potentially sensitive founder data while preserving debugging utility.
