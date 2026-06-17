# Moufida — مفيدة

**An intelligent, voice-first entrepreneurial companion for Tunisian founders.**

Moufida (Arabic for "useful") lives in your system tray. You wake it by saying *"Hey Moufida"*, describe your startup by voice, and it replies by speaking back — in French or Arabic. Everything runs on your own machine. No data leaves your computer.

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
| 100% local | All LLMs run via Ollama (Mistral 7B, Llama 3.1, nomic-embed-text). Voice models (Whisper, Piper, Kokoro-82M) run locally. |
| Explainable scoring | Every score decomposes to a formula: `ci = wi × vi × mi` where `mi` reflects the evidence quality (declared × 0.6, verified document × 1.0, daemon-observed × 1.2). |
| Traceable resources | Every roadmap action links to a real, verified source URL. No hallucinated programme names. |
| Bilingual first-class | French and Tunisian Arabic (Derja) both supported throughout the voice pipeline. The LLM output defaults to French or MSA (Derja generation is not attempted — disclosed on first launch). |
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
Models: Ollama (Mistral 7B · Llama 3.1 · nomic-embed)
        Whisper TuniSpeech · Piper FR · Kokoro-82M AR
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
- Frontend scaffold builds with system-tray menu and language toggle

**Coming next (Phase 2):** adaptive intake questionnaire, maturity classifier (Axis 01 / ideation-service), LangGraph diagnostic pass orchestration, and the orchestrator's Redis consumer.

---

## Quick start

```bash
# 1. Copy and fill in environment variables
cp .env.example .env

# 2. Boot the backend (first run pulls Docker images — ~4 GB)
docker compose up --build

# 3. Pull Ollama models (needs the ollama service to be running)
./scripts/download-models.sh

# 4. Run the desktop app (on the host, needs a display)
cd frontend
npm install
npm run tauri dev
```

Every backend service exposes `GET /health`. Check them:
```bash
curl http://localhost:8001/health   # orchestrator
curl http://localhost:8102/health   # market-intelligence-service
curl http://localhost:8300/health   # rag
```

---

## Scoring engine (standalone)

The `scoring-engine/` package can be installed and tested without any running services.

```bash
cd scoring-engine
uv venv && uv pip install -e ".[dev]"

# Run the 24-test suite
.venv/bin/python -m pytest -q

# Run Tier 2 evals (determinism + anomaly recall — no LLM needed)
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
scoring-engine/      Affinitree scoring library (done — 24 tests green)
orchestrator/        FastAPI brain + axis registry + topology endpoint
services/            10 specialised FastAPI services (5 scoring, 5 stubs)
rag/                 Knowledge-base RAG service + taxonomy (stubs)
daemon/              Go monitoring daemon (goroutines on real cadences, heartbeat)
frontend/            Tauri + React/TS desktop app (scaffold + locales)
db/migrations/       3 SQL migrations (auto-run by postgres container)
eval/                Tier 2 fixtures + runner · Tier 1/3 placeholders
scripts/             download-models · ingest-kb · run-all-evals
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
| [`docs/03-language-and-evaluation.md`](docs/03-language-and-evaluation.md) | French/Arabic pipeline, voice models, evaluation framework |
| [`docs/04-mapping-workflows-conclusion.md`](docs/04-mapping-workflows-conclusion.md) | Two-state workflow walkthrough and PRD coverage map |
| [`docs/plan/implementation-plan.md`](docs/plan/implementation-plan.md) | Six-phase build plan with deliverables |
| [`docs/omar.md`](docs/omar.md) | What is built, what is stubbed, and what comes next — in detail |
