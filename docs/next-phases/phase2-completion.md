# Phase 2 Completion — Remaining Adaptive Intake & Diagnostic Items

**Status:** Orchestrator-side glue. This document covers the orchestrator and the marketing/sales stubs. The **correctness of the existing scoring axes is a separate, higher-priority task** — do [phase2b-axis-services.md](./phase2b-axis-services.md) **first**, because the items below assume the axes emit correct scores and real `blockers`.

> ⚠️ Do not trust the "✅ Live" labels below as "spec-complete." They mean "runs without error." The scoring axes run but return materially wrong numbers until Phase 2b lands — see the audit in [README.md](./README.md).

---

## What Was Already Shipped (orchestrator)

| Component | File | Status | Caveat |
|---|---|---|---|
| Language detection | `orchestrator/app/lang_detect.py` | ✅ Runs | Detects `ar-TN/fr/other`; Derja→FR translate helper exists but isn't invoked in the intake path yet |
| Adaptive questionnaire | `intake/questionnaire.py` + `branches.json` | ✅ Runs | Sector enum aligned with profile model |
| State router (DB-backed) | `state_router.py` | ✅ Runs | — |
| Diagnostic 3-wave runner | `diagnostic/runner.py` | ✅ Runs | Sends `prior_outputs` to Axis 04 which currently drops it (Phase 2b defect 4) |
| Results aggregator | `diagnostic/aggregator.py` | 🟡 Runs | Ranks `blockers` that **no axis emits yet** (Phase 2b defect 2); dedupe anomalies (defect 5) |
| SSE infrastructure | `sse.py` | ✅ Runs | — |
| LangGraph state model | `graph/state.py` | ✅ Defined | TypedDict only; no graph nodes wired (see item 6) |
| Axis 01 maturity classifier | `services/ideation-service/app/main.py` | ✅ Runs | Correct per spec |
| Grounded chat endpoint | `main.py` `/api/v1/chat` | ✅ Runs | — |
| Tier 1 eval runner | `eval/tier1-maturity/run_eval.py` | ✅ Exists | Dataset only 15/50 vignettes (item 5) |

---

## What Remains

### 1. Redis Consumer (Orchestrator)

**File to create:** `orchestrator/app/redis_consumer.py`

**What it does:** A background async task that subscribes to the `moufida:metrics` Redis channel and, on every message, forwards the payload to the correct axis's `/metric_update` endpoint using the routing table in `axis_registry.METRIC_ROUTES`.

**Message schema (from daemon):**
```json
{
  "project_id": "uuid",
  "type": "competitor | budget | legal | milestone | trend",
  "value": { ... },
  "timestamp": "ISO8601"
}
```

**Routing table (from `axis_registry.py`):**
```python
METRIC_ROUTES = {
    "competitor": ["market"],
    "budget": ["business-model"],
    "legal": ["legal"],
    "milestone": ["ideation", "gtm"],
    "trend": ["market"],
}
```

**Implementation steps:**
1. Add `asyncio`-based Redis subscriber using `redis.asyncio` (already in orchestrator deps).
2. On each message: parse JSON, look up `type` in `METRIC_ROUTES`, call `POST <axis_host(slug)>/metric_update` with the full message as body.
3. Register as a FastAPI lifespan background task in `orchestrator/app/main.py`.
4. Silently log and continue on network errors from individual axes (never crash the consumer).

**Wire-up in `main.py`:**
```python
from contextlib import asynccontextmanager
from . import redis_consumer

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(redis_consumer.consume())
    yield
    task.cancel()

app = FastAPI(title="Moufida Orchestrator", lifespan=lifespan)
```

---

### 2. Marketing & Sales Diagnose Endpoints

**Files to update:**
- `services/marketing-service/app/main.py`
- `services/sales-service/app/main.py`

Both currently return `{"status": "not_implemented"}`. They need lightweight scoring logic — no Affinitree dependency, just a readiness check.

**Marketing service (`/diagnose`):** Returns a `marketing_readiness` score (0–1) based on presence of profile fields:
- `offer.brand_name_registered` → brand registered
- `offer.logo_exists` → visual identity exists
- `market.mrr_usd > 0` → revenue-generating (has a real product to market)
- Derive a simple weighted average; include a `gaps` list for missing fields.
- Return: `{"axis": 7, "marketing_readiness": float, "gaps": list[str]}`

**Sales service (`/diagnose`):** Returns a `sales_readiness` score (0–1):
- `market.paid_pilots_count > 0` → paying customers exist
- `market.customer_interviews_count > 0` → discovery done
- `finance.cac_usd > 0` → acquisition cost tracked
- Same pattern: weighted sum + gaps list.
- Return: `{"axis": 8, "sales_readiness": float, "gaps": list[str]}`

These scores are secondary inputs: the aggregator will surface their `gaps` as `info`-severity blockers.

---

### 3. Natural-Language Score Justification

**Where to add it:** In each live axis service after Affinitree returns the breakdown — or centrally in the aggregator.

**What it is:** A single LLM call that turns the score breakdown into 2–3 plain-language sentences explaining what drove the result, written in the user's language.

**Approach:**
- After Affinitree returns the `explanation` tree, build a compact prompt listing the top 2 contributors and the top 1 gap (lowest-contribution sub-dimension).
- Call Ollama `llama3.1:8b` with `"stream": false`.
- Return the justification as a `"justification"` field alongside the score.
- Language: default French. Wire language through the `profile.language` field.

**Example prompt (market score):**
```
You are an entrepreneurship advisor. Based on these scoring results, write 2-3 sentences 
explaining the Market Score of 0.75/5 in plain French. Focus on the main strengths and 
the most critical gap. 
Strengths: customer_validation (contribution 0.45). 
Gaps: addressable_market_size (contribution 0.0) — no SAM/TAM data provided.
Be specific. Do not give generic advice.
```

Add `justification: str | None` to the service response and to the `score_breakdowns` dict in the aggregator.

---

### 4. Improvement Guidance Per Score

**Where:** In `orchestrator/app/diagnostic/aggregator.py`, add a `recommendations` field.

**What it is:** For each score, identify the highest-weight sub-dimension with a low contribution and suggest the single most impactful action.

**Implementation:** Hard-coded action templates keyed by `(score_name, sub_dimension_id)` — no LLM needed here, this is rule-based. Examples:

```python
GUIDANCE = {
    ("market", "addressable_market_size"): "Conduct a TAM/SAM/SOM analysis to size your market.",
    ("market", "customer_validation"): "Run at least 5 structured customer interviews.",
    ("commercial_offer", "value_proposition_clarity"): "Write a one-sentence value proposition using the Jobs-to-be-Done framework.",
    ("innovation", "product_novelty"): "Document your TRL level and any IP protection steps taken.",
    ("scalability", "unit_economics"): "Calculate your CAC, LTV, and payback period from current data.",
    ("green", "sdg_alignment"): "Map your project to 2-3 UN SDGs and write a one-paragraph alignment rationale.",
}
```

Add `"recommendations": list[{"score_name", "sub_dimension", "action"}]` to the aggregator output.

---

### 5. Tier 1 Evaluation Dataset Completion

**File:** `eval/tier1-maturity/vignettes.json`

**Current state:** 15 vignettes exist with keys `id`, `source`, `text`, `gold_label`, `annotator_labels`, `notes`.

**Target:** 50 vignettes (6 stages × ~8 vignettes minimum, distributed across all stages).

**Current distribution check:**
```bash
python3 -c "
import json
v = json.load(open('eval/tier1-maturity/vignettes.json'))
from collections import Counter
print(Counter(x['gold_label'] for x in v))
"
```

**To reach 50:** Add 35 more vignettes covering all six stages (Ideation, Market Validation, Structuration, Fundraising, Launch Planning, Growth). Sources:
- Synthetic: prompt `llama3.1:8b` with "generate a 200-word startup description at the [STAGE] stage" for each stage
- Real: ANAVA case studies, Startup Tunisia profiles
- Each vignette needs `annotator_labels` with at least 2 entries (can be the same human and the model's output)

**Run the eval after completion:**
```bash
cd eval/tier1-maturity
pip install -r requirements.txt
python run_eval.py --url http://localhost:8101 --kappa
```

---

## Verification Checklist

- [ ] `POST http://localhost:8001/api/v1/project/new` → `{"project_id": "...", "mode": "STATE_NEW"}`
- [ ] `POST http://localhost:8001/api/v1/intake/start {"language":"fr"}` → first question returned
- [ ] `POST http://localhost:8001/api/v1/project/{id}/run-diagnostic` → all 5 scores + maturity stage
- [ ] Docker logs for orchestrator show no `redis_consumer` errors when daemon publishes
- [ ] Marketing/sales diagnose return `{"marketing_readiness": float, "gaps": [...]}`
- [ ] Score responses include `"justification": "..."` text
- [ ] Aggregator response includes `"recommendations": [...]`
- [ ] Tier 1 eval: `python run_eval.py` prints macro-F1 ≥ 0.65
