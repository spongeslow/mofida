# Moufida

**Intelligent Entrepreneurial Orientation Engine** — a voice-first, 100% local AI
companion for entrepreneurs in Tunisia. Team Makrouna Kadheba.

See [`docs/`](docs/) for the full technical specification and
[`docs/plan/implementation-plan.md`](docs/plan/implementation-plan.md) for the
phased build plan.

## Architecture at a glance

| Component | Tech | Port |
|---|---|---|
| Orchestrator (state router, intake, diagnostic pass, LangGraph) | FastAPI | 8001 |
| Axes 01–10 (specialised agents) | FastAPI | 8101–8110 |
| Knowledge-Base RAG | FastAPI + Qdrant | 8300 |
| Affinitree | shared Python scoring library | — |
| Monitoring daemon (5 watchers + KB staleness) | Go | — |
| Desktop app (tray, dashboard, voice) | Tauri + React/TS | host |
| Datastores | PostgreSQL, Redis, Qdrant | 5432 / 6379 / 6333 |
| Local models | Ollama (Mistral 7B, Llama 3.1, nomic-embed) | 11434 |

## Quick start

```bash
cp .env.example .env
docker compose up --build            # boots all backend services
./scripts/download-models.sh         # pulls Ollama + voice models
cd frontend && npm install && npm run tauri dev   # desktop app (on host)
```

Every backend service exposes `GET /health`.

## Affinitree scoring library

The deterministic, explainable scoring core (`affinitree/`) is independent and
fully tested.

```bash
cd affinitree
uv venv && uv pip install -e ".[dev]"
.venv/bin/python -m pytest -q          # 24 unit tests
```

The five composite scores (Market, Commercial Offer, Innovation, Scalability,
Green) are weighted sums of literature-cited sub-dimensions, computed as
`ci = wi × vi × mi` where `mi` is the three-tier evidence multiplier
(declared ×0.6 / artefact-backed ×1.0 / daemon-observed ×1.2). Configs live in
`affinitree/affinitree/config/*.json`; the Innovation config matches Listing 2
of the spec exactly.

## Evaluation

```bash
./scripts/run-all-evals.sh
```

- **Tier 2a** (determinism): 100% ✅
- **Tier 2c** (anomaly recall, 10 cases): 100% ✅
- **Tier 2b** (rubric stability): needs a live Ollama backend
- **Tier 1 / Tier 3**: arrive with Phases 2 / 3

## Repository layout

```
affinitree/   shared scoring library (Phase 1 — done)
orchestrator/ FastAPI brain + axis registry
axes/         10 axis microservices (scoring axes wired to Affinitree)
rag/          knowledge-base RAG service + taxonomy
daemon/       Go monitoring daemon (stdlib skeleton)
frontend/     Tauri + React desktop app scaffold
db/migrations 001 init · 002 score_snapshots · 003 roadmap_versions
eval/         three-tier evaluation suites
scripts/      model download · KB ingest · run-all-evals
```
