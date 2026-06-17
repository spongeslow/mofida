# Moufida — مفيدة

**An intelligent, voice-first entrepreneurial companion for Tunisian founders.**

Moufida (Arabic for "useful") lives in your system tray. You wake it by saying *"Hey Moufida"*, describe your startup by voice, and it replies by speaking back — in French or English. Everything runs on your own machine. No data leaves your computer.

Built for Team Makrouna Kadheba · June 2026 hackathon submission.

---

## What it does

Moufida covers two modes of use:

**Starting a new project (STATE_NEW):** Ten specialised agents guide you step by step through idea validation, market research, product design, brand, business model, legal, marketing, sales, operations, and go-to-market. After each step you review and approve the output before moving on.

**Diagnosing an existing project (STATE_EXISTING):** You describe your current situation. Moufida asks adaptive follow-up questions, then produces:

- A **maturity stage** (Ideation → Market Validation → Structuration → Fundraising → Launch Planning → Growth) with evidence points
- Five **composite scores** — Market, Commercial Offer, Innovation, Scalability, Green — each broken down into sub-dimensions with weights, evidence tiers, and plain-language explanations
- A ranked list of **priority blockers** (critical / warning / info)
- A personalised **roadmap** linking real Tunisian support programmes, financing options, and guides to your specific gaps
- Automatic **anomaly detection** that flags contradictory signals (e.g. revenue claimed with zero customer interviews)

After the first diagnosis, Moufida stays alive in the background. A lightweight Go daemon watches your competitors, budget, legal landscape, and project milestones 24/7, updating scores and alerting you without any user action.

---

## Core design principles

| Principle | How it is implemented |
|---|---|
| 100% local | All LLMs run via Ollama (llama3.1:8b, nomic-embed-text). Voice models (Whisper, Piper, Kokoro-82M) run locally. |
| Explainable scoring | Every score decomposes to a formula: `ci = wi × vi × mi` where `mi` reflects the evidence quality (declared × 0.6, verified document × 1.0, daemon-observed × 1.2). |
| Traceable resources | Every roadmap action links to a real, verified source URL. No hallucinated programme names. |
| Bilingual first-class | French and English supported throughout the voice pipeline. STT uses Whisper large-v2; TTS uses Piper (FR) and Kokoro-82M (EN). Language is auto-detected per utterance via fastText. |
| Liveness | The system updates itself from real-world signals even when you're not interacting with it. |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Tauri Desktop App (React + TypeScript)  [host]     │
│  System tray · HUD overlay · Dashboard · Mon Parcours│
│  Voice: Porcupine → Whisper → Piper / Kokoro-82M   │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────▼──────────────────────────────┐
│  Orchestrator  :8001                                 │
│  FastAPI + LangGraph                                 │
│  - State router (STATE_NEW / STATE_EXISTING)         │
│  - Adaptive intake questionnaire                     │
│  - Diagnostic runner (3-wave dependency order)       │
│  - Redis consumer → service metric_update routing    │
└──┬────────────────────────────────────────────────┬─┘
   │ POST /diagnose (3 waves)                       │
   ▼                                                ▼
┌──────────────────────┐         ┌──────────────────────┐
│  10 Specialised       │         │  RAG Service  :8300  │
│  Services :8101–8110  │         │  Qdrant + BM25 + RRF │
│  (each a FastAPI app) │         │  80-100 Tunisian KB  │
│  Scoring engine       │─────────▶  /retrieve           │
│  (shared library)     │         └──────────────────────┘
└──────────────────────┘
          ▲
          │ moufida:metrics (Redis pub/sub)
┌─────────┴────────────┐
│  Go Daemon           │
│  5 watchers 24/7:    │
│  budget · competitor │
│  legal · milestone   │
│  trend + KB staleness│
└──────────────────────┘

Datastores: PostgreSQL · Redis · Qdrant
Ollama (host): llama3.1:8b · nomic-embed-text
Voice (host):  Whisper large-v2 · Piper FR · Kokoro-82M EN · fastText LID
```

---

## Five composite scores

| Score | Owner service | Sub-dimensions |
|---|---|---|
| Market | market-intelligence | Addressable market size, customer validation evidence, revenue model clarity, competitive intensity |
| Commercial Offer | product-offering | Value proposition clarity, product maturity, pricing coherence, differentiation |
| Innovation | brand-innovation | Product/tech novelty 35%, market novelty 25%, brand distinctiveness 20%, value-creation novelty 20% |
| Scalability | business-model + operations | Unit economics, funding readiness, revenue model, automation, supply-chain resilience, quality framework |
| Green | legal-compliance | GDPR compliance, AI Act compliance, IP protection, SDG alignment, environmental impact |

---

## Current state (as of June 2026)

Phases 0 and 1 are complete. See [`docs/omar.md`](docs/omar.md) for a detailed breakdown of what is built and what comes next.

**Working right now:**
- All backend services boot and pass `/health` checks via `docker compose up`
- The scoring engine computes all five composite scores with full explainability trees
- 5 of 10 service `diagnose` endpoints return real scores (market, commercial offer, innovation, scalability, green)
- Anomaly detection passes 10/10 contradiction recall cases
- Determinism test passes 100% (identical results on 10 repeated runs)
- PostgreSQL schema is in place (profiles, diagnostic history, score snapshots, roadmap versions, alerts)
- Frontend scaffold builds with system-tray menu and language toggle (FR/EN)

**Coming next (Phase 2):** adaptive intake questionnaire, maturity classifier (Axis 01 / ideation-service), LangGraph diagnostic pass orchestration, and the orchestrator's Redis consumer.

---

## Setup

### 1. Install prerequisites

| Tool | Purpose | Install |
|---|---|---|
| Docker + Compose | Runs all backend services | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Ollama | Serves LLM and embeddings locally | [ollama.com/download](https://ollama.com/download) |
| Node.js 20+ | Builds the Tauri frontend | [nodejs.org](https://nodejs.org/) |
| Rust + Cargo | Required by Tauri | [rustup.rs](https://rustup.rs/) |
| Tauri CLI | `tauri dev` / `tauri build` | `cargo install tauri-cli` |

```bash
# Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

# Tauri CLI
cargo install tauri-cli

# Node.js 20 via nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 20 && nvm use 20
```

### 2. Configure environment

```bash
cp .env.example .env
```

### 3. Pull models and download voice assets

Run once after setting up `.env`. This pulls Ollama models and downloads all local voice files:

```bash
./scripts/setup.sh
```

Add `--skip-whisper` to defer the 1.1 GB Whisper download and finish in ~150 MB first:

```bash
./scripts/setup.sh --skip-whisper
```

What the script handles automatically:

| Asset | File | Size |
|---|---|---|
| LLM | `llama3.1:8b` via Ollama | ~4.7 GB |
| Embeddings | `nomic-embed-text` via Ollama | ~274 MB |
| Language ID | `models/lid.176.ftz` | ~1 MB |
| French TTS | `models/piper-fr.onnx` + `.onnx.json` | ~61 MB |
| TTS engine | `models/kokoro/model_quantized.onnx` | ~89 MB |
| French voice | `models/kokoro/voices/ff_siwis.bin` | ~510 KB |
| English voice | `models/kokoro/voices/af_heart.bin` | ~510 KB |
| STT (EN + FR) | `models/whisper.bin` (Whisper large-v2 q5_0) | ~1.1 GB |

The **Porcupine wake word** requires a free [Picovoice](https://console.picovoice.ai/) account — the script prints exact steps for this when it reaches that point.

### 4. Start the backend

Make sure Ollama is running, then:

```bash
docker compose up --build
```

This starts: PostgreSQL (migrations applied automatically), Redis, Qdrant, the orchestrator, 10 axis services, the RAG service, the Go daemon, and the scoring engine API (`:8200`).

The **frontend is not started by `docker compose up`** — it runs on the host (see step 5).

> **No port conflicts with local databases:** PostgreSQL, Redis, and Qdrant do not bind to host ports. To access them from the host: `docker compose exec postgres psql -U $POSTGRES_USER`

Verify the backend is healthy:
```bash
curl http://localhost:8001/health   # orchestrator
curl http://localhost:8102/health   # market-intelligence-service
curl http://localhost:8200/health   # scoring engine API
curl http://localhost:8300/health   # rag service
```

### 5. Run the desktop app

With the Docker backend running (step 4), open a **separate terminal**:

```bash
cd frontend
npm install        # first time only
npm run tauri dev  # starts Vite on :5173, opens the system-tray app
```

Tauri starts its own Vite dev server on port 5173 and opens the native desktop window. The app communicates with the backend at `localhost:8001`.

> **Do not run `docker compose --profile web up frontend`** at the same time as `npm run tauri dev` — both use port 5173 and will conflict. The `--profile web` frontend container is only for browser access without the Tauri shell.

---

## Scoring engine (standalone)

The scoring engine also runs as a Docker service on port `:8200` with a REST API:

```bash
curl http://localhost:8200/health
# POST /score      — compute one named score for a profile
# POST /score/all  — compute all five scores in one call
# POST /detect     — run anomaly detection on a profile
```

To run tests or work on the engine without Docker:

```bash
cd scoring-engine
uv venv && uv pip install -e ".[dev]"
.venv/bin/python -m pytest -q

# Tier 2 evals (determinism + anomaly recall — no LLM needed)
cd ..
scoring-engine/.venv/bin/python eval/tier2-affinitree/run_eval.py
```

---

## Evaluation targets

| Tier | Subsystem | Metric | Target | Status |
|---|---|---|---|---|
| T2a | Scoring engine determinism | 10-run identity | 100% | ✅ Pass |
| T2c | Anomaly detection recall | 10 contradictions | 100% | ✅ Pass |
| T2b | Rubric LLM stability | σ ≤ 0.15 per field | σ ≤ 0.15 | Needs Ollama |
| T1 | Maturity classifier | Macro-F1 ≥ 0.65, Top-2 Acc ≥ 0.85 | — | Phase 2 |
| T3 | RAG retrieval | Recall@3 ≥ 0.80, MRR ≥ 0.70 | — | Phase 3 |

---

## Repository layout

```
scoring-engine/      Affinitree scoring library + standalone HTTP API (:8200)
orchestrator/        FastAPI brain + axis registry + topology endpoint
services/            10 specialised FastAPI services (5 scoring, 5 stubs)
rag/                 Knowledge-base RAG service + taxonomy (stubs)
daemon/              Go monitoring daemon (goroutines on real cadences, heartbeat)
frontend/            Tauri + React/TS desktop app (runs on host, not in Docker)
db/migrations/       3 SQL migrations (auto-run by postgres container)
eval/                Tier 2 fixtures + runner · Tier 1/3 placeholders
scripts/             setup.sh · ingest-kb · run-all-evals
docs/                Full technical spec + component architecture
docs/plan/           Implementation plan (phases 0–6)
docs/omar.md         Current state + detailed next-steps breakdown
```

---

## Documentation

| Document | Contents |
|---|---|
| [`docs/01-prd-and-system-overview.md`](docs/01-prd-and-system-overview.md) | Hackathon PRD requirements and system overview |
| [`docs/02-component-architecture.md`](docs/02-component-architecture.md) | Detailed component specs, StartupProfile schema, Affinitree formulas |
| [`docs/03-language-and-evaluation.md`](docs/03-language-and-evaluation.md) | Language pipeline, voice models, evaluation framework |
| [`docs/04-mapping-workflows-conclusion.md`](docs/04-mapping-workflows-conclusion.md) | Two-state workflow walkthrough and PRD coverage map |
| [`docs/plan/implementation-plan.md`](docs/plan/implementation-plan.md) | Six-phase build plan with deliverables |
| [`docs/omar.md`](docs/omar.md) | What is built, what is stubbed, and what comes next — in detail |
