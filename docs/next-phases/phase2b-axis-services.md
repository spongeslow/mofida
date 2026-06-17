# Phase 2b — Axis Service Correctness (FIX FIRST)

**Goal:** Make the five "live" scoring services actually correct per spec. Today they run and return a number, but three of the five numbers are **wrong** (rubric text fields silently score 0), no service emits **blockers** (a mandatory PRD feature), and anomalies are duplicated 5× by the aggregator.

**Why this is first:** Every downstream phase (roadmap, dashboard, evaluation) consumes these scores and blockers. Building the frontend on top of silently-wrong scores wastes effort and produces a misleading demo.

**Prerequisites:** Stack runs (`docker compose up`), Ollama reachable.

---

## The Five Defects

| # | Defect | Affected | Severity | PRD impact |
|---|---|---|---|---|
| 1 | Rubric text fields never scored → contribute 0 | Axes 03, 04, 06 | 🔴 Critical | Scores wrong by ~40% (03, 04) |
| 2 | No axis emits `blockers` | All scoring axes | 🔴 Critical | Feature 1 "blocker identification" dead |
| 3 | No deterministic financial engine | Axis 05 | 🟠 High | CAC/LTV/payback/runway never computed |
| 4 | `prior_outputs` sent to Axis 04 but ignored | Axis 04 | 🟡 Medium | Innovation data-flow contract broken |
| 5 | Each axis returns the global anomaly list → 5× duplication | Aggregator | 🟡 Medium | Dashboard shows each anomaly 5 times |

---

## Defect 1 — Rubric Text Fields Score 0

### Evidence

- `scoring-engine/affinitree/scorer.py` resolves `rubric:`-prefixed inputs via `profile.rubric_scores.get(field_path, 0)` — **default 0**.
- The configs depend on these inputs:
  - `commercial_offer.json`: `rubric:offer.value_prop_text`, `rubric:offer.differentiation_text`
  - `innovation.json`: `rubric:innovation.brand_distinctiveness_text`, `rubric:innovation.novelty_text`, `rubric:offer.value_prop_text`
  - `green.json`: `rubric:legal.sdg_alignment_text`
- The rubric scorer (`affinitree/rubric.py::score_profile_text_fields`) populates `profile.rubric_scores` — **but no axis service calls it.**
- `rubric` and `OllamaClient` are **not exported** from `affinitree/__init__.py`, so services can't even reach them via the public import.

### Impact (weight that silently zeroes out)

- **Commercial Offer:** value-prop clarity + differentiation ≈ **40–50%** of the score → 0.
- **Innovation:** brand distinctiveness (20%) + value-creation novelty (20%) ≈ **40%** → 0.
- **Green:** SDG alignment sub-dimension → 0.

### Fix

**Step A — export the rubric API.** In `scoring-engine/affinitree/__init__.py`:
```python
from .rubric import OllamaClient, score_profile_text_fields, RUBRICS
# add the three names to __all__
```

**Step B — score text fields before the numeric score, in each affected service.**
Pattern for `product-offering-service`, `brand-innovation-service`, `legal-compliance-service`:

```python
import os
from affinitree import StartupProfile, score as affinitree_score
from affinitree import OllamaClient, score_profile_text_fields

# Module-level client; reads OLLAMA_BASE_URL + OLLAMA_MODEL from env (fail-fast).
_RUBRIC_CLIENT = OllamaClient(
    model=os.environ["OLLAMA_MODEL"],
    base_url=os.environ["OLLAMA_BASE_URL"],
)

@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    profile = StartupProfile(**req.profile)
    # Populate profile.rubric_scores so the deterministic scorer reads real values.
    score_profile_text_fields(profile, _RUBRIC_CLIENT)   # NEW
    result = affinitree_score(profile, "commercial_offer")
    ...
```

**Step C — graceful degradation.** If Ollama is unreachable, `score_field` should not crash the diagnose call. Wrap `score_profile_text_fields` in a try/except that logs a warning and leaves `rubric_scores` empty (scores degrade to the current behaviour rather than 500). Add `degraded_rubric: true` to the response so the dashboard can flag it.

**Step D — make rubric scoring observable.** Return the rubric detail (score + evidence_quote + reasoning per field) in the diagnose response under `rubric_detail`, so the dashboard's expandable score panel and the natural-language justifier can cite the quote.

**Note on Axis 05/09 (Scalability) and Axis 02 (Market):** these have **no** rubric inputs, so they are already correct and need no rubric call. Don't add the client to them.

### Acceptance

```bash
# With a value-prop text present, commercial_offer must exceed the all-zero-text baseline.
curl -s -X POST localhost:8103/diagnose -H 'content-type: application/json' -d '{
  "profile": {"offer": {"value_prop_text": "We cut SME invoice-processing time by 80% using OCR, validated with 12 paying clients.",
                        "differentiation_text": "Only solution integrated with the Tunisian e-facture standard."}}
}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('score:', d['score']); print('rubric:', d.get('rubric_detail'))"
# Expect score > 0 and rubric_detail showing non-zero integers with evidence quotes.
```

---

## Defect 2 — No Blockers Emitted (Mandatory PRD Feature)

### Evidence

- `orchestrator/app/diagnostic/aggregator.py` reads `out.get("blockers")` from each axis and ranks them.
- **No service returns a `blockers` key.** They return `missing_fields` + `anomalies` only.
- Result: `aggregator.blockers` is always `[]`; the dashboard `BlockerList` will always be empty; PRD Feature 1 "detect and rank priority blockers" is unmet.

### Fix

Add a small, deterministic blocker derivation to each scoring axis. A blocker is produced when (a) a required field is missing, or (b) a sub-dimension's normalised value is below a threshold. Keep it rule-based (no LLM).

**Shared helper** — add `scoring-engine/affinitree/blockers.py`:
```python
from .scorer import ScoreResult

# (score_name, sub_dimension_id) -> (human description, remediation)
BLOCKER_RULES = {
    ("market", "customer_validation"):
        ("No customer validation evidence.", "Run at least 5 structured customer interviews."),
    ("market", "addressable_market_size"):
        ("Market size not quantified.", "Estimate TAM/SAM/SOM with a bottom-up model."),
    ("commercial_offer", "value_proposition_clarity"):
        ("Value proposition unclear.", "State problem, segment, and a measurable benefit in one sentence."),
    ("scalability", "unit_economics"):
        ("Unit economics not established.", "Compute CAC, LTV, and payback period."),
    ("scalability", "funding_readiness"):
        ("Funding readiness low / short runway.", "Extend runway or prepare a fundraising package."),
    ("green", "sdg_alignment"):
        ("SDG alignment not articulated.", "Map the venture to 2-3 specific UN SDGs."),
    # ... one entry per low-leverage sub-dimension
}

LOW_THRESHOLD = 0.34  # normalised vi below this raises a blocker

def derive_blockers(result: ScoreResult, axis_slug: str) -> list[dict]:
    out = []
    for c in result.components:
        rule = BLOCKER_RULES.get((result.score_name, c.name))
        if rule and c.raw_value < LOW_THRESHOLD:
            desc, remediation = rule
            out.append({
                "axis": axis_slug,
                "code": f"{result.score_name}.{c.name}.low",
                "description": desc,
                "severity": "critical" if c.weight >= 0.30 else "warning",
                "score_dimension": result.score_name,
                "remediation": remediation,
            })
    for mf in result.missing_fields:
        out.append({
            "axis": axis_slug, "code": f"missing.{mf}",
            "description": f"Required field not provided: {mf}.",
            "severity": "info", "score_dimension": result.score_name,
            "remediation": f"Provide {mf} during intake.",
        })
    return out
```

Export it from `affinitree/__init__.py`, then in each scoring axis:
```python
from affinitree import derive_blockers
...
return {
    "axis": AXIS, "score_name": "market", "score": result.score,
    "explanation": result.explanation_tree(),
    "missing_fields": result.missing_fields,
    "blockers": derive_blockers(result, SLUG),   # NEW
}
```

The aggregator already ranks by severity — once axes emit blockers, `BlockerList` populates with no aggregator change required (but verify its severity keywords still apply).

### Acceptance

```bash
curl -s -X POST localhost:8102/diagnose -d '{"profile":{}}' -H 'content-type: application/json' \
 | python3 -c "import sys,json; print(json.load(sys.stdin)['blockers'])"
# Expect a non-empty list including a 'market.customer_validation.low' or missing-field blocker.
```

---

## Defect 3 — Axis 05 Has No Deterministic Financial Engine

### Evidence

Spec §3.2.5 requires Axis 05 to "use a deterministic financial engine (pure Python) to calculate exact numbers" — CAC, LTV, payback period, runway, burn rate — and return **financial blockers** (e.g., "negative unit economics", "runway < 6 months"). The current service only calls `affinitree_score(profile, "scalability")`.

### Fix

Add `services/business-model-service/app/finance.py`:
```python
def compute_financials(profile: dict) -> dict:
    f = profile.get("finance", {})
    cac = f.get("cac_usd")
    ltv = f.get("ltv_usd")
    burn = f.get("burn_rate_usd")
    runway = f.get("runway_months")

    ltv_cac_ratio = (ltv / cac) if (cac and ltv and cac > 0) else None
    payback_months = (cac / (ltv / 12)) if (cac and ltv and ltv > 0) else None

    blockers = []
    if ltv_cac_ratio is not None and ltv_cac_ratio < 1:
        blockers.append({"code": "negative_unit_economics", "severity": "critical",
                         "description": f"LTV/CAC = {ltv_cac_ratio:.2f} (< 1).",
                         "remediation": "Reduce CAC or raise LTV before scaling spend."})
    if runway is not None and runway < 6:
        sev = "critical" if runway < 3 else "warning"
        blockers.append({"code": "short_runway", "severity": sev,
                         "description": f"Runway is {runway} months.",
                         "remediation": "Extend runway via revenue, cost cuts, or financing."})
    return {"ltv_cac_ratio": ltv_cac_ratio, "payback_months": payback_months,
            "blockers": blockers}
```

In the service's `/diagnose`, merge `compute_financials(req.profile)["blockers"]` into the blocker list and surface the computed metrics under a `financials` key. These deterministic numbers also feed the natural-language justification (phase2-completion).

### Acceptance

```bash
curl -s -X POST localhost:8105/diagnose -d '{"profile":{"finance":{"cac_usd":100,"ltv_usd":50,"runway_months":2}}}' \
 -H 'content-type: application/json' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['financials']); print([b['code'] for b in d['blockers']])"
# Expect ltv_cac_ratio≈0.5, and blockers include negative_unit_economics + short_runway(critical).
```

---

## Defect 4 — Axis 04 Ignores `prior_outputs`

### Evidence

`orchestrator/app/diagnostic/runner.py` sends Axis 04 (brand):
```python
body = {"profile": profile, "prior_outputs": {dep: axis_outputs.get(dep) for dep in ("ideation","market","product")}}
```
But `brand-innovation-service` defines `DiagnoseRequest(profile: dict)` only — `prior_outputs` is silently dropped. Spec §4.3 requires Axis 04 to consume Axes 01/02 outputs (TRL, IP status, competitor count) when assembling the Innovation Score.

### Fix

In practice TRL/IP/competitor_count already live on the StartupProfile, so the *score* may be unaffected — but the contract should be honoured and the data used for evidence/justification. Update the request model and use prior outputs to (a) confirm competitor_count, (b) enrich the justification, (c) raise a blocker if Axis 02 flagged missing competitor data:

```python
class DiagnoseRequest(BaseModel):
    profile: dict
    prior_outputs: dict = {}

@app.post("/diagnose")
def diagnose(req: DiagnoseRequest):
    profile = StartupProfile(**req.profile)
    score_profile_text_fields(profile, _RUBRIC_CLIENT)   # defect 1 fix
    result = affinitree_score(profile, "innovation")
    blockers = derive_blockers(result, SLUG)
    # Use prior market output to add an evidence note / blocker:
    market_out = req.prior_outputs.get("market") or {}
    if (req.profile.get("market", {}).get("competitor_count") is None):
        blockers.append({"axis": SLUG, "code": "innovation.market_novelty.no_competitor_data",
                         "severity": "warning", "score_dimension": "innovation",
                         "description": "Competitor count unknown — market-novelty confidence reduced.",
                         "remediation": "Complete the market competitor analysis (Axis 02)."})
    return {"axis": AXIS, "score_name": "innovation", "score": result.score,
            "explanation": result.explanation_tree(),
            "missing_fields": result.missing_fields, "blockers": blockers}
```

### Acceptance

Posting to `localhost:8104/diagnose` with a `prior_outputs` block returns HTTP 200 (no validation error) and, when competitor data is absent, includes the `no_competitor_data` blocker.

---

## Defect 5 — Anomaly Duplication (5×)

### Evidence

Every scoring axis calls `detect(profile)` on the **whole** profile and returns the **complete** anomaly list. The aggregator does `anomalies.extend(out.get("anomalies"))` over all 5 axes → each anomaly appears up to 5 times.

### Fix (choose one — Option A preferred)

**Option A (preferred): compute anomalies once in the aggregator.**
- Remove the per-axis `detect(profile)` calls and the `anomalies` key from every axis `/diagnose` response.
- In `orchestrator/app/diagnostic_router.py`, after loading the profile, call `detect()` once. This needs the affinitree library available to the orchestrator (it already installs it in its Dockerfile) and the raw profile (already loaded). Add `anomalies = [a.to_dict() for a in detect(StartupProfile(**profile))]` and merge into the aggregated result.

**Option B (minimal): de-duplicate in the aggregator.**
- Keep per-axis anomalies but dedupe by `code` in `aggregate_results`:
  ```python
  seen = set(); deduped = []
  for a in anomalies:
      if a["code"] not in seen:
          seen.add(a["code"]); deduped.append(a)
  ```

Option A is cleaner (anomalies are a profile-level property, not an axis-level one) and removes redundant work from 5 services.

### Acceptance

```bash
# Run a diagnostic on a profile with one known contradiction; the result's
# anomalies list must contain that code exactly once.
```

---

## Service-by-Service Summary (after Phase 2b)

| Service | Port | Current | After Phase 2b |
|---|---|---|---|
| ideation (01) | 8101 | ✅ maturity classifier | unchanged (execute stub → Phase 4) |
| market (02) | 8102 | 🟡 score ok, no blockers, dup anomalies | ✅ + blockers, anomalies removed |
| product (03) | 8103 | 🟡 rubric=0, no blockers | ✅ rubric scored + blockers |
| brand (04) | 8104 | 🟡 rubric=0, ignores prior_outputs | ✅ rubric + prior_outputs + blockers |
| business-model (05) | 8105 | 🟡 no financial engine | ✅ financial engine + blockers |
| legal (06) | 8106 | 🟡 SDG rubric=0 | ✅ rubric scored + blockers |
| marketing (07) | 8107 | ⏳ stub | readiness score → **phase2-completion** |
| sales (08) | 8108 | ⏳ stub | readiness score → **phase2-completion** |
| operations (09) | 8109 | 🟡 score ok, no blockers | ✅ + blockers |
| gtm (10) | 8110 | ⏳ stub | roadmap → **phase3** |

---

## Phase 2b Completion Criteria

- [ ] `affinitree/__init__.py` exports `OllamaClient`, `score_profile_text_fields`, `derive_blockers`
- [ ] Axes 03/04/06 call `score_profile_text_fields` and return non-zero scores for populated text fields
- [ ] Rubric failure (Ollama down) degrades gracefully with `degraded_rubric: true`, no 500
- [ ] Every scoring axis (02,03,04,05,06,09) returns a non-empty `blockers` list on a sparse profile
- [ ] Axis 05 returns a `financials` block with `ltv_cac_ratio` and `payback_months`
- [ ] Axis 04 accepts `prior_outputs` without validation error
- [ ] A diagnostic run shows each anomaly exactly once (no duplication)
- [ ] Existing Tier 2a determinism (`run_eval.py --determinism`) still 100% (rubric uses fixed seeds; numeric path unchanged)
