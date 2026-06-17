# Moufida — Implementation Plan

**Team Makrouna Kadheba** | June 2026

---

## 1. Proposed Project Structure

```
moufidaa/
├── docker-compose.yml
├── .env.example
├── docs/
│   └── plan/
│       └── implementation-plan.md
│
├── affinitree/                        # Shared scoring library (Python package)
│   ├── pyproject.toml
│   └── affinitree/
│       ├── __init__.py
│       ├── scorer.py                  # Weighted-sum engine + evidence-tier multipliers
│       ├── rubric.py                  # LLM-as-judge rubric scoring for text fields
│       ├── anomaly.py                 # Rule-based contradiction checks
│       └── config/
│           ├── market.json
│           ├── commercial_offer.json
│           ├── innovation.json        # Listing 2 from spec
│           ├── scalability.json
│           └── green.json
│
├── orchestrator/                      # FastAPI + LangGraph  |  Port 8001
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── state_router.py            # STATE_NEW / STATE_EXISTING dispatcher
│       ├── intake/
│       │   ├── questionnaire.py       # Branching adaptive questionnaire
│       │   └── branches.json          # Branching rules (sector, revenue, etc.)
│       ├── diagnostic/
│       │   ├── runner.py              # Calls diagnose endpoints on axes
│       │   └── aggregator.py          # Perception gap, blocker ranking
│       ├── redis_consumer.py          # Listens to moufida:metrics, routes to axes
│       ├── lang_detect.py             # fastText language ID (ar-TN / fr / other)
│       └── graph/                     # LangGraph state machine
│           ├── state.py               # StartupProfile + conversation state
│           └── nodes.py               # Graph nodes per axis
│
├── axes/
│   ├── axis01-ideation/               # Port 8101
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── app/
│   │       ├── main.py
│   │       ├── execute.py             # STATE_NEW: brainstorming, SCAMPER, feasibility
│   │       ├── diagnose.py            # Maturity classifier (Mistral 7B)
│   │       └── metric_update.py       # Receives milestone signals
│   ├── axis02-market/                 # Port 8102
│   │   └── app/
│   │       ├── execute.py             # TAM/SAM/SOM, personas, competitor analysis
│   │       ├── diagnose.py            # Market Score via Affinitree
│   │       └── metric_update.py       # Competitor watcher signals
│   ├── axis03-product/                # Port 8103
│   │   └── app/
│   │       ├── execute.py
│   │       └── diagnose.py            # Commercial Offer Score via Affinitree
│   ├── axis04-brand/                  # Port 8104  (Innovation Score owner)
│   │   └── app/
│   │       ├── execute.py
│   │       └── diagnose.py            # Innovation Score aggregation + brand strength
│   ├── axis05-business-model/         # Port 8105
│   │   └── app/
│   │       ├── execute.py             # BMC, unit economics, financial forecasts
│   │       ├── diagnose.py            # Scalability Score (financial half)
│   │       └── metric_update.py       # Budget watcher signals
│   ├── axis06-legal/                  # Port 8106
│   │   └── app/
│   │       ├── execute.py             # IP strategy, compliance checklists
│   │       ├── diagnose.py            # Green Score via Affinitree
│   │       └── metric_update.py       # Legal radar signals
│   ├── axis07-marketing/              # Port 8107
│   │   └── app/
│   │       ├── execute.py
│   │       └── diagnose.py            # Marketing readiness (feeds Market Score)
│   ├── axis08-sales/                  # Port 8108
│   │   └── app/
│   │       ├── execute.py
│   │       └── diagnose.py            # Sales readiness (feeds Scalability Score)
│   ├── axis09-operations/             # Port 8109
│   │   └── app/
│   │       ├── execute.py             # Workflow plans, lean/agile, supply chain
│   │       ├── diagnose.py            # Scalability Score (operational half)
│   │       └── metric_update.py
│   └── axis10-gtm/                    # Port 8110
│       └── app/
│           ├── execute.py             # Launch playbook, RACI matrix
│           ├── roadmap.py             # RAG-grounded personalised roadmap
│           └── metric_update.py       # Milestone / new KB resource signals
│
├── rag/                               # Knowledge Base RAG service  |  Port 8300
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── ingest.py                  # PDF/web ingestion → Qdrant
│       ├── retrieve.py                # Metadata-filtered hybrid retrieval (RRF)
│       └── admin.py                   # Add/update resources endpoint
│   └── knowledge-base/
│       ├── taxonomy.json              # Stage × Type × Sector taxonomy
│       └── resources/                 # 80-100 curated Tunisian resource documents
│
├── daemon/                            # Go monitoring daemon  (~10 MB binary)
│   ├── Dockerfile
│   ├── go.mod
│   ├── go.sum
│   ├── cmd/
│   │   └── main.go
│   └── internal/
│       ├── watchers/
│       │   ├── budget.go              # 6-hour threshold check
│       │   ├── competitor.go          # 12-hour RSS/web scrape
│       │   ├── legal.go               # Daily regulatory feed
│       │   ├── milestone.go           # Daily deadline alert (14/7/1/0 days)
│       │   └── trend.go               # Weekly keyword frequency
│       ├── redis/
│       │   └── publisher.go           # Publishes to moufida:metrics
│       └── kb_staleness/
│           └── checker.go             # Nightly resource URL hash verification
│
├── frontend/                          # Tauri (Rust) + React + TypeScript
│   ├── src-tauri/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       └── main.rs                # System tray, window management
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── hud/
│   │   │   │   ├── ChatPanel.tsx
│   │   │   │   ├── ReviewCard.tsx     # Approve / Edit / Retry
│   │   │   │   └── AlertFeed.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── MaturityCard.tsx   # Stage + confidence + evidence
│   │   │   │   ├── ScoreGauge.tsx     # Composite score + expandable sub-scores
│   │   │   │   ├── BlockerList.tsx    # Critical / warning / info badges
│   │   │   │   └── RoadmapTimeline.tsx
│   │   │   └── mon-parcours/
│   │   │       ├── ScoreChart.tsx     # Line chart per composite score over time
│   │   │       └── HistoryList.tsx
│   │   ├── voice/
│   │   │   ├── wakeword.ts            # Porcupine ("Hey Moufida")
│   │   │   ├── stt.ts                 # Whisper.cpp (TuniSpeech fine-tune + FR fallback)
│   │   │   └── tts.ts                 # Piper (FR) + Kokoro-82M (AR)
│   │   ├── sse/
│   │   │   └── consumer.ts            # score_update / alert / roadmap_update / review_ready
│   │   └── locales/
│   │       ├── fr.json
│   │       └── ar.json
│   ├── package.json
│   └── tsconfig.json
│
├── db/
│   └── migrations/
│       ├── 001_init.sql               # profiles, diagnostic_history, alerts
│       ├── 002_score_snapshots.sql
│       └── 003_roadmap_versions.sql
│
├── models/                            # AI model checkpoints (gitignored, downloaded at setup)
│   └── .gitkeep
│
├── eval/                              # Evaluation datasets and scripts
│   ├── tier1-maturity/
│   │   ├── vignettes.json             # 50 labelled startup vignettes
│   │   └── run_eval.py
│   ├── tier2-affinitree/
│   │   ├── structured_profiles.json   # Determinism test cases
│   │   ├── text_profiles.json         # Rubric variance test cases
│   │   ├── contradiction_profiles.json # 10 anomaly recall cases
│   │   └── run_eval.py
│   └── tier3-rag/
│       ├── query_pairs.json           # 20 (query, expected-resource) pairs
│       └── run_eval.py
│
└── scripts/
    ├── download-models.sh             # Pulls Whisper, Mistral 7B, Llama 3.1, Piper, Kokoro
    ├── ingest-kb.sh                   # Runs rag/ingest.py on all resources
    └── run-all-evals.sh
```

---

## 2. Implementation Phases

### Phase 0 — Infrastructure & Scaffolding

**Goal:** Every service boots, health checks pass, developers can run the full stack locally with a single `docker compose up`.

- `docker-compose.yml` with services: postgres, redis, qdrant, ollama, orchestrator, all 10 axes, rag, daemon, frontend (dev mode).
- `.env.example` with all required variables (ports, model names, Redis URL, DB DSN, Qdrant URL).
- PostgreSQL migrations (001–003): `profiles`, `diagnostic_history`, `score_snapshots`, `roadmap_versions`, `alerts`.
- Stub FastAPI `main.py` + `/health` route for each axis and the RAG service.
- Go daemon skeleton: `main.go` starts all watchers as goroutines; each watcher logs a heartbeat, publishes nothing.
- Tauri app scaffold: system tray icon with context menu items wired to empty handlers.
- `scripts/download-models.sh`: downloads Whisper large-v2 TuniSpeech checkpoint, Mistral 7B (GGUF), Llama 3.1 8B (GGUF), Piper French voice, Kokoro-82M Arabic voice, fastText language ID model.

---

### Phase 1 — Affinitree Scoring Library

**Goal:** The deterministic scoring core is complete and passes all Tier 2 evaluation targets before any axis is built.

- `StartupProfile` Pydantic model covering all fields from Table 1 (market.*, offer.*, innovation.*, finance.*, ops.*, legal.*) with evidence-tier annotations.
- Five JSON config files (market, commercial_offer, innovation, scalability, green) with sub-dimensions, weights, aggregation method, and citation per dimension. Innovation config matches Listing 2 exactly.
- `scorer.py`: loads config, validates required fields, applies `ci = wi × vi × mi` formula, returns a result object with normalised [0–5] score, per-component contributions (name, raw value, weight, evidence tier, contribution), and a serialisable explanation tree.
- `rubric.py`: wraps Mistral 7B with rubric prompts for the five text fields (value_prop, differentiation, novelty, brand_distinctiveness, sdg_alignment); runs twice, takes median on divergence > 1; returns `{"score": int, "evidence_quote": str, "reasoning": str}`.
- `anomaly.py`: rule engine that checks for contradictions (e.g., mrr_usd > 0 with customer_interviews_count == 0); returns a list of flagged anomalies.
- Tier 2 evaluation suite (`eval/tier2-affinitree/`): determinism test (10 runs → identical), text stability test (5 runs per field → σ ≤ 0.15), anomaly recall test (10 contradiction profiles → 100% recall). All three must pass before Phase 2 begins.

---

### Phase 2 — Adaptive Intake & Diagnostic Engine

**Goal:** STATE_EXISTING first-run flow works end-to-end in the orchestrator; all five scores are computed and returned to a test client.

**Orchestrator:**
- `lang_detect.py`: fastText language ID, returns `ar-TN | fr | other` with confidence.
- `intake/branches.json`: branching rules — agri-food certification questions, revenue > 0 validation questions, legal form questions, self-assessed stage capture.
- `intake/questionnaire.py`: stateful branching engine that reads branches.json and returns the next question given prior answers; populates StartupProfile fields.
- `state_router.py`: reads profile state from PostgreSQL, dispatches to STATE_NEW or STATE_EXISTING LangGraph graph.
- `graph/`: LangGraph graph with nodes for intake, diagnostic pass, aggregation, roadmap call, human review.
- `diagnostic/runner.py`: calls `POST /diagnose` on Axes 01–06 and 09 in dependency order (Axes 01–03 first, then 04 with their outputs, then 05–06 and 09 in parallel).
- `diagnostic/aggregator.py`: computes perception gap (self-assessed vs. Axis 01 stage), merges blocker lists, ranks by severity, triggers Axis 10 roadmap call.
- `redis_consumer.py`: background task that subscribes to `moufida:metrics` and routes messages by type to the correct axis `metric_update` endpoint.

**Axis 01 — Ideation:**
- `diagnose.py`: Mistral 7B prompt → maturity stage (one of six) + confidence + 3–5 evidence points from StartupProfile. Output stored to `diagnostic_history`.
- `metric_update.py`: receives milestone signals, conditionally upgrades maturity stage.

**Axis 02 — Market:**
- `diagnose.py`: calls `Affinitree(profile, "market")`; returns Market Score, component breakdown, market blockers (missing interviews, missing competitor data).
- `metric_update.py`: receives competitor signals, re-runs Affinitree market score, pushes SSE alert if score drops > 0.5.

**Axis 03 — Product:**
- `diagnose.py`: calls `Affinitree(profile, "commercial_offer")`; includes rubric calls for value_prop_text and differentiation_text; returns Commercial Offer Score + product gaps.

**Axis 04 — Brand (Innovation Score owner):**
- `diagnose.py`: receives full profile + Axes 01/02 outputs (TRL, IP, competitor_count); calls `Affinitree(profile, "innovation")`; returns Innovation Score with all four sub-dimension contributions + brand strength indicator.

**Axis 05 — Business Model:**
- `diagnose.py`: deterministic financial engine (pure Python) computes CAC, LTV, payback, runway, burn rate from finance.* fields; calls `Affinitree(profile, "scalability")` for the financial half; returns score + financial blockers.
- `metric_update.py`: receives budget signals, recomputes runway and scalability score, sends critical alert if runway < 3 months.

**Axis 06 — Legal:**
- `diagnose.py`: calls `Affinitree(profile, "green")`; rubric call for sdg_alignment_text; returns Green Score + legal blockers.
- `metric_update.py`: receives legal radar signals, updates compliance checklist, recomputes Green Score.

**Axes 07/08 — Marketing/Sales:**
- `diagnose.py` stubs returning marketing and sales readiness scores (secondary inputs to Market and Scalability scores).

**Axis 09 — Operations:**
- `diagnose.py`: calls `Affinitree(profile, "scalability")` for the operational sub-dimensions (manual_steps_pct, sop_documented, supply_chain_single_point); returns ops scalability score + operational blockers.

**Tier 1 evaluation dataset:** build `eval/tier1-maturity/vignettes.json` with 50 vignettes (published case studies + partner incubator profiles + synthetic), label with three annotators, compute Cohen's κ (target ≥ 0.65), run `run_eval.py` against Axis 01 (target: macro-F1 ≥ 0.65, top-2 accuracy ≥ 0.85).

---

### Phase 3 — Knowledge Base & RAG Service

**Goal:** Axis 10 can retrieve traceable, personalised Tunisian resources for any (gap, stage, sector) combination.

**Knowledge base curation:**
- Collect 80–100 resources from APII, BFPME, BTS, Startup Act, ANPE, incubators, accelerators, EU funds, UNDP, Tunisian legal guides, administrative procedure documents.
- Each resource follows the metadata schema of Listing 1 (id, title, type, stage[], sector[], score_dimensions[], url, language, last_verified, provider).
- Target coverage: ≥ 2 resources per (Stage × Type) cell = 60 floor entries; remaining 20–40 are sector-specific additions for Agri-food, Digital/Tech, Industry.

**RAG service:**
- `ingest.py`: splits documents into paragraph chunks, embeds with `nomic-embed-text` via Ollama, stores in Qdrant with full metadata.
- `retrieve.py`: three-step pipeline — (1) pre-filter by `stage` ∩ diagnosed stage and `score_dimensions` ∩ low-score dimensions; (2) hybrid dense (cosine) + sparse (BM25) retrieval over filtered set, merged with Reciprocal Rank Fusion; (3) sector boost ×1.3 for matching sector. Returns top-k chunks with relevance score, source URL, and title.
- `admin.py`: authenticated endpoint to add a resource or mark one `needs_review`.

**Axis 10 — Go-to-Market:**
- `roadmap.py`: for each gap/low sub-score, formulates a query and calls the RAG `/retrieve` endpoint with stage and dimension filters; uses Llama 3.1 to organise retrieved resources into immediate/short-term/medium-term action plan; stores result in `roadmap_versions`; narration language follows Section 5 language policy.
- `metric_update.py`: on milestone completion or new KB resource, regenerates roadmap.

**Tier 3 evaluation:** `eval/tier3-rag/query_pairs.json` — 20 (query, expected-resource-id) pairs covering all six stages and five resource types; run `run_eval.py` (target: Recall@3 ≥ 0.80, MRR ≥ 0.70).

---

### Phase 4 — Voice Pipeline & Frontend

**Goal:** The desktop app is functional with full voice interaction, real-time dashboard, and working "Mon Parcours" view.

**Voice pipeline (Tauri frontend + native bindings):**
- `voice/wakeword.ts`: Porcupine wake word detection ("Hey Moufida"); transitions app from IDLE to LISTENING.
- `voice/stt.ts`: voice state machine (IDLE → LISTENING → TRANSCRIBING → PROCESSING → SPEAKING); primary path is TuniSpeech fine-tuned Whisper large-v2; fallback to standard French Whisper if `avg_logprob < -0.5`; detected language forwarded to orchestrator `lang_detect` step.
- `voice/tts.ts`: Piper for French output; Kokoro-82M for MSA output; selected based on user's active language preference.

**Tauri system tray (`src-tauri/main.rs`):**
- Tray icon with context menu: Start New Project, Diagnose Existing Project, Open Settings, Quit.
- Settings submenu includes language selector (French / Arabic) that persists to StartupProfile.
- Tray icon pulse animation on non-urgent Go daemon signals.

**HUD overlay:**
- `hud/ChatPanel.tsx`: voice transcript display + text fallback input; sends commands to orchestrator.
- `hud/ReviewCard.tsx`: displays axis output for human review; Approve / Edit / Retry buttons; forwards decision to orchestrator.
- `hud/AlertFeed.tsx`: real-time alert stream from SSE consumer; reads alert via TTS on arrival.

**Dashboard view:**
- `dashboard/MaturityCard.tsx`: current stage badge, confidence %, collapsible evidence list.
- `dashboard/ScoreGauge.tsx`: gauge or number card for each of the five composite scores; expandable to show sub-score table (component name, weight, raw value, evidence tier, contribution); natural-language justification below.
- `dashboard/BlockerList.tsx`: ranked blockers with critical/warning/info severity badges.
- `dashboard/RoadmapTimeline.tsx`: three-column timeline (Immediate / Short-term / Medium-term); each action card has rationale + clickable source link.

**"Mon Parcours" view:**
- `mon-parcours/ScoreChart.tsx`: recharts line chart, one line per composite score, x-axis = timestamp.
- `mon-parcours/HistoryList.tsx`: past maturity stage assignments with evidence, completed roadmap actions with dates.
- Data fetched from orchestrator API reading `diagnostic_history`, `score_snapshots`, `roadmap_versions`.

**SSE consumer (`sse/consumer.ts`):**
- Listens to orchestrator SSE stream; dispatches `score_update` → score widgets, `alert` → AlertFeed + TTS, `roadmap_update` → RoadmapTimeline, `review_ready` → ReviewCard.

**UI localisation:**
- `locales/fr.json` and `locales/ar.json` for all UI strings.
- RTL layout toggled via `dir="rtl"` on root element when Arabic is active.

---

### Phase 5 — Go Daemon & Liveness

**Goal:** The system updates scores and alerts autonomously without any user action.

- `watchers/budget.go`: every 6 hours, reads spend/limit from profile via orchestrator API; publishes at 80%, 90%, 100% thresholds.
- `watchers/competitor.go`: every 12 hours, scrapes RSS feeds and web pages in competitor list; compares page hashes; publishes on new article or product.
- `watchers/legal.go`: daily, fetches EU AI Act and Tunisian Official Gazette feeds; keyword filter (GDPR, Startup Act, AI Act); publishes on new relevant regulation.
- `watchers/milestone.go`: daily, reads project milestones from profile; publishes alerts at 14, 7, 1, 0 days before each deadline.
- `watchers/trend.go`: weekly, counts keyword occurrences in TechCrunch and Wamda RSS; publishes if frequency changes > 50% week-over-week.
- `redis/publisher.go`: publishes JSON messages to `moufida:metrics` with schema `{project_id, type, value, timestamp}`.
- `kb_staleness/checker.go`: nightly, fetches source URLs for resources where `last_verified` > 90 days old; if response hash differs, marks resource `needs_review` via RAG admin endpoint.
- Orchestrator `redis_consumer.py` static routing table wired to all axis `metric_update` endpoints.

---

### Phase 6 — Integration, Evaluation & Submission

**Goal:** Full STATE_NEW and STATE_EXISTING flows work end-to-end on a real machine; all three evaluation tiers pass their targets; results card is ready for hackathon submission.

**Integration testing:**
- End-to-end STATE_NEW walkthrough: voice wake → new project → all 10 axis execute calls → review cards → complete StartupProfile persisted.
- End-to-end STATE_EXISTING walkthrough: voice wake → diagnose → adaptive intake → diagnostic pass on 8 axes → dashboard populated → roadmap generated → Go daemon triggers score update → SSE alert shown and spoken.
- "Mon Parcours" view populated after two diagnostic runs with at least one score change.
- Derja input → lang_detect → translation → rubric scoring → stored with original + translated text.

**Evaluation runs:**
- **Tier 1**: run `eval/tier1-maturity/run_eval.py`; report macro-F1 and top-2 accuracy; document annotator κ.
- **Tier 2a**: `run_eval.py --determinism`; must be 100%.
- **Tier 2b**: `run_eval.py --text-stability`; flag any field with σ > 0.15 for rubric refinement.
- **Tier 2c**: `run_eval.py --anomaly`; must detect all 10 contradiction cases.
- **Tier 3**: `eval/tier3-rag/run_eval.py`; report Recall@3 and MRR; iterate on retrieval pipeline if below targets.

**Results card:** structured markdown document reporting dataset size, labelling protocol, annotator profiles, inter-annotator κ, and metric value per tier. Where a target is missed, include diagnosis and mitigation applied.

**Known limitations disclosure (onboarding flow):** Derja voice output is not attempted; responses are always in French or MSA. Disclosed to user on first launch.

---

## 3. Phase Summary

| Phase | Scope | Key Deliverable |
|---|---|---|
| 0 | Infrastructure & scaffolding | Full stack boots with `docker compose up` |
| 1 | Affinitree scoring library | All 5 scores computable; Tier 2 evaluation passes |
| 2 | Adaptive intake & diagnostic engine | STATE_EXISTING diagnostic pass returns all 5 scores |
| 3 | Knowledge base & RAG service | Axis 10 generates traceable, personalised roadmap; Tier 3 evaluation passes |
| 4 | Voice pipeline & frontend | Desktop app fully interactive with dashboard and "Mon Parcours" |
| 5 | Go daemon & liveness | Scores update autonomously from real-world signals |
| 6 | Integration, evaluation & submission | All Tier 1–3 targets met; results card produced |
