# System Overview

Moufida is a 100% locally-run AI diagnostic platform for Tunisian entrepreneurs. Every model inference, database write, and retrieval call happens on the founder's own machine — nothing leaves the device.

---

## Component Map

| Component | Lang | Port | Role |
|---|---|---|---|
| Tauri Desktop App | React/TS + Rust | — (host) | Primary UI, voice pipeline, companion window |
| Orchestrator | Python/FastAPI | 8001 | Central brain — all 18 API routers |
| Axis Services (×10) | Python/FastAPI | 8101–8110 | Per-axis generate + diagnose + metric_update |
| Scoring Engine (Affinitree) | Python | 8200 | Deterministic formula-based scoring library |
| RAG Service | Python/FastAPI | 8300 | Hybrid retrieval + KB management + web search |
| Signal Service | Rust/Axum | 8010 | Concept Bottleneck + Axis Direction Probe |
| Go Daemon | Go | — (internal) | Background monitoring, 6 adaptive watchers |
| Admin Panel | React/Vite | 3002 | Read-only observability SPA |
| PostgreSQL | — | (internal) | All persistent relational data |
| Redis | — | (internal) | Pub/sub messaging (daemon → orchestrator) |
| Qdrant | — | (internal) | Vector store for KB embeddings |
| SearXNG | — | (internal) | Self-hosted metasearch (no API keys) |
| Ollama | — | 11434 (host) | LLM inference + embeddings |

---

## Request Flow — Diagnosis

```
Founder clicks "Diagnose"
  └─► POST /api/v1/project/{id}/diagnostic (Orchestrator)
        │
        ├─► score_profile_text_fields()   — rubric-score free-text via Ollama
        ├─► enrich_profile()              — pull tools upgrade evidence tiers (T1→T3)
        │
        ├─► Wave 0 (parallel): ideation + market + legal
        │     each service:
        │       RAG /retrieve  →  Qdrant + BM25 + Signal /probe/project (axis-aware rerank)
        │       Affinitree.score()  →  deterministic formula scoring
        │       Ollama  →  justification text
        │       Signal /cbm/score   →  concept breakdown + bottleneck
        │
        ├─► Wave 1 (parallel, depends on wave 0): product + business-model + operations
        ├─► Wave 2 (parallel, depends on wave 1): brand + marketing + sales + go-to-market
        │
        ├─► Aggregate: anomaly detection, maturity stage classification
        ├─► Persist: diagnostic_history + score_snapshots + concept_scores
        └─► SSE push: score_update × 10, maturity_update, review_ready, concept_update
```

## The Four Update Sources

After the first diagnosis, Moufida stays live. Any of four sources can trigger a dependency-aware axis re-run:

| Source | Example | How it arrives |
|---|---|---|
| Manual edit | Founder updates a plan section | `POST /event` source=manual |
| Chat intent | "We pivoted to B2B" | LLM intent detection → `apply_update()` |
| Tool signal | GitHub push via Composio | `tool_signals` table → dispatch |
| Daemon event | Competitor launched new feature | Redis pub/sub → `redis_consumer.py` |

The dependency engine (`dependency.py`) resolves which downstream axes must re-run — a market signal cascades to product → brand → marketing → sales but not to legal.

## Privacy

| Concern | Implementation |
|---|---|
| LLM inference | Ollama on host GPU/CPU — no OpenAI, Anthropic, or any cloud LLM |
| Embeddings | `bge-m3` multilingual, runs via Ollama locally |
| Voice STT | Whisper via `whisper-cli` on the host — audio never leaves the machine |
| Voice TTS | Piper (FR) + Kokoro-82M (EN) run as local ONNX models |
| Web search | SearXNG is self-hosted — no Google/Bing API keys |
| External auth | Composio is the only optional cloud dependency (managed OAuth only) |
| Storage | PostgreSQL + Qdrant in Docker, no host ports exposed by default |

---

## Further Reading

- [Orchestrator](orchestrator.md) — all 18 API routers
- [Axis Services](axis-services.md) — 10 diagnostic/generation services
- [Scoring Engine](scoring-engine.md) — Affinitree formulas
- [RAG & Knowledge Base](rag-and-knowledge-base.md) — hybrid retrieval + 83 curated resources
- [Signal Service](signal-service.md) — CBM + Axis Direction Probe; see also [research/](../research/)
- [Go Daemon](daemon.md) — background monitoring
- [Database](database.md) — 20 SQL migrations
- [Desktop App](desktop-app.md) — Tauri shell + voice + companion
- [Tool Integrations](tool-integrations.md) — GitHub, Notion, Slack, GA, Composio
- [Local Models](models.md) — Whisper, Piper, Kokoro, fastText
- [Web Interfaces](web-interfaces.md) — Admin panel + Landing page
