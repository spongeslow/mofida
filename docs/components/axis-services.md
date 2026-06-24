# Axis Services

**Location:** `backend/services/` | **Ports:** 8101–8110  
**Stack:** Python 3.12, FastAPI, httpx, Affinitree (in-process library)

Ten specialised microservices, one per business domain. All share an identical three-endpoint contract.

---

## Shared Contract

Every axis service exposes:

**`GET /health`**

**`POST /generate`** (creation mode) — called by the orchestrator after it prefetches KB evidence and live web results. The `evidence` block is passed in the request, forcing every generated claim to be citation-backed. Returns a structured JSON proposal with inline `[n]` markers.

**`POST /diagnose`** (diagnosis mode) — receives a `StartupProfile`, calls `Affinitree.score()`, runs `run_due_diligence()`, calls Ollama for a justification text. Returns `score`, `explanation_tree`, `missing_fields`, `blockers`, `dd_flags`, `justification`. See [scoring-engine.md](scoring-engine.md) for the scoring math.

**`POST /metric_update`** — receives structured daemon signals (competitor change, trend spike, budget alert, legal update, milestone). Formats an SSE alert and pushes it back to the orchestrator.

---

## The Ten Axes

| # | Service | Port | Domains assessed | Special features |
|---|---|---|---|---|
| 1 | **Ideation** | 8101 | Problem clarity, solution originality, founder-market fit, idea testability | Also classifies **maturity stage** (6 stages); daemon receives `milestone` signals |
| 2 | **Market Intelligence** | 8102 | TAM/SAM/SOM, customer validation evidence, revenue model, competitive intensity | Receives `competitor_change`, `trend_spike` signals |
| 3 | **Product Offering** | 8103 | MVP existence, technical feasibility, feature definition, UX consideration | — |
| 4 | **Brand & Innovation** | 8104 | Product/tech novelty (35%), market novelty (25%), brand distinctiveness (20%), value-creation novelty (20%) | Receives `prior_outputs` from wave-0 axes as upstream context |
| 5 | **Business Model** | 8105 | Revenue model, unit economics (LTV/CAC), pricing strategy, path to profitability | Bidirectional SCC with Axis 9; receives `budget_alert` |
| 6 | **Legal Compliance** | 8106 | GDPR, AI Act, IP protection, entity registration, SDG alignment | Receives `legal_update` signals |
| 7 | **Marketing** | 8107 | GTM strategy, channel identification, messaging clarity, content presence | — |
| 8 | **Sales** | 8108 | Pipeline existence, sales process, conversion evidence, revenue traction | — |
| 9 | **Operations** | 8109 | Team completeness, process definition, supplier readiness, operational capacity | Bidirectional SCC with Axis 5 |
| 10 | **Go-to-Market** | 8110 | Launch-readiness synthesis; roadmap integration | `/generate` produces final roadmap |

---

## Three-Wave Parallelism

```
Wave 0 (simultaneous):  ideation · market · legal
         ↓  (depends on wave 0 scores)
Wave 1 (simultaneous):  product · business-model · operations
         ↓  (depends on wave 1 scores)
Wave 2 (simultaneous):  brand · marketing · sales · go-to-market
```

Total diagnosis time ≈ 3 × (slowest single axis call) ≈ 30–60 seconds depending on Ollama throughput.

---

## Evidence-Grounded Generation

Before calling any `/generate` endpoint the orchestrator:
1. Retrieves 3–5 KB chunks with axis-direction re-ranking (`current_axis` passed to RAG)
2. Runs a SearXNG live web search for the axis topic + sector
3. Formats an `evidence_block` with citations
4. Passes it in the request body

The axis Ollama prompt includes the evidence block; every generated claim is constrained to cited sources. See [rag-and-knowledge-base.md](rag-and-knowledge-base.md) for the retrieval details.

---

## Investor-Grade Due Diligence

Every `/diagnose` call runs `run_due_diligence()` beyond the standard scoring:
- Market: SAM/SOM derivation present, pricing sensitivity analysis
- Business model: LTV/CAC ratio, payback period
- Legal: IP ownership chain, compliance calendar, data processing agreements
- Operations: key-person risk, supplier concentration

These flags appear as investability indicators on the dashboard and feed the `PitchReadinessReport`.

---

## Academic Grounding by Score

| Composite Score | Axis | Key References |
|---|---|---|
| Market | market-intelligence | Kotler & Keller (2016) Marketing Management; Blank (2013) Customer Development |
| Commercial Offer | product-offering | Osterwalder et al. (2014) Value Proposition Design |
| Innovation | brand-innovation | OECD Oslo Manual (2018) |
| Scalability | business-model + operations | Ries (2011) Lean Startup; Christensen (1997) Innovator's Dilemma |
| Green | legal-compliance | EU AI Act; GDPR; UN SDG framework |
