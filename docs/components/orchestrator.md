# Orchestrator

**Location:** `backend/orchestrator/` | **Port:** 8001  
**Stack:** Python 3.12, FastAPI, LangGraph, asyncpg, httpx, redis-py, pydantic v2

The orchestrator is the central brain. Every action — running a diagnosis, generating a plan, chatting, sending a pitch — goes through this single FastAPI service. It owns 18 sub-routers, a background Redis consumer, and a telemetry middleware that correlates every HTTP request with every downstream LLM call.

---

## API Routers

### Project lifecycle (`state_router`)
- `POST /project/new` — creates a project (`state=NEW|EXISTING`, `sector`, `language`)
- `PATCH /project/{id}/profile` — updates any profile fields; triggers no re-run by itself
- `GET /projects` — lists all projects
- `DELETE /project/{id}` — cascades all associated data

### Adaptive Intake (`intake_router`) — Stateless CAT/IRT engine
- `POST /intake/next` — client replays the full answer history on every call; server re-derives θ̂ (maturity ability estimate) via Bayesian EAP, selects the next maximum-Fisher-information item, and returns `complete` when SE(θ̂) < 0.40 or ≥ 12 items answered. No server-side session. See [adaptive-testing.md](../research/adaptive-testing.md) for the IRT math.

### Creation mode (`creation_router`)
- `POST /generate/{axis}` — fetches KB evidence + live web search, calls axis `/generate`, returns a cited proposal (not persisted)
- `POST /generate/{axis}/approve` — persists to `plan_sections`
- `POST /generate/{axis}/retry` — regenerates with higher temperature + optional constraints
- `GET /plan` — full plan document
- `POST /finalize` — after all 9 axes approved: generates roadmap from approved sections + KB

### Diagnostic mode (`diagnostic_router`)
- `POST /project/{id}/diagnostic` — 3-wave parallel axis fan-out, CBM scoring, anomaly detection, maturity staging, persists `diagnostic_history` + `score_snapshots` + `concept_scores`, SSE-streams results
- `POST /project/{id}/documents` — PDF/markdown upload → pypdf extraction → Qdrant ingest
- `POST /project/{id}/axis/{axis}/debate` — score debate: LLM judge evaluates the founder's argument; if convinced, updates the score and locks the row (`locked=true`)

### Roadmap engine (`roadmap_router`)
- `POST /project/{id}/roadmap/regenerate` — re-generates with latest KB; bumps `kb_version`
- `POST /project/{id}/roadmap/advance` — generates next horizon after all current actions are complete
- `GET /project/{id}/roadmap/provenance` — returns KB version, trigger source, source document IDs

### Investor Pitch Simulator (`pitch_router`)
- `POST /project/{id}/pitch/start` — persona types: `seed_vc | angel | impact_fund | strategic`; questions grounded **only** in the project's actual diagnostic evidence (scores, blockers, competitors, opportunities)
- `POST /project/{id}/pitch/{session_id}/message` — one exchange turn
- `POST /project/{id}/pitch/{session_id}/end` — closes session, produces `PitchReadinessReport` (per-axis readiness, hardest questions, prep actions)

### Customer Persona Simulator (`persona_router`)
- `POST /project/{id}/personas/generate` — 3 evidence-grounded Tunisian personas (archetype, region, budget, objections, buying triggers)
- `POST /project/{id}/personas/{persona_id}/chat` — in-character chat

### Pivot Scenario Planner (`scenario_router`)
- `POST /project/{id}/scenarios/simulate` — profile field overrides → parallel RAG-grounded axis projections with confidence + citations
- `POST /project/{id}/scenarios/{scenario_id}/adopt` — patches profile + triggers re-diagnostic

### Concept Bottleneck Model (`cbm/router`)
- `POST /project/{id}/cbm` — LLM scores all concepts per axis in parallel (`asyncio.gather`), then calls `signal:8010/cbm/score` for the linear bottleneck; persists to `concept_scores`; SSE `concept_update`

### Competitor + Opportunity (`competitor_router`, `opportunity_router`)
- Receive structured observations from the Go daemon, run LLM extraction/scoring, persist + push SSE

### Watch targets (`watch_targets_router`)
- `POST /project/{id}/watch-targets/refresh` — LLM-derives niche-specific feeds/keywords from the full profile; cached by profile hash

### Events + History + Chat
- `GET /project/{id}/events/stream` — SSE (dedicated path, not the REST list); 13 event types
- `POST /event/{id}/act|manual|ignore`, `GET /event/{id}/diff`
- `GET /whats-new` — LLM digest of recent activity
- `GET /history/compare` — diffs any two diagnostic runs
- `POST /chat` — grounded on latest diagnostic; LLM intent detection triggers `apply_update()` when the message asserts a real change

### Daemon control plane (`daemon_router`)
- `GET /daemon/control`, `POST /daemon/pause|resume`, `POST /daemon/focus/{project_id}`

### Admin API (`/api/admin/`)
- Health probes, paginated request log, LLM call log, daemon activity log, live log SSE stream. Optional `ADMIN_TOKEN` gating.

---

## Shared Modules

**`axis_registry.py`** — single source of truth for axis slugs, ports, compose hostnames, score ownership, `DIAGNOSTIC_WAVES`, `METRIC_ROUTES` (daemon signal type → axis slug), `TOOL_AXES` (Composio trigger → axes to re-run).

**`dependency.py`** — directed dependency graph with transitive re-run resolution. The `business-model ↔ operations` cycle (the only SCC) is handled explicitly — both re-run simultaneously.

**`sse.py`** — per-project in-memory `asyncio.Queue` per SSE subscriber.

**`redis_consumer.py`** — background asyncio task subscribed to the daemon's Redis channel. Routes metric events to axis `metric_update` endpoints; calls `interpret_daemon_event()` for `significant_change` signals.

**`telemetry_middleware.py`** — wraps every HTTP request: records to `api_requests`, seeds `request_id` + `project_id` ContextVars so all downstream `generate_json()` calls correlate in `llm_calls`.

**`evidence_snapshot.py`** — `gather_evidence()`: builds the rich evidence snapshot used by pitch/persona/scenario (scores, maturity, weak points, competitors, opportunities, concept bottlenecks).

---

## Notable Design Decisions

**Stateless CAT** — the intake questionnaire has zero server-side session state; the client replays full history on every call. This makes the intake horizontally scalable by design.

**Score debate with locking** — after a debate updates a score, the row is locked (`locked=true`). Subsequent diagnostics do not overwrite locked scores, preserving the human's override.

**Best-effort signal integration** — if `moufida-signal` is down, all 10 axis diagnostics still complete. CBM cards are simply absent from the UI. No hard dependency.

**Dependency-aware re-runs** — a market signal only re-runs market and its dependents, not all 10 axes. Cost scales with the change, not the total system.
