# Phase 2 — Conversational diagnostic engine

## 1. Overview

Phase 2 turns the deterministic scoring engine from Phase 1 (`scoring-engine/`,
the `affinitree` package) into a live, conversational diagnostic product. It adds
the orchestrator brain that talks to a user, runs an adaptive intake
questionnaire, fans a `StartupProfile` out to the ten axis micro-services in three
dependency-ordered waves, aggregates their outputs into a single diagnostic
snapshot (maturity stage, perception gap, prioritised blockers, composite scores),
persists that snapshot to PostgreSQL, and streams live events to the desktop UI
over Server-Sent Events. It also delivers the first LLM-backed axis (Axis 01 —
Ideation maturity classifier) and the Tier 1 evaluation skeleton. Phase 2 is the
bridge between Phase 1 (which only *scores* a structured profile) and Phase 3
(which will consume the aggregated diagnostic + scores to generate a RAG-grounded
roadmap): the aggregator output and the `score_snapshots` / `diagnostic_history`
rows are exactly the inputs Phase 3's roadmap builder reads.

## 2. What was built

### `orchestrator/app/graph/state.py` (new)
Defines `MoufidaState`, the single dict threaded through the conversation graph.
It carries everything a session needs: project id, mode (NEW vs EXISTING), the
profile, conversation history, intake answers, the current diagnostic wave, each
axis's output, the maturity verdict, blockers, anomalies, scores, breakdowns, the
roadmap, and a pending SSE queue. **Design decision:** it is a plain
`TypedDict(total=False)` of JSON-friendly values (the profile is a `dict`, not the
typed `StartupProfile`) so the whole state stays serialisable for LangGraph
checkpointing and SSE replay; the strongly-typed model stays in `scoring-engine`.

### `orchestrator/app/state_router.py` (new)
Owns the project lifecycle. `POST /project/new` inserts a profile row,
`POST /project/{id}/diagnose` flips it into STATE_EXISTING, and `GET /project/{id}`
returns a full `MoufidaState` snapshot. **Design decisions:** uses `asyncpg`
directly with a lazily-created, cached connection pool (no ORM, per the project's
"thin data layer" rule); maps between the DB vocabulary (`state` = `NEW`/`EXISTING`,
constrained by a CHECK) and the graph vocabulary (`mode` = `STATE_NEW`/
`STATE_EXISTING`) so neither layer leaks the other's terms.

### `orchestrator/app/intake/branches.json` + `intake/questionnaire.py` (new)
A data-driven, branch-aware intake questionnaire. `branches.json` is the editable
question graph (sector → conditional certifications, revenue → conditional MRR,
etc.); `AdaptiveQuestionnaire` loads it and exposes `start`, `next`, `resume`, and
`merge_to_profile`. **Design decisions:** the flow is **fully stateless** — the
client replays the accumulated `answers` map every turn and the server walks the
branch graph to find the next unanswered node, so there is no server-side session
to lose or scale; questions are bilingual (FR/AR) and `merge_to_profile` folds
answers into a nested profile patch via dotted field paths.

### `orchestrator/app/intake_router.py` (new)
Thin FastAPI router exposing the stateless questionnaire as `POST /intake/start`
and `POST /intake/answer`. Returns either the next question or, when the branch
walk is exhausted, `{done: true, profile_patch: {...}}`.

### `orchestrator/app/diagnostic/runner.py` (new)
Runs the STATE_EXISTING diagnostic pass: an `httpx.AsyncClient` (60 s timeout —
wave 0 contains the LLM maturity axis, whose cold-model generation can take
30 s+) fans the profile out to the axis services in the three waves from
`axis_registry.DIAGNOSTIC_WAVES`. **Design decisions:** waves 0 and 2 use
`asyncio.gather` for true concurrency (the axes within a wave are independent, so
parallel I/O collapses ~5 sequential HTTP round-trips into one); wave 1 (brand)
runs *after* wave 0 because it consumes ideation/market/product outputs, passed as
`prior_outputs`; a failing or unreachable axis is captured as an `{"error": ...}`
stub instead of aborting the whole pass, so a partial diagnostic still aggregates.

### `orchestrator/app/diagnostic/aggregator.py` (new)
Pure function that folds the per-axis responses into one snapshot: maturity vs.
self-assessed stage and the `perception_gap` boolean, blockers tagged with their
source axis and a severity (keywords `runway`/`gdpr`/`ai act`/`no customer` →
`critical`, else `warning`) then sorted critical→warning→info, the five composite
scores and their explanation trees keyed by `score_name`, and the union of
anomalies. **Design decision:** kept side-effect-free (no DB, no HTTP) so it is
trivially unit-testable and reusable by Phase 3.

### `orchestrator/app/diagnostic_router.py` (new)
Exposes `POST /project/{id}/run-diagnostic`: loads the profile, calls the runner
and aggregator, persists one `diagnostic_history` row plus one `score_snapshots`
row per score inside a single transaction, fires `score_update` + `maturity_update`
SSE events, and returns the full aggregated result.

### `orchestrator/app/sse.py` (new)
In-memory, per-project SSE broker. `push_event(project_id, event, payload)`
broadcasts to every subscriber; `event_stream` yields `data: {json}\n\n` frames.
**Design decisions:** the registry lives here (not in `main.py`) to avoid an import
cycle, since the diagnostic router needs `push_event` while `main` imports the
routers; process-local fan-out is sufficient for the single-instance desktop
deployment, with Redis pub/sub deferred to Phase 5 for multi-replica.

### `orchestrator/app/lang_detect.py` (new)
`detect_language(text)` classifies messages as `fr` / `ar-TN` / `other` and
`translate_derja_to_french` translates Tunisian Derja via a 5-shot Llama 3.1
prompt. **Design decisions:** uses the lightweight `langdetect` package (no model
download, fast, offline) seeded for deterministic output; maps langdetect's generic
`ar` to `ar-TN` because Moufida treats all inbound Arabic as Tunisian dialect for
now; falls back to `fr` on detection failure (the product's default UI language).

### `orchestrator/app/main.py` (changed)
Mounts the four routers under `/api/v1`, adds the `GET /project/{id}/events` SSE
endpoint, re-exports `push_event`, and adds `POST /chat` — a grounded chat endpoint
that detects the message language, loads the latest diagnostic + scores from the
DB, and calls Mistral 7B with a system prompt that forbids generic advice and
restricts answers to the project's own diagnostic data.

### `orchestrator/app/axis_registry.py` (changed)
Added the `DIAGNOSTIC_WAVES` constant (the runner's source of truth);
`diagnostic_order()` now returns it.

### `services/ideation-service/app/main.py` (changed)
Implements Axis 01's real `/diagnose`: builds a maturity-classification prompt and
calls Mistral 7B via Ollama with `httpx.AsyncClient`, parsing the JSON response
safely with a deterministic fallback. **Design decision:** `/diagnose` accepts
three body shapes — the orchestrator's `{"profile": ...}` wrapper, a bare
`StartupProfile`, and an eval payload with free-text `meta.description` — so the
runner, manual calls, and the Tier 1 harness all work against one endpoint.
`/metric_update` logs milestone signals and returns `{"status": "received"}`.

### `eval/tier1-maturity/vignettes.json` + `run_eval.py` + `requirements.txt` (new)
15 labelled, Tunisia-specific startup vignettes (the format/skeleton for the 50-case
set) and a runner that scores Axis 01's predictions with macro-F1 and an
approximated top-2 accuracy, plus optional inter-annotator Cohen's κ.

### Infrastructure (changed)
`orchestrator/Dockerfile` (fixed the renamed `scoring-engine` copy path — the old
`COPY affinitree` was a build-breaker — and added `asyncpg`/`langdetect`/
`langgraph`), `docker-compose.yml`, `.env.example` (working defaults), and
`scripts/phase2-smoke-test.sh`. Compose decisions: **Ollama runs on the host by
default** (services reach it via `host.docker.internal`); the bundled
`ollama/ollama` container is opt-in behind `--profile bundled-ollama` so the stack
does not force a multi-GB image pull on machines that already run Ollama. The
Postgres host port is remappable (`${POSTGRES_HOST_PORT:-5433}:5432`) to avoid
clashing with a host-native Postgres; `OLLAMA_BASE_URL` and `OLLAMA_MODEL` were
added to the shared axis env.

## 3. API surface

| Method | Path | Service | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/project/new` | orchestrator | Create a profile row (STATE_NEW); returns `{project_id, mode}` |
| POST | `/api/v1/project/{project_id}/diagnose` | orchestrator | Flip project into STATE_EXISTING |
| GET | `/api/v1/project/{project_id}` | orchestrator | Return current `MoufidaState` snapshot |
| POST | `/api/v1/intake/start` | orchestrator | First intake question (translated) |
| POST | `/api/v1/intake/answer` | orchestrator | Next question, or `{done, profile_patch}` |
| POST | `/api/v1/project/{project_id}/run-diagnostic` | orchestrator | Run the 3-wave diagnostic, persist, emit SSE, return aggregate |
| GET | `/api/v1/project/{project_id}/events` | orchestrator | SSE stream (`score_update`, `alert`, `roadmap_update`, `review_ready`, `maturity_update`) |
| POST | `/api/v1/chat` | orchestrator | Grounded chat over the project's diagnostic; returns `{reply, detected_lang}` |
| POST | `/diagnose` | ideation-service (8101) | Maturity classification via Mistral 7B |
| POST | `/metric_update` | ideation-service (8101) | Receive a daemon milestone signal |
| POST | `/execute` | ideation-service (8101) | STATE_NEW guided step (stub, unchanged) |

## 4. Data flow — STATE_EXISTING diagnostic pass

```
  ┌──────────┐   voice    ┌─────────┐  text   ┌─────────────────────────────┐
  │  User    │ ─────────▶ │   STT   │ ──────▶ │       Orchestrator          │
  │ (desktop)│            │ Whisper │         │  POST /chat  or             │
  └──────────┘            └─────────┘         │  POST /project/{id}/run-... │
        ▲                                     └───────────────┬─────────────┘
        │                                                     │ load profile (asyncpg)
        │                                                     ▼
        │                              ┌──────────────────────────────────────────┐
        │                              │  WAVE 0  (asyncio.gather — parallel)       │
        │                              │   ideation(8101)  market(8102)  product(8103)
        │                              └───────────────┬──────────────────────────┘
        │                                              │ outputs feed forward
        │                                              ▼
        │                              ┌──────────────────────────────────────────┐
        │                              │  WAVE 1   brand(8104)                      │
        │                              │   body = {profile, prior_outputs:{ideation,│
        │                              │            market, product}}               │
        │                              └───────────────┬──────────────────────────┘
        │                                              ▼
        │                              ┌──────────────────────────────────────────┐
        │                              │  WAVE 2  (asyncio.gather — parallel)       │
        │                              │  business-model(8105) legal(8106)          │
        │                              │  operations(8109) marketing(8107) sales(8108)
        │                              └───────────────┬──────────────────────────┘
        │                                              ▼
        │                                   ┌─────────────────────┐
        │                                   │     aggregator      │  maturity_stage,
        │                                   │  (pure function)    │  perception_gap,
        │                                   └──────────┬──────────┘  blockers, scores
        │                                              ▼
        │                          ┌───────────────────────────────────┐
        │                          │  PostgreSQL (asyncpg, 1 txn)       │
        │                          │  diagnostic_history + score_snapshots
        │                          └──────────────────┬────────────────┘
        │                                             ▼
        │             score_update × N        ┌───────────────┐
        └──────────── maturity_update ◀────── │  SSE broker   │ ── data: {json}\n\n ──▶ frontend
                       (dashboard)            └───────────────┘                         dashboard
```

## 5. Evaluation status

| Tier | Test | Status after Phase 2 | Notes |
|------|------|----------------------|-------|
| Tier 2 | `--determinism` (structured profiles scored 10×) | ✅ passing (Phase 1) | No LLM; untouched by Phase 2 |
| Tier 2 | `--anomaly` (10 contradiction profiles, 100% recall) | ✅ passing (Phase 1) | No LLM; untouched by Phase 2 |
| Tier 2 | `--text-stability` (rubric σ ≤ 0.15) | ⏸ wired, unmeasured | Needs Ollama + `mistral:7b` pulled |
| Tier 1 | `vignettes.json` (15-case skeleton) | 🆕 enabled by Phase 2 | Format established; 35 partner cases pending |
| Tier 1 | `run_eval.py` macro-F1 / top-2 | 🆕 enabled, unmeasured | Needs Axis 01 + Ollama running |
| Unit | `lang_detect` (fr / ar-TN / other / empty→fr) | 🆕 verified ad hoc | Dedicated unit-test file deferred |
| E2E | `scripts/phase2-smoke-test.sh` | ✅ verified PASS | Full stack up; real llama3.1:8b classification, scores persisted to Postgres |

## 6. Known limitations & deferred items

- **LLM model is operator-provided** — the stack expects an Ollama (host or
  bundled) with a chat model pulled. `OLLAMA_MODEL` selects it (`.env` ships
  `llama3.1:8b`, which the smoke test exercised; set `mistral:7b` once pulled).
  All callers degrade gracefully — Axis 01 returns an `Ideation`/0.0 fallback if
  the model is unreachable. The first call loads the model into memory and can
  exceed the runner's per-axis budget, so the smoke test warms it first.
- **Intake answers are not persisted into the project** — `/intake/answer` returns a
  `profile_patch`, but there is no endpoint that merges it into the project row yet,
  so `run-diagnostic` scores whatever profile was set at `/project/new`. *(Owner:
  Phase 3 — a `PATCH /project/{id}/profile` merge step.)*
- **Real Derja translation untested** — `translate_derja_to_french` is implemented
  and exported but not yet wired into `/chat`, and the 5-shot prompt is unvalidated
  against real Derja. *(Owner: Phase 4 voice/NLU.)*
- **Voice pipeline (STT/TTS) is host-side and stubbed** — Whisper/Piper/Kokoro assets
  and the SSE consumer in the Tauri app land in Phase 4.
- **RAG / roadmap are stubs** — `rag/` exposes `/health` + stubbed ingest/retrieve;
  the `roadmap` field on `MoufidaState` and `roadmap_versions` table are unused until
  Phase 3.
- **SSE broker is in-memory** — fine for the single-instance desktop deployment;
  multi-replica needs Redis pub/sub. *(Owner: Phase 5.)*
- **Body-shape standardisation** — axis `/diagnose` endpoints settled on the
  `{"profile": ...}` wrapper; Axis 01 accepts that plus bare/eval shapes for
  compatibility. Remaining axes assume the wrapper.

## 7. How to run Phase 2

Prerequisites: Docker + Docker Compose. An LLM runtime is needed for real Axis 01
classification — either a **host Ollama** (default) or the bundled container.

```bash
# 1. Configure environment (defaults are wired for the compose network).
cp .env.example .env

# 2a. Using a HOST Ollama (default). Ensure it is reachable from containers:
#     run it bound to all interfaces and pull a chat model.
OLLAMA_HOST=0.0.0.0 ollama serve          # (if not already running)
ollama pull llama3.1:8b                    # matches OLLAMA_MODEL in .env
# 2b. ...or use the bundled container instead:
#     docker compose --profile bundled-ollama up -d ollama
#     then set OLLAMA_URL/OLLAMA_BASE_URL=http://ollama:11434 and
#     `docker compose exec ollama ollama pull llama3.1:8b`

# 3. Build and start the full backend stack.
docker compose up -d

# 4. Run the Phase 2 end-to-end smoke test.
bash scripts/phase2-smoke-test.sh
```

The Postgres host port defaults to **5433** (override with `POSTGRES_HOST_PORT`)
to avoid clashing with a host-native Postgres; in-compose services always reach it
as `postgres:5432`.

The smoke test waits for `/health` on ports 8001, 8101–8106, 8109, 8300, creates a
project, drives the adaptive intake (agri-food / Market Validation / 5 interviews /
team of 3 / SARL), runs the diagnostic, and asserts the aggregated response has a
non-null `maturity_stage`, all five composite scores, a `blockers` list, and a
`perception_gap` field. It prints the full response and `PASS`/`FAIL`.

To run the Tier 1 maturity eval against the live Axis 01 service:

```bash
pip install -r eval/tier1-maturity/requirements.txt
python eval/tier1-maturity/run_eval.py --kappa
```

To run the exact commands again:

```bash
docker compose up -d
bash scripts/phase2-smoke-test.sh
```
