# Signal Service — moufida-signal

**Location:** `signal/` | **Port:** 8010  
**Stack:** Rust, Axum, tokio, serde_json, parking_lot

A standalone Rust microservice implementing two research papers. It runs no database queries, makes no LLM calls, and has no external runtime dependencies. All weights and direction vectors are baked into the image or installed at startup.

**Best-effort integration:** the diagnostic and RAG pipelines degrade gracefully if this service is down. CBM concept breakdowns are simply absent; RAG falls back to standard RRF.

For full mathematical derivations see:
- [research/concept-bottleneck.md](../research/concept-bottleneck.md)
- [research/axis-directions.md](../research/axis-directions.md)

---

## Paper 1 — Concept Bottleneck Model

**Papers:** Koh et al. ICML 2020; Oikarinen et al. (Label-Free) ICLR 2023

Moufida's Label-Free CBM variant: the LLM scores each named concept (0–1), then a linear weight layer produces the final score and identifies the bottleneck.

### Endpoints

**`POST /cbm/score`**
```json
{
  "axis": "market",
  "concepts": { "tam_evidence": 0.62, "icp_specificity": 0.18, "wtp_signal": 0.38 }
}
```
Returns: `score`, `weighted_contributions`, `bottleneck` (concept_id, current, weight, score_if_fixed).

Bottleneck = `argmax_i [ wᵢ × (1 - cᵢ) ]` — the concept with highest improvement potential.

**`POST /cbm/calibrate`** — ridge regression (`min_w ||Cw−y||² + λ||w||²`) over the `score_snapshots` history. Updates `cbm_weights.json`. Runs on ≥ 20 rows per axis.

### Concept Definitions

| Axis | Concepts |
|---|---|
| Ideation | problem_clarity, solution_originality, founder_domain_fit, idea_testability |
| Market | tam_evidence, icp_specificity, wtp_signal, competitive_differentiation, market_timing |
| Product | mvp_existence, technical_feasibility, core_features_defined, ux_considered |
| Brand | brand_identity, innovation_degree, ip_awareness |
| Business Model | revenue_model_clarity, unit_economics_viability, pricing_strategy, path_to_profitability |
| Legal | corporate_structure, regulatory_compliance, ip_protection, environmental_awareness |
| Operations | team_completeness, process_definition, supplier_readiness, operational_capacity |
| Marketing | gtm_strategy, channel_identification, messaging_clarity, content_presence |
| Sales | pipeline_existence, sales_process_defined, conversion_evidence, revenue_traction |

### Prior Weights vs. Calibrated Weights

Weights start from domain priors defined in `concepts.json` (e.g., `icp_specificity` weight = 0.35 for market — domain knowledge says ICP clarity is most diagnostic for early-stage market validation). As `score_snapshots` accumulates ≥ 20 rows per axis, `/cbm/calibrate` learns data-driven weights that override the priors. The UI shows a "prior / calibrated" chip per axis.

---

## Paper 2 — Contrastive Axis Direction Probe

**Papers:** Zou et al. (Representation Engineering) arXiv 2023; Park et al. (Linear Representation Hypothesis) arXiv 2023

Nine unit direction vectors in 1024-dim `bge-m3` embedding space, one per diagnostic axis. Computed offline by `scripts/compute_axis_directions.py` (contrastive mean: μ_pos − μ_neg, normalised).

### Endpoints

**`POST /probe/project`**
```json
{ "embedding": [0.12, -0.03, ...], "top_k": 3 }
```
Returns: `axis_relevance` (all 9 axes scored 0–1), `top_axes`, `dominant_axis`.

Matrix multiply: `Dᵀ · e` where D is (9×1024). Executes in < 5 µs — zero perceptible latency.

**`POST /probe/install`** — pushes new direction matrix + stats at runtime (used by `compute-directions` script).

**`POST /probe/reload`** — reloads from disk (JSON or NumPy `.npy` format).

### Two Uses

1. **RAG re-ranking:** 30% axis relevance blended into RRF score during retrieval when `current_axis` is provided.
2. **Auto-tagging at ingest:** each chunk receives its top-2 axes from the probe, replacing manual `score_dimensions` tagging for new content.

---

## Paper 3 — IRT/EAP Acceleration

**`POST /cat/eap`** — Rust-accelerated Bayesian EAP computation for the CAT intake engine. The Python orchestrator has a pure-Python fallback, so this is never blocking. See [research/adaptive-testing.md](../research/adaptive-testing.md).

---

## Why Rust?

- Matrix-vector multiply (9×1024) in < 5 µs — no GIL, no runtime overhead
- Ridge regression on a k×k matrix (k ≤ 5) with nalgebra: microseconds
- Zero Python dependency: the binary is a static executable on a scratch base image
- `context.Context`-style cancellation is built into tokio — concurrent requests don't block each other
