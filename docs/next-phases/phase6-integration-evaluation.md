# Phase 6 — Integration, Evaluation & Submission

> 📍 Plan order: last. Gates the submission. See [README](./README.md). Note Tier 2b/2c and Tier 1/3 scores are only meaningful **after** Phase 2b fixes the rubric scoring — re-run them once 2b lands.

**Goal:** Both end-to-end flows (STATE_NEW and STATE_EXISTING) work completely on a real machine. All three evaluation tiers pass their targets. A structured results card is ready for the hackathon submission.

**Prerequisites:** Phases 2–5 complete.

---

## 6.1 End-to-End Integration Testing

### Flow A — STATE_EXISTING (Priority: Demo Critical)

This is the primary hackathon demo flow. It must work flawlessly.

**Steps to verify manually:**

1. `docker compose up` — all 17 containers healthy.
2. `cd frontend && npm run tauri dev` — tray icon appears.
3. Say "Hey Moufida" — HUD overlay opens (or click "Diagnostiquer" from tray).
4. Answer the adaptive intake questionnaire (5–10 questions, branching by sector).
5. The orchestrator calls `/run-diagnostic` — 3-wave pass completes.
6. Dashboard populates:
   - **MaturityCard**: stage assigned, confidence %, evidence list
   - **5 ScoreGauges**: all non-zero, sub-dimension breakdown visible
   - **BlockerList**: at least 1 critical or warning blocker
   - **RoadmapTimeline**: at least 3 action cards with real resource links
7. Wait for the Go daemon's next tick (can shorten cadences during testing — see below).
8. Daemon publishes a `competitor` metric → orchestrator routes to Axis 02 → Axis 02 re-scores → SSE `alert` event → AlertFeed shows notification → TTS reads it aloud.
9. "Mon Parcours" view — run diagnostic a second time with slightly different answers → ScoreChart shows 2 data points per score.

**Shorten daemon intervals for testing:** Add env vars:
```
BUDGET_INTERVAL=30s
COMPETITOR_INTERVAL=60s
LEGAL_INTERVAL=120s
MILESTONE_INTERVAL=30s
TREND_INTERVAL=300s
```
And read them in `daemon/cmd/main.go` via `os.Getenv` with real cadences as fallbacks.

### Flow B — STATE_NEW (Nice-to-have for demo)

1. Click "Nouveau projet" from tray.
2. Axis 01 (Ideation) calls `/execute` → returns brainstorming output + feasibility.
3. ReviewCard appears → click "Approuver".
4. Orchestrator advances to Axis 02 (Market Research) → `/execute` returns market analysis.
5. Continue through all 10 axes.
6. At the end: complete StartupProfile is persisted in PostgreSQL.
7. User can transition to STATE_EXISTING diagnostic from the same project.

**Note:** The 10 `execute` endpoints are all stubs returning `{"status": "not_implemented"}`. For the hackathon, STATE_EXISTING is sufficient. If time permits, implement Axes 01 and 02 `execute` endpoints with actual LLM prompts.

### Derja Input Path

1. Enable Arabic input in settings (or type in Derja text in the ChatPanel text input).
2. `lang_detect` classifies as `ar-TN`.
3. `translate_derja_to_french()` translates using Llama 3.1.
4. French translation is used for rubric scoring.
5. Both original Derja text and French translation stored in profile.
6. Response from Moufida delivered in French (TTS).

**Verification:** The profile JSONB in PostgreSQL must contain both `original_text` and `translated_text` fields for any Derja input.

---

## 6.2 Tier 1 Evaluation — Maturity Classifier

**Target:** macro-F1 ≥ 0.65, top-2 accuracy ≥ 0.85, Cohen's κ ≥ 0.65.

**Prerequisites:**
- `eval/tier1-maturity/vignettes.json` must have ≥ 50 vignettes with `gold_label` and `annotator_labels`.
- `services/ideation-service` must be running with Ollama available.

### Run

```bash
cd eval/tier1-maturity
pip install -r requirements.txt
python run_eval.py --url http://localhost:8101 --kappa
```

### If F1 < 0.65

- Check distribution: are some stages never predicted?
- Inspect the prompt in `services/ideation-service/app/main.py` — `PROMPT_TEMPLATE`. Add more explicit stage definitions.
- Add few-shot examples of each stage to the prompt.
- Re-run eval.

### Reporting Fields

```
Tier 1 Results:
  Dataset: 50 vignettes (17 published case studies, 15 partner incubator, 18 synthetic)
  Annotators: [domain expert name], [team member], Axis 01 model (as 3rd annotator)
  Cohen's κ (human-human): X.XX
  Macro-F1: X.XX  (target: ≥ 0.65)
  Top-2 Accuracy: X.XX  (target: ≥ 0.85)
  Stage distribution: Ideation N, Market Validation N, ...
```

---

## 6.3 Tier 2 Evaluation — Affinitree Stability

All three sub-tests run from the existing `eval/tier2-affinitree/run_eval.py`.

### Tier 2a — Determinism

```bash
cd eval/tier2-affinitree
python run_eval.py --determinism
```

Expected: **100%** (already passing from Phase 1). Re-run to confirm nothing regressed.

### Tier 2b — Text-Field Stability (Requires Live Ollama)

```bash
python run_eval.py --text-stability --ollama-url http://localhost:11434
```

Runs the 5 rubric fields × 5 runs each and reports σ per field.

**Target:** σ ≤ 0.15 for all fields. If any field exceeds this:
1. Check `scoring-engine/affinitree/rubric.py` — ensure the median-on-divergence logic is active.
2. Tighten the rubric prompt for that field (add more specific descriptors for each 0–4 level).
3. Re-run until stable.

### Tier 2c — Anomaly Recall

```bash
python run_eval.py --anomaly
```

Expected: **100%** (10/10, already passing from Phase 1). Re-run to confirm.

### Reporting Fields

```
Tier 2 Results:
  T2a Determinism: 100% (3 profiles × 5 scores × 10 runs)
  T2b Text stability:
    value_prop_text: σ = X.XX
    differentiation_text: σ = X.XX
    novelty_text: σ = X.XX
    brand_distinctiveness_text: σ = X.XX
    sdg_alignment_text: σ = X.XX
    All fields: PASS / FAIL
  T2c Anomaly recall: 10/10 = 100%
```

---

## 6.4 Tier 3 Evaluation — RAG Retrieval Quality

**Prerequisites:** Knowledge base ingested (≥ 60 resources in Qdrant), `eval/tier3-rag/query_pairs.json` exists with 20 pairs.

```bash
cd eval/tier3-rag
python run_eval.py --url http://localhost:8300
```

**Target:** Recall@3 ≥ 0.80, MRR ≥ 0.70.

### If Recall@3 < 0.80

Likely causes and fixes:
1. **Too few resources in the filtered set** — check pre-filter is not over-restricting. Try relaxing stage filter to allow adjacent stages.
2. **Embedding model mismatch** — ensure all resources were ingested with the same `nomic-embed-text` model version currently running.
3. **BM25 corpus too small** — BM25 needs enough documents to rank well. Try increasing top-k in the hybrid step.
4. **Sector boost drowning out relevance** — reduce boost from 1.3 to 1.1 and re-run.

### If MRR < 0.70

The expected resource is found but not ranked first. Check if sector boost and RRF weights are calibrated correctly. Try giving more weight to the dense retrieval path.

### Reporting Fields

```
Tier 3 Results:
  Dataset: 20 (query, expected-resource) pairs
  Coverage: 6 stages × 5 resource types (at least 1 pair per cell)
  Recall@3: X.XX  (target: ≥ 0.80)
  MRR:      X.XX  (target: ≥ 0.70)
  Failing queries (if any): [list with diagnosis]
```

---

## 6.5 Results Card

**File to create:** `docs/evaluation-results.md`

Structure:

```markdown
# Moufida — Evaluation Results Card

**Team Makrouna Kadheba** | Hackathon June 2026

## Dataset Construction

### Tier 1 — Maturity Vignettes
- Total: 50 vignettes
- Sources: X published (ANAVA/Startup Tunisia), Y incubator (2 partners), Z synthetic
- Annotators: [names/roles]
- Labelling protocol: independent labelling by 2 humans, majority class with model as tiebreaker
- Cohen's κ: X.XX (target ≥ 0.65) → PASS / FAIL

### Tier 2 — Affinitree Test Profiles
- T2a: 3 structured profiles × 5 scores × 10 runs
- T2b: 5 text-field profiles × 5 rubric runs each
- T2c: 10 hand-crafted contradictory profiles

### Tier 3 — RAG Query Pairs
- 20 (query, expected-resource) pairs
- Created by: [domain expert annotation]
- Coverage: all 6 stages, all 5 resource types

## Results

| Tier | Metric | Target | Result | Status |
|---|---|---|---|---|
| T1 | Macro-F1 | ≥ 0.65 | X.XX | ✅ / ❌ |
| T1 | Top-2 Accuracy | ≥ 0.85 | X.XX | ✅ / ❌ |
| T1 | Cohen's κ | ≥ 0.65 | X.XX | ✅ / ❌ |
| T2a | Determinism | 100% | 100% | ✅ |
| T2b | σ (text fields) | ≤ 0.15 | max σ = X.XX | ✅ / ❌ |
| T2c | Anomaly recall | 100% | 100% | ✅ |
| T3 | Recall@3 | ≥ 0.80 | X.XX | ✅ / ❌ |
| T3 | MRR | ≥ 0.70 | X.XX | ✅ / ❌ |

## Limitations & Mitigations

[For any missed target: diagnosis + what was tried]
```

---

## 6.6 Known Limitations Disclosure

Document these in the onboarding screen (first launch modal):

1. **Derja voice output not supported.** Moufida cannot generate fluent Tunisian dialect speech. All voice responses are in French (or MSA when Arabic is selected). This is a deliberate product decision — Llama 3.1's Derja generation is unreliable.

2. **Whisper STT accuracy on heavy Derja.** Standard Whisper large-v2 achieves WER ~25–40% on Tunisian Arabic. For best results, use French or speak clearly.

3. **Knowledge base currency.** Tunisian support programmes change frequently. Resources verified as of June 2026; the Go daemon flags stale resources but cannot update them automatically. Manual re-verification is required.

4. **LLM maturity classification.** The Axis 01 maturity classifier uses `llama3.1:8b`. On borderline cases (e.g., late Market Validation vs. early Structuration), confidence may be below 0.5. The perception gap feature helps surface these ambiguous cases.

5. **Rubric scoring variance.** Free-text fields (value proposition, novelty, etc.) are scored by `llama3.1:8b` with a rubric. The median-on-divergence logic reduces variance (σ ≤ 0.15 target), but scores may shift slightly between runs. Numeric fields are fully deterministic.

---

## 6.7 Final Pre-Submission Checklist

### Infrastructure
- [ ] `docker compose up --build` — all 17 containers healthy, no errors in logs
- [ ] `.env.example` has all keys (no values) — nothing sensitive committed
- [ ] `git log --oneline -20` — clean commit history, no debug commits
- [ ] `scripts/setup.sh` runs end-to-end without error on a clean machine

### Backend
- [ ] `curl http://localhost:8001/health` → `{"status":"ok"}`
- [ ] All 13 service health checks return 200
- [ ] `POST /api/v1/project/new` → project created in DB
- [ ] `POST /api/v1/project/{id}/run-diagnostic` → all 5 scores + maturity stage + roadmap
- [ ] `GET /api/v1/project/{id}/history` → score time series
- [ ] SSE stream emits events on diagnostic completion
- [ ] Redis consumer routes daemon metrics to axis services

### Frontend
- [ ] `npm run tauri dev` opens desktop app with tray icon
- [ ] Dashboard renders after diagnostic: MaturityCard, 5 ScoreGauges, BlockerList, RoadmapTimeline
- [ ] Mon Parcours shows score chart with ≥ 2 time points
- [ ] AlertFeed shows daemon alerts within 5 seconds
- [ ] Language toggle works (FR ↔ EN)
- [ ] Source links open in system browser

### Evaluation
- [ ] Tier 1: `python eval/tier1-maturity/run_eval.py` → macro-F1 printed
- [ ] Tier 2a: `python eval/tier2-affinitree/run_eval.py --determinism` → 100%
- [ ] Tier 2c: `python eval/tier2-affinitree/run_eval.py --anomaly` → 10/10
- [ ] Tier 3: `python eval/tier3-rag/run_eval.py` → Recall@3 and MRR printed
- [ ] `docs/evaluation-results.md` filled with actual numbers

### Documentation
- [ ] `README.md` setup instructions accurate (test on clean machine)
- [ ] `docs/evaluation-results.md` complete
- [ ] Known limitations documented in onboarding modal

---

## Phase Summary Table (Full Project)

| Phase | Scope | Key Deliverable | Status |
|---|---|---|---|
| 0 | Infrastructure & scaffolding | Full stack boots | ✅ Complete |
| 1 | Affinitree scoring library | All 5 scores; Tier 2a/2c pass | ✅ Complete |
| 2 | Adaptive intake & diagnostic engine | STATE_EXISTING diagnostic returns all 5 scores | ✅ Core runs; orchestrator items remain |
| 2b | Axis service correctness | Rubric scoring, blockers, financial engine, anomaly dedup | ❌ **Fix first** — 3/5 scores wrong today |
| 3 | Knowledge base & RAG service | Axis 10 generates traceable roadmap; Tier 3 eval | ❌ Not started |
| 4 | Voice pipeline & frontend | Desktop app fully interactive | ❌ Not started |
| 5 | Go daemon & liveness | Scores update autonomously from real-world signals | ❌ Not started |
| 6 | Integration, evaluation & submission | All Tier 1–3 targets met; results card | ❌ Not started |
