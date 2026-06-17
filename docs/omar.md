# Moufida — Current Implementation State & Next Steps

**Team Makrouna Kadheba** | June 2026

---

## What Has Been Built

Phases 0 and 1 of the implementation plan are complete. The foundation — the entire backend scaffold and the deterministic scoring engine — exists and works. Below is a precise account of what each component currently does.

---

### Scoring Engine (`scoring-engine/`)

This is the most complete component. It is a standalone Python package (`affinitree`) that can be installed and tested independently of everything else.

**What it does:**

- Defines the full `StartupProfile` Pydantic model (all fields from Table 1 in the spec): six domain blocks — `market`, `offer`, `innovation`, `finance`, `ops`, `legal` — each typed as Boolean, Numeric, Enum, or free-text.
- Implements the **three-tier evidence model**: every field can be marked T1 (declared, ×0.6), T2 (artefact-backed, ×1.0), or T3 (daemon-observed, ×1.2). The multiplier `mi` is applied per field during scoring.
- Computes all **five composite scores** using the formula `ci = wi × vi × mi`:
  - **Market Score** (4 sub-dimensions: addressable market size, customer validation, revenue model clarity, competitive intensity)
  - **Commercial Offer Score** (4 sub-dimensions: value proposition clarity, product maturity, pricing coherence, differentiation)
  - **Innovation Score** (4 sub-dimensions exactly matching Listing 2 in the spec: product/tech novelty at 35%, market novelty at 25%, brand distinctiveness at 20%, value-creation novelty at 20%)
  - **Scalability Score** (6 sub-dimensions spanning both financial — unit economics, funding readiness, revenue model — and operational — automation, supply-chain resilience, quality framework)
  - **Green Score** (5 sub-dimensions: GDPR compliance, AI Act compliance, IP protection, SDG alignment, environmental impact)
- Each JSON config (`config/*.json`) stores sub-dimension weights, the formula string, and a literature citation (OECD Oslo Manual, Kotler, Blank, Porter, etc.).
- A **safe formula evaluator** (`formula.py`) parses and evaluates only a whitelisted arithmetic subset — no `eval()` — so config formulas run safely.
- **Rubric scoring** (`rubric.py`): wraps any LLM client via an injectable protocol. Runs the rubric prompt twice; triggers a third run and takes the median when two scores diverge by more than 1. Five rubrics are defined (value proposition, differentiation, novelty, brand distinctiveness, SDG alignment), each with 0–4 integer scales and explicit level descriptors.
- **Anomaly detection** (`anomaly.py`): 10 rule-based contradiction checks (e.g., revenue without customer interviews, LTV < CAC, AI Act applicable but not compliant, runway < 3 months).

**Test coverage:**

- 24 pytest unit tests covering: scores stay in range [0, 5], determinism over 10 runs, config weights sum to 1.0, evidence tiers raise scores, Innovation config matches Listing 2 weights exactly, rubric median-on-divergence logic, empty-text short-circuit.
- Tier 2a (determinism): **100%** — 3 structured profiles × 5 scores × 10 runs, all identical.
- Tier 2c (anomaly recall): **100%** — all 10 contradiction profiles fire their expected anomaly code.

**What it does NOT do yet:**

- The rubric scorer requires a live Ollama backend (Tier 2b stability test). It's wired but not measurable until Ollama is running.
- No natural-language justification step (translating the score breakdown into a plain-language sentence). That is a thin LLM call added when the axis services call this library in Phase 2.

---

### 10 Specialised Services (`services/`)

Each service is a FastAPI microservice with its own `Dockerfile` and `pyproject.toml`.

| Service | Port | Diagnose endpoint | Score computed |
|---|---|---|---|
| `ideation-service` | 8101 | Stub — returns `not_implemented` | Maturity stage (Phase 2) |
| `market-intelligence-service` | 8102 | **Live** — calls scoring engine | Market Score |
| `product-offering-service` | 8103 | **Live** — calls scoring engine | Commercial Offer Score |
| `brand-innovation-service` | 8104 | **Live** — calls scoring engine | Innovation Score |
| `business-model-service` | 8105 | **Live** — calls scoring engine | Scalability Score |
| `legal-compliance-service` | 8106 | **Live** — calls scoring engine | Green Score |
| `marketing-service` | 8107 | Stub | Marketing readiness (Phase 2) |
| `sales-service` | 8108 | Stub | Sales readiness (Phase 2) |
| `operations-service` | 8109 | **Live** — calls scoring engine | Scalability Score (ops half) |
| `go-to-market-service` | 8110 | Stub | Roadmap (Phase 3) |

Every service exposes:
- `GET /health` → `{"status": "ok", "axis": N, "slug": "..."}`
- `POST /execute` → stub (Phase 4, STATE_NEW guided flow)
- `POST /diagnose` → live for scoring services, stub otherwise
- `POST /metric_update` → stub (Phase 5, Go daemon signals) — present on ideation, market, business-model, legal, operations, gtm

The five live `diagnose` endpoints return: `score` (0–5), full `explanation` tree (per-component: name, weight, normalised value, evidence tier, multiplier, contribution, formula, derived variables, citation), `missing_fields`, and `anomalies`.

---

### Orchestrator (`orchestrator/`)

FastAPI service on port 8001. Currently exposes:

- `GET /health`
- `GET /topology` — returns the full axis map and the three-wave diagnostic dependency order: `[["ideation","market","product"], ["brand"], ["business-model","legal","operations","marketing","sales"]]`
- `GET /state/{project_id}` — stub

The `axis_registry.py` module is the single source of truth for:
- All compose-internal service hostnames and ports
- Which score each service owns
- The Go-daemon metric type → service routing table (`competitor→market`, `budget→business-model`, `legal→legal-compliance`, `milestone→ideation+gtm`, `trend→market`)
- The diagnostic dependency-wave order

Everything that will be built in Phases 2 and 5 (state router, adaptive intake, LangGraph graph, Redis consumer, diagnostic runner) reads from this registry.

---

### RAG Service (`rag/`)

FastAPI service on port 8300. Stub-only at this stage:

- `GET /health`
- `POST /retrieve` → empty results
- `POST /ingest` → not implemented
- `POST /admin/resource` → not implemented

The `knowledge-base/taxonomy.json` defines the full Stage × Type × Sector matrix the retrieval pipeline will filter against. The `knowledge-base/resources/` directory is empty — curating 80–100 Tunisian resources is a Phase 3 task.

---

### Go Monitoring Daemon (`daemon/`)

Standard-library-only Go binary (no external dependencies yet, so it builds cleanly without a `go.sum`). On startup it launches six goroutines on their real cadences:

| Goroutine | Cadence | Current behavior |
|---|---|---|
| Budget watcher | Every 6 hours | Logs heartbeat |
| Competitor watcher | Every 12 hours | Logs heartbeat |
| Legal radar | Daily | Logs heartbeat |
| Milestone checker | Daily | Logs heartbeat |
| Trend scanner | Weekly | Logs heartbeat |
| KB staleness checker | Daily | Logs heartbeat |

The `redis/publisher.go` logs the JSON message it would emit rather than connecting to Redis. The actual scraping, threshold checks, and Redis publish calls land in Phase 5.

---

### PostgreSQL Database (`db/migrations/`)

Three migrations run automatically on first `docker compose up`:

- `001_init.sql` — `profiles` (JSONB profile + state NEW/EXISTING), `diagnostic_history` (maturity stage, self-assessed stage, perception gap, evidence, blockers, anomalies), `alerts` (type, severity, payload)
- `002_score_snapshots.sql` — `score_snapshots` (score name, value, full breakdown JSONB, timestamp)
- `003_roadmap_versions.sql` — `roadmap_versions` (roadmap JSON, trigger, version number)

---

### Frontend (`frontend/`)

Tauri 2 (Rust) + React 18 + TypeScript. Runs on the host, not in Docker.

**What exists:**
- System tray icon with context menu: "Nouveau projet", "Diagnostiquer un projet existant", "Paramètres", "Quitter" — all four menu items compile and the Quit handler works; the others are `TODO Phase 4`.
- Minimal `App.tsx`: renders the app title, tagline, and a language-toggle button (French ↔ Arabic, with RTL layout flip via `dir="rtl"`).
- Full i18n structure: `locales/fr.json` and `locales/ar.json` with keys for all UI strings defined so far.
- All 13 component and utility files exist as Phase 4 stubs: `ChatPanel`, `ReviewCard`, `AlertFeed`, `MaturityCard`, `ScoreGauge`, `BlockerList`, `RoadmapTimeline`, `ScoreChart`, `HistoryList`, `wakeword.ts`, `stt.ts`, `tts.ts`, `consumer.ts`.

**What does not exist yet:** any actual UI logic, API calls, voice integration, or SSE consumption.

---

### Infrastructure

- `docker-compose.yml` — validated; boots PostgreSQL, Redis, Qdrant, Ollama, orchestrator, 10 services, RAG service, and Go daemon. Health checks on Postgres and Redis gate dependent services.
- `.env.example` — all required variables with empty defaults (fill before running).
- `scripts/download-models.sh` — pulls Mistral 7B, Llama 3.1, nomic-embed-text via Ollama API; lists voice model checkpoints that must be placed manually.
- `scripts/ingest-kb.sh` — calls `POST /ingest` on the RAG service.
- `scripts/run-all-evals.sh` — runs Tier 2 (always), skips Tier 1 and 3 with a message until those phases deliver their runners.

---

## What Is NOT Built Yet (Phases 2–6)

### Phase 2 — Adaptive Intake & Diagnostic Engine

This is the next phase to implement. Everything in this list currently returns `not_implemented`.

**Orchestrator additions needed:**
- `lang_detect.py` — fastText language identification (ar-TN / fr / other)
- `intake/branches.json` — branching rules: agri-food certifications, revenue > 0 follow-up questions, legal form questions, self-assessed stage capture
- `intake/questionnaire.py` — stateful branching engine that walks `branches.json` and populates `StartupProfile` fields
- `state_router.py` — reads `profiles` table, dispatches to STATE_NEW or STATE_EXISTING LangGraph graph
- `graph/state.py` and `graph/nodes.py` — LangGraph state machine with nodes for intake, diagnostic pass, aggregation, roadmap call, human review
- `diagnostic/runner.py` — calls `POST /diagnose` on services in the three-wave dependency order defined in `axis_registry.py`
- `diagnostic/aggregator.py` — computes perception gap (self-assessed vs. ideation-service stage), merges blocker lists, ranks by severity, triggers go-to-market-service roadmap call
- `redis_consumer.py` — subscribes to `moufida:metrics`, routes messages to service `metric_update` endpoints using the routing table in `axis_registry.py`

**Ideation service additions needed:**
- Maturity classifier in `diagnose` endpoint: Mistral 7B prompt → one of six stages (Ideation, Market Validation, Structuration, Fundraising, Launch Planning, Growth) + confidence + 3–5 evidence points, written to `diagnostic_history`
- `metric_update` endpoint logic: conditional stage upgrade on milestone signals

**Marketing and sales services:**
- `diagnose` endpoints returning readiness scores (secondary inputs to Market Score and Scalability Score)

**Tier 1 evaluation:**
- `eval/tier1-maturity/vignettes.json` — 50 labelled startup vignettes (3 annotators, Cohen's κ ≥ 0.65 target)
- `eval/tier1-maturity/run_eval.py` — macro-F1 ≥ 0.65, top-2 accuracy ≥ 0.85

---

### Phase 3 — Knowledge Base & RAG Service

**Knowledge base curation:**
- Collect and verify 80–100 Tunisian support resources covering: APII, BFPME, BTS, Startup Act, ANPE, incubators, EU funds, UNDP, legal guides, administrative procedures
- Each resource must follow the Listing 1 metadata schema: id, title, type, stage[], sector[], score_dimensions[], url, language, last_verified, provider
- Coverage floor: ≥ 2 resources per Stage × Type cell (6 stages × 5 types × 2 = 60 minimum), plus sector-specific additions for agri-food, digital/tech, industry

**RAG service (`rag/app/`):**
- `ingest.py` — split documents into paragraph chunks, embed with nomic-embed-text via Ollama, store in Qdrant with metadata
- `retrieve.py` — three-step pipeline: (1) pre-filter by stage ∩ diagnosed stage and score_dimensions ∩ low-score dimensions; (2) hybrid dense (cosine) + sparse (BM25) retrieval merged with RRF; (3) sector boost ×1.3 for matching sector
- `admin.py` — authenticated endpoint to add a resource or flag one `needs_review`

**Go-to-market service:**
- `roadmap.py` — for each gap/low sub-score, formulates a query, calls RAG `/retrieve` with stage and dimension filters, uses Llama 3.1 to organise retrieved resources into immediate/short-term/medium-term action plan, stores in `roadmap_versions`
- `metric_update` endpoint logic: regenerate roadmap on milestone completion or new KB resource

**Tier 3 evaluation:**
- `eval/tier3-rag/query_pairs.json` — 20 (query, expected-resource-id) pairs across all six stages and five resource types
- `eval/tier3-rag/run_eval.py` — Recall@3 ≥ 0.80, MRR ≥ 0.70

---

### Phase 4 — Voice Pipeline & Frontend

**Voice pipeline (all currently empty stubs):**
- `voice/wakeword.ts` — Porcupine wake-word detection ("Hey Moufida"); IDLE → LISTENING transition
- `voice/stt.ts` — full voice state machine (IDLE → LISTENING → TRANSCRIBING → PROCESSING → SPEAKING); primary path: TuniSpeech fine-tuned Whisper large-v2; fallback to French Whisper when `avg_logprob < -0.5`; detected language forwarded to orchestrator
- `voice/tts.ts` — Piper for French output; Kokoro-82M for MSA output; selected by user language preference

**Tauri backend (currently empty handlers):**
- System tray handlers for "New Project" and "Diagnose Existing Project" (open a window, call orchestrator)
- Tray icon pulse animation when Go daemon emits a non-urgent signal
- Settings window with language selector persisted to `StartupProfile`

**Dashboard components (currently empty stubs):**
- `MaturityCard.tsx` — current stage badge, confidence %, collapsible evidence list
- `ScoreGauge.tsx` — number card per composite score; expandable to sub-score table (component name, weight, raw value, evidence tier, contribution); natural-language justification below
- `BlockerList.tsx` — ranked blockers with critical/warning/info severity badges
- `RoadmapTimeline.tsx` — three-column timeline (Immediate / Short-term / Medium-term); each card has rationale + clickable source link
- `ChatPanel.tsx` — voice transcript display + text fallback input; sends commands to orchestrator
- `ReviewCard.tsx` — Approve / Edit / Retry for human review of axis outputs
- `AlertFeed.tsx` — real-time alert stream from SSE; reads alerts via TTS on arrival

**"Mon Parcours" view (currently empty stubs):**
- `ScoreChart.tsx` — recharts line chart, one line per composite score, x-axis = timestamp
- `HistoryList.tsx` — past stage assignments with evidence, completed roadmap actions with dates

**SSE consumer (`sse/consumer.ts`):**
- `score_update` → score widgets refresh
- `alert` → AlertFeed + TTS
- `roadmap_update` → RoadmapTimeline refresh
- `review_ready` → ReviewCard display

---

### Phase 5 — Go Daemon & Liveness

The daemon goroutines exist on their correct cadences but do nothing except log. Each watcher needs its real logic:

- **Budget watcher** — read spend/limit from orchestrator API; publish at 80%, 90%, 100% thresholds
- **Competitor watcher** — scrape RSS feeds + web pages in competitor list; store response hashes; publish on change
- **Legal radar** — fetch EU AI Act and Tunisian Official Gazette feeds; keyword filter; publish on new relevant regulation
- **Milestone checker** — read project milestones from profile; publish alerts at 14/7/1/0 days before deadline
- **Trend scanner** — count keyword occurrences in TechCrunch and Wamda RSS; publish if frequency changes > 50% week-over-week
- **KB staleness checker** — fetch source URLs for resources where `last_verified` > 90 days; flag as `needs_review` via RAG admin endpoint if hash changed

The Redis publisher (`redis/publisher.go`) currently logs messages instead of connecting to Redis; a real Redis client (e.g. `go-redis`) needs to be added to `go.mod` and wired in.

The orchestrator's `redis_consumer.py` (not yet written) needs to subscribe to `moufida:metrics` and forward each message to the correct service using the routing table in `axis_registry.py`.

---

### Phase 6 — Integration, Evaluation & Submission

- End-to-end STATE_NEW walkthrough: voice wake → new project → all 10 services call → review cards → completed StartupProfile persisted
- End-to-end STATE_EXISTING walkthrough: voice wake → diagnose → adaptive intake → diagnostic pass → dashboard populated → roadmap generated → Go daemon triggers score update → SSE alert shown and spoken
- "Mon Parcours" view populated after two diagnostic runs with at least one score change
- Derja input → lang_detect → translation → rubric scoring → stored with original + translated text
- Full Tier 1, 2 (all sub-tests), and Tier 3 evaluation runs with results card

---

## File Map

```
scoring-engine/
├── affinitree/
│   ├── __init__.py          exports: Affinitree, StartupProfile, score, detect
│   ├── profile.py           StartupProfile Pydantic model + evidence tier logic
│   ├── scorer.py            weighted-sum engine, ci=wi*vi*mi, ScoreResult
│   ├── formula.py           safe AST-based arithmetic evaluator
│   ├── normalisers.py       pure normalisation functions (boolean, ordinal_map, etc.)
│   ├── rubric.py            LLM-as-judge with median-on-divergence, OllamaClient
│   ├── anomaly.py           10 contradiction-detection rules
│   └── config/
│       ├── market.json
│       ├── commercial_offer.json
│       ├── innovation.json      (matches Listing 2 exactly)
│       ├── scalability.json
│       └── green.json
└── tests/
    ├── test_scorer.py       7 parametrised tests
    └── test_rubric.py       5 tests using FakeClient

orchestrator/app/
├── main.py                  /health, /topology, /state stub
└── axis_registry.py         compose hostnames, diagnostic waves, metric routing

services/
├── ideation-service/        port 8101 — diagnose stub
├── market-intelligence-service/   port 8102 — diagnose LIVE (market score)
├── product-offering-service/      port 8103 — diagnose LIVE (commercial_offer)
├── brand-innovation-service/      port 8104 — diagnose LIVE (innovation)
├── business-model-service/        port 8105 — diagnose LIVE (scalability)
├── legal-compliance-service/      port 8106 — diagnose LIVE (green)
├── marketing-service/             port 8107 — diagnose stub
├── sales-service/                 port 8108 — diagnose stub
├── operations-service/            port 8109 — diagnose LIVE (scalability ops half)
└── go-to-market-service/          port 8110 — diagnose stub

rag/
├── app/main.py              stubs: /retrieve, /ingest, /admin/resource
└── knowledge-base/
    ├── taxonomy.json        Stage × Type × Sector coverage matrix
    └── resources/           empty — Phase 3 task

daemon/
├── cmd/main.go              launches 6 goroutines on real cadences
├── internal/watchers/       5 watchers — heartbeat only
├── internal/redis/          publisher — logs instead of connecting
└── internal/kbstaleness/    checker — heartbeat only

frontend/
├── src-tauri/src/main.rs    system tray + 4 menu items (Quit works, others TODO)
├── src/App.tsx              minimal shell + language toggle
├── src/locales/             fr.json, ar.json
├── src/components/          13 component stubs (all empty exports)
├── src/voice/               3 voice stubs
└── src/sse/                 SSE consumer stub

db/migrations/               001 (profiles/history/alerts), 002 (scores), 003 (roadmap)
eval/tier2-affinitree/       determinism + anomaly fixtures + runner (passing)
eval/tier1-maturity/         README only — vignettes.json needed in Phase 2
eval/tier3-rag/              README only — query_pairs.json needed in Phase 3
scripts/                     download-models, ingest-kb, run-all-evals
```

---

## Recommended Order of Next Work

1. **Phase 2 — Start with `ideation-service` maturity classifier** (the Tier 1 eval unlocks once this works)
2. **Phase 2 — Adaptive intake + state router + LangGraph graph** in the orchestrator (this is the heaviest engineering chunk)
3. **Phase 2 — Diagnostic runner + aggregator** wiring the three-wave call sequence
4. **Phase 3 — Knowledge base curation** (can run in parallel with Phase 2; it is primarily research and data collection)
5. **Phase 3 — RAG ingest + retrieve + Axis 10 roadmap** (depends on the KB being populated)
6. **Phase 4 — Frontend dashboard components** (depends on Phase 2 data being available to display)
7. **Phase 4 — Voice pipeline** (relatively independent; needs model checkpoints)
8. **Phase 5 — Go daemon real logic + Redis consumer** (depends on Phases 2/3 for the metric routing to be meaningful)
9. **Phase 6 — Integration test + all evals**
