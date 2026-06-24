# Research: Concept Bottleneck Models

## Papers

**Primary architecture:**
> Koh, P. W., et al. (2020). "Concept Bottleneck Models." *ICML 2020.* [arXiv:2007.04612](https://arxiv.org/abs/2007.04612)

**Label-free extension (Moufida uses this variant):**
> Oikarinen, T., et al. (2023). "Label-Free Concept Bottleneck Models." *ICLR 2023.* [arXiv:2304.06129](https://arxiv.org/abs/2304.06129)

**Post-hoc version:**
> Yuksekgonul, M., et al. (2023). "Post-hoc Concept Bottleneck Models." *ICLR 2023.* [arXiv:2205.15480](https://arxiv.org/abs/2205.15480)

---

## The Core Idea — Plain Language

Imagine a doctor who gives you a single health score: 2.3 out of 5. That number is useless on its own. Now imagine they first tell you: "blood pressure is elevated (0.3), oxygen saturation is fine (0.9), temperature is slightly high (0.4), heart rate is borderline (0.5)" — and *then* derive the severity from those named observations. You now know exactly what to treat.

That is a **Concept Bottleneck Model**. The prediction must flow through a layer of named, human-readable concepts before producing the final output. The concepts are the bottleneck through which all information must pass.

The original paper was designed for skin lesion diagnosis: instead of `image → cancer risk`, it used `image → [asymmetry, border irregularity, color variation, diameter] → cancer risk`. A doctor can read the concepts, correct them if wrong, and the correction propagates to the final prediction.

---

## The Problem with Standard CBMs

The original approach requires concept-level ground-truth labels — human annotators must score each input on each concept. That's expensive.

The **Label-Free CBM** (Oikarinen et al., ICLR 2023) solves this: instead of human labels, use an LLM as a zero-shot concept scorer. You still learn the concept-to-output weights from historical data, but you never need annotated concept labels.

---

## The Math

Let `x` be the input (founder's profile), `y` be the output (axis score 0–5), and `c₁…cₖ` be `k` named concepts.

**Standard CBM:**
```
x  →  [c₁, c₂, …, cₖ]  →  ŷ
       concept layer       linear layer
```

**Moufida's Label-Free CBM:**

The LLM (Ollama) replaces the trained concept encoder. For each concept `cᵢ`:

```
Prompt to Ollama:
"On a scale of 0.0 to 1.0, how well does this startup profile demonstrate [concept_i]?
 Return only JSON: { 'score': float }"

→ cᵢ ∈ [0, 1]
```

A learned weight vector `w` (calibrated by ridge regression on `score_snapshots` history) computes:

```
axis_score = sigmoid(wᵀ · c + b) × 5.0
```

**Bottleneck identification:**
```
bottleneck = argmax_i [ wᵢ × (1 - cᵢ) ]
```
The concept with the highest weight × improvement potential is the bottleneck. If `cᵢ` is low AND `wᵢ` is large, fixing that concept will move the score the most.

**Projected improvement:**
```
Δscore if concept_i → 0.80:
  new_raw = current_raw + wᵢ × (0.80 - cᵢ)
  new_score = sigmoid(new_raw) × 5.0
```

This gives a concrete, quantified target: "fixing ICP clarity from 0.18 to 0.60 would move your market score from 2.3 to 3.1."

---

## Calibration — Ridge Regression

The weight vector `w` starts from domain priors (encoded in `concepts.json`). As the system accumulates ≥ 20 diagnostic records per axis, the Rust `/cbm/calibrate` endpoint runs ridge regression to learn data-driven weights:

```
Minimize: ||Cw - y||² + λ||w||²
Solution: w = (CᵀC + λI)⁻¹ Cᵀy
```

Where:
- `C` = N×k concept matrix (N historical diagnoses, k concepts)
- `y` = N×1 actual score vector from `score_snapshots`
- `λ` = ridge regularisation (prevents overfitting with small N)

Because `k ≤ 5`, this is a tiny matrix inversion — computed in microseconds by the nalgebra crate. The calibrated weights are persisted in `signal/assets/cbm_weights.json`.

---

## How This Differs from Standard ML Interpretability

**Not LIME/SHAP post-hoc explanations.** LIME/SHAP explain an existing black-box model by perturbing inputs. The CBM layer is part of the scoring pipeline, not an afterthought.

**Not neural CBMs.** No neural network is trained. The "concept encoder" is the LLM (Ollama). The only learned component is the linear weight vector, which is auditable by inspection.

**Not reinventing CBMs.** The contribution is applying the Label-Free CBM paradigm to startup diagnostic scoring — a domain where named micro-concepts (TAM evidence, ICP specificity, WTP signal) map cleanly to the evaluation rubric.

---

## Implementation in Moufida

```
Axis Diagnosis Request
  │
  ├─ Python (orchestrator/cbm/scorer.py)
  │    For each concept in concepts.json for this axis:
  │      asyncio.gather(Ollama calls in parallel) → concept_scores dict
  │
  ├─ Rust (signal:8010/cbm/score)
  │    Apply weight vector → score, weighted_contributions, bottleneck
  │
  ├─ PostgreSQL (concept_scores table)
  │    Persist concept scores + bottleneck for history tracking
  │
  └─ SSE (concept_update event)
       Push to UI → ConceptBreakdown component renders bar chart
```

**Performance:** Concept scoring runs in parallel with axis scoring. 4–5 concepts × ~300ms per Ollama call = ~400ms total (same as one axis call, since they run concurrently with `asyncio.gather`).

---

## What Founders and Judges See

The `ConceptBreakdown` dashboard component shows:

```
┌──────────────────────────────────────────────────────────┐
│  Market                                       2.3 / 5    │
│                                                          │
│  ▼ Concept breakdown                                     │
│                                                          │
│  TAM Evidence        ████████░░░░  0.62  ×0.20           │
│  ICP Specificity     ██░░░░░░░░░░  0.18  ×0.35  ◄── ⚡   │
│  WTP Signal          █████░░░░░░░  0.38  ×0.25           │
│  Competitive Diff.   ███████░░░░░  0.54  ×0.10           │
│  Market Timing       ██████████░░  0.80  ×0.10           │
│                                                          │
│  ⚡ Bottleneck: ICP Specificity                          │
│    Improving this from 0.18 → 0.60 would bring your     │
│    market score from 2.3 to 3.1                          │
│                                                          │
│  [→ See ICP recommendations in roadmap]                  │
└──────────────────────────────────────────────────────────┘
```

The roadmap engine receives `bottleneck.concept_id` and surfaces ICP-specific actions as the top priority for that axis.

---

## For a Deep Dive

See the full engineering design document: `docs/research/` (original research paper adaptation by the Moufida team) and the implementation in:
- `backend/orchestrator/app/cbm/` — Python concept scorer
- `signal/src/cbm.rs` — Rust weight layer
- `frontend/src/components/dashboard/ConceptBreakdown.tsx` — UI component
