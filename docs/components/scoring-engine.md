# Scoring Engine — Affinitree

**Location:** `backend/scoring-engine/` | **Port:** 8200 (standalone API, also used in-process by axis services)  
**Stack:** Python 3.12, pydantic v2 — no database or network dependencies

Affinitree is a deterministic, explainable scoring library. Every formula, weight, and normalisation function is defined in JSON config files with inline academic citations. There is no randomness, no neural network, and no floating-point non-determinism.

---

## The Scoring Formula

Each sub-dimension contribution:

```
cᵢ = wᵢ × vᵢ × mᵢ
```

- `wᵢ` — sub-dimension weight (from axis config JSON)
- `vᵢ` — normalised value (after applying a normaliser to the raw profile field)
- `mᵢ` — **evidence tier multiplier** (T1 declared = 0.6, T2 artefact = 1.0, T3 daemon-observed = 1.2)

The composite score is the weighted sum of all `cᵢ`, scaled to [0, 5].

## Evidence Tiers

| Tier | Multiplier | Source |
|---|---|---|
| T1 — Declared | 0.6× | Founder self-reported in intake |
| T2 — Artefact-backed | 1.0× | Uploaded document, Notion page |
| T3 — Daemon-observed | 1.2× | GitHub commit data, Google Analytics, competitor monitor |

Tool integrations auto-upgrade tiers: connecting GitHub upgrades `ops.engineering_velocity` to T3. A founder who self-reports strong engineering scores lower than one whose GitHub shows 200 commits last month — evidence quality is a first-class concern in the scoring model.

## Normalisation Functions

| Function | Use case |
|---|---|
| `saturating(max)` | Values that plateau — e.g., team size: 1→0.2, 5+→1.0 |
| `ordinal_map(mapping)` | Discrete categories — e.g., revenue model: "none"→0.0, "subscription"→0.8 |
| `inverse_log_density(...)` | Competitive intensity — more competitors → lower score |

The formula evaluator uses AST parsing with a strict arithmetic whitelist (no `eval`). Config files are safe to edit.

## Text Field Pre-Scoring

Free-text profile fields (value proposition, differentiation, problem statement) are pre-scored via Ollama before the formula runs. Each field maps to a structured rubric:

```
"value_proposition": "Score 0–4:
  0=vague/absent, 1=generic benefit, 2=specific benefit,
  3=specific+quantified, 4=specific+quantified+evidence"
```

Scores (0–4 integers) are cached in `profile.rubric_scores` and fed as `vᵢ`. Rubric calls run in parallel with `asyncio.gather`. These are the only non-deterministic component (T2b eval target: σ ≤ 0.15 per field with temperature=0.1).

## Anomaly Detection

Ten rule-based contradiction detectors applied after scoring:

| Anomaly | Trigger |
|---|---|
| `revenue_without_interviews` | Revenue claimed, zero customer interviews |
| `negative_unit_economics` | LTV below CAC |
| `critical_runway` | < 3 months runway |
| `ai_act_noncompliance` | AI product, no GDPR/AI Act measures |
| `ltv_without_cac` | LTV reported, no CAC |
| `high_burn_no_revenue` | High burn, zero revenue |
| `team_single_founder_ops` | Solo founder + operations-heavy business |
| `ip_gap` | Tech innovation claimed, no IP protection |
| `legal_unregistered` | Revenue reported, not registered |
| `market_size_mismatch` | Very large TAM claim with early-stage profile |

Eval target T2c: **100% recall** across 10 fixture profiles — verified.

## Standalone HTTP API

```
POST /score       — one named composite score for a profile
POST /score/all   — all five scores in one call
POST /detect      — run anomaly detection only
GET  /health
```

Axis services use Affinitree **in-process** (no HTTP hop) for performance. The HTTP API is for testing and external integrations.

## Determinism Guarantee

Eval target T2a: **10-run identity** — the same profile input produces bit-identical scores. Verified. This is fundamental to Score Debate: the system can recompute from a modified profile and guarantee the delta reflects only the profile change.

For the full formula configuration and academic citations embedded in config JSON, see `backend/scoring-engine/affinitree/config/`.
