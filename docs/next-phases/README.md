# Moufida — Next Phases Implementation Plan

This folder breaks the remaining work into ordered, self-contained phase documents. Read this index first: it carries the **audit of what is actually built**, the **dependency order**, and the **cross-cutting issues** that span multiple phases.

> ⚠️ The earlier `docs/omar.md` and the original `docs/plan/implementation-plan.md` describe the *intended* state. This folder describes the *actual* state after the phase2 merge, including correctness gaps that those documents do not mention.

---

## Status Legend

| Symbol | Meaning |
|---|---|
| ✅ | Implemented and correct per spec |
| 🟡 | Implemented but incomplete or incorrect vs spec (silent wrong output) |
| ⏳ | Scaffolded / stub only |
| ❌ | Not started |

---

## Audit Summary — What Is Actually Working

| Subsystem | Spec intent | Reality | Status |
|---|---|---|---|
| Affinitree numeric scoring | Deterministic weighted sum | Correct | ✅ |
| Affinitree **rubric (text) scoring** | LLM-as-judge for 5 text fields | **Wired in the library but no axis ever calls it → text fields silently score 0** | 🟡 |
| Market score (Axis 02) | All-numeric | Correct | ✅ |
| Commercial Offer (Axis 03) | 4 sub-dims incl. 2 rubric | **~40% of weight (value-prop + differentiation) scores 0** | 🟡 |
| Innovation (Axis 04) | 4 sub-dims incl. 2 rubric + Axes 01/02 inputs | **~40% of weight (brand + value-creation novelty) scores 0; `prior_outputs` ignored** | 🟡 |
| Scalability (Axes 05/09) | Incl. deterministic financial engine | **No CAC/LTV/payback/runway engine; pure Affinitree only** | 🟡 |
| Green (Axis 06) | 5 sub-dims incl. 1 rubric | **SDG-alignment sub-dim scores 0** | 🟡 |
| **Blocker identification** | Each axis returns ranked blockers (PRD Feature 1) | **No axis emits `blockers`; aggregator always receives `[]`** | ❌ |
| Anomaly aggregation | Union of detected anomalies | **Each of 5 axes returns the global list → 5× duplication in aggregator** | 🟡 |
| Natural-language justification | Plain-language per score | Not implemented anywhere | ❌ |
| Maturity classifier (Axis 01) | LLM stage + evidence | Correct | ✅ |
| Adaptive intake | Branching questionnaire | Correct (sector enum fixed) | ✅ |
| Diagnostic runner / aggregator | 3-wave fan-out | Works, but see blockers/anomalies above | 🟡 |
| Marketing / Sales (Axes 07/08) | Readiness scores | Stub | ⏳ |
| Roadmap (Axis 10) | RAG-grounded plan | Stub | ❌ |
| RAG service | Hybrid retrieval | Stub | ❌ |
| Go daemon | 6 real watchers + Redis | Heartbeat only | ⏳ |
| Redis consumer | Route metrics to axes | Not built | ❌ |
| Frontend | Dashboard / voice / Mon Parcours | Empty stubs | ⏳ |

**Headline:** Three of the five composite scores (Commercial Offer, Innovation, Green) currently return numbers that are **wrong**, not just incomplete — the rubric sub-dimensions silently contribute 0 instead of their LLM-judged value. A demo today would show artificially deflated scores. This is the highest-priority fix and is documented in **[phase2b-axis-services.md](./phase2b-axis-services.md)**.

---

## Are the `services/` Well Implemented?

**Short answer: the 5 scoring axes run and return a score, but 3 of them are materially incorrect, and the mandatory blocker-identification feature is absent from all of them.** The 5 stub axes (01-execute, 07, 08, 10) are unimplemented by design for this stage. Details and fixes are in **[phase2b-axis-services.md](./phase2b-axis-services.md)** — read it before any frontend work, because the dashboard will display the wrong numbers until these are fixed.

---

## Phase Documents & Dependency Order

```
phase2b-axis-services.md   ← FIX FIRST (correctness of existing scores)
        │
        ▼
phase2-completion.md       ← orchestrator glue: redis consumer, marketing/sales,
        │                    justification, guidance, Tier-1 dataset
        ├──────────────► phase3-rag-knowledge-base.md   (KB + RAG + Axis 10 roadmap)
        │                        │
        ▼                        ▼
phase5-daemon-liveness.md   phase4-voice-frontend.md   (can run in parallel
        │                        │                       once phase2/3 data exists)
        └────────────┬───────────┘
                     ▼
        phase6-integration-evaluation.md   ← LAST (E2E + all eval tiers + results card)
```

| Order | Document | Priority | Rough effort |
|---|---|---|---|
| 1 | [phase2b-axis-services.md](./phase2b-axis-services.md) | 🔴 Demo-critical | 2–3 days |
| 2 | [phase2-completion.md](./phase2-completion.md) | 🔴 Demo-critical | 3–4 days |
| 3 | [phase3-rag-knowledge-base.md](./phase3-rag-knowledge-base.md) | 🔴 Demo-critical | 5–7 days (KB curation dominates) |
| 4 | [phase4-voice-frontend.md](./phase4-voice-frontend.md) | 🟠 High (the demo surface) | 7–10 days |
| 5 | [phase5-daemon-liveness.md](./phase5-daemon-liveness.md) | 🟡 Medium (the "liveness" differentiator) | 4–5 days |
| 6 | [phase6-integration-evaluation.md](./phase6-integration-evaluation.md) | 🔴 Submission gate | 3–4 days |

Phase 3 KB curation is mostly research/data-entry and can start in parallel on day 1.

---

## Cross-Cutting Conventions (apply in every phase)

1. **No hardcoded config.** Use `os.environ["KEY"]` (fail fast) in Python and `mustenv` in Go. Never bake URLs/credentials/model names as fallbacks. `.env.example` keeps every key with an **empty** value.
2. **Diagnose response contract.** Every axis `/diagnose` must return at minimum:
   ```json
   {"axis": N, "score_name": "...", "score": 0.0, "explanation": {...},
    "missing_fields": [...], "blockers": [...], "justification": "..."}
   ```
   `anomalies` is computed once by the aggregator, **not** per-axis (see phase2b).
3. **Blocker schema** (shared across all axes and the aggregator):
   ```json
   {"axis": "market", "code": "no_customer_interviews",
    "description": "No customer interviews recorded.",
    "severity": "critical|warning|info", "score_dimension": "market",
    "remediation": "Run at least 5 structured interviews."}
   ```
4. **SSE event names** are fixed: `score_update`, `alert`, `roadmap_update`, `review_ready`, `maturity_update`. Don't invent new ones without updating both producer (`orchestrator/app/sse.py`) and consumer (`frontend/src/sse/consumer.ts`).
5. **Language** flows through `profile.language` (`fr` default, `en` optional). Derja (`ar-TN`) input is translated to French before rubric scoring; output is never Derja (documented limitation).
6. **Acceptance criteria are executable.** Each phase ends with a checklist of `curl`/CLI commands that must produce the stated output before the phase is "done."

---

## Spec Cross-Reference

| Topic | Spec section |
|---|---|
| PRD mandatory features | `docs/01-prd-and-system-overview.md` §1 |
| Per-axis responsibilities | `docs/02-component-architecture.md` §3.2 |
| StartupProfile field catalogue | `docs/02-component-architecture.md` §3.3.2 (Table 1) |
| Rubric scoring procedure | `docs/02-component-architecture.md` §3.3.3 |
| Innovation Score ownership/formula | `docs/02-component-architecture.md` §4 |
| Knowledge base taxonomy | `docs/02-component-architecture.md` §3.5 |
| Language pipeline | `docs/03-language-and-evaluation.md` §5 |
| Evaluation tiers | `docs/03-language-and-evaluation.md` §6 |
