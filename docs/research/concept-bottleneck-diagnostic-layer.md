# Concept Bottleneck Diagnostic Layer

## Papers to Read

**Primary — the architecture:**
> Koh, P. W., Nguyen, T., Tang, Y. S., Mussmann, S., Pierson, E., Kim, B., & Liang, P. (2020).
> **"Concept Bottleneck Models."**
> *International Conference on Machine Learning (ICML 2020).*
> https://arxiv.org/abs/2007.04612

**Extension — removes manual concept annotation:**
> Oikarinen, T., Das, S., Nguyen, L. M., & Weng, T.-W. (2023).
> **"Label-Free Concept Bottleneck Models."**
> *International Conference on Learning Representations (ICLR 2023).*
> https://arxiv.org/abs/2304.06129

**Complementary — post-hoc version (no retraining):**
> Yuksekgonul, M., Wang, M., & Zou, J. (2023).
> **"Post-hoc Concept Bottleneck Models."**
> *International Conference on Learning Representations (ICLR 2023).*
> https://arxiv.org/abs/2205.15480

---

## 1. The Core Idea — Plain Language

Imagine you ask a doctor "what's wrong with this patient?" and they give you a single number: 2.3 out of 5. That number is useless on its own. Now imagine they first tell you: "blood pressure is elevated (0.3), oxygen saturation is good (0.9), temperature is slightly high (0.4), heart rate is borderline (0.5)" — and *then* derive the severity score from those named observations. Suddenly you know exactly what to treat.

That's a **Concept Bottleneck Model**. The prediction must flow through a layer of named, human-readable concepts before it produces the final output. The concepts are the bottleneck through which all information must pass.

The original CBM paper (Koh et al., ICML 2020) was designed for image classification — specifically skin lesion diagnosis. Instead of `image → cancer risk score`, it used `image → [asymmetry, border irregularity, color variation, diameter] → cancer risk`. Each concept in the middle layer is interpretable. A doctor can read them, correct them if wrong ("the model overestimates border irregularity"), and the correction propagates to the final prediction.

### The Problem with Standard CBMs

The original approach requires concept-level ground-truth labels in your training data — you need human annotators to score each image on "asymmetry" and "border irregularity". That's expensive.

The **Label-Free CBM** (Oikarinen et al., ICLR 2023) solves this: instead of human labels, use the LLM itself to evaluate whether a given concept applies to a given input. The LLM acts as a zero-shot concept scorer. You still learn the concept-to-output weights from historical data, but you never need annotated concept labels.

The **Post-hoc CBM** (Yuksekgonul et al., ICLR 2023) goes further — you can take an existing model's predictions and reverse-engineer a concept bottleneck on top of them. No retraining at all.

---

## 2. The Math (Approachable)

Let `x` be the input (founder's profile), `y` be the output (axis score 0–5), and `c₁…cₖ` be `k` named concepts.

**Standard CBM:**
```
x  →  [c₁, c₂, …, cₖ]  →  ŷ
       concept layer       linear layer
```

- The concept layer `f(x) → c` produces a vector of concept activations in [0, 1].
- The linear layer `g(c) = Σᵢ wᵢ · cᵢ + b` produces the final score.
- `g` is intentionally kept simple (linear) so the mapping is auditable: score = weighted sum of concepts.

**Label-Free CBM (Moufida version):**

The LLM replaces the learned concept layer `f`. For each concept `cᵢ`, you prompt Ollama:
```
"On a scale of 0.0 to 1.0, how well does this startup profile demonstrate [concept_i]?
 Profile: {profile_text}
 Return only a JSON: { \"score\": float }"
```

This gives you `c = [c₁, c₂, …, cₖ]` from the LLM without any concept annotation.

Then a learned weight vector `w` (calibrated from the `score_snapshots` history) computes:
```
axis_score = sigmoid(wᵀ · c + b) × 5.0
```

The weight vector `w` tells you how much each concept contributes to the final score. A large `|wᵢ|` means concept `i` is a strong driver. If `cᵢ` is low AND `wᵢ` is large, concept `i` is the **bottleneck** — the concept that is most holding the score down.

---

## 3. Why This Matters for Moufida

### The current problem

Right now, the market axis produces:
```json
{ "score": 2.3, "confidence": "medium", "evidence": ["No validated customers..."] }
```

The founder knows the score is low. They do not know:
- Which specific aspect of "market" is the weakest
- How much improving each aspect would move the score
- Whether fixing ICP clarity is more valuable than fixing WTP evidence
- Whether the LLM's assessment of each sub-dimension is actually grounded

### What the CBM layer adds

```
Market score: 2.3 / 5

  Concept breakdown:
  ┌────────────────────────────────────────────────────────────┐
  │ TAM evidence           ████████░░░░░░  0.62  (w=0.20)     │
  │ ICP specificity        ██░░░░░░░░░░░░  0.18  (w=0.35) ◄── │  ← Bottleneck
  │ WTP signal             █████░░░░░░░░░  0.38  (w=0.25)     │
  │ Competitive diff.      ███████░░░░░░░  0.54  (w=0.10)     │
  │ Market timing          ███████████░░░  0.80  (w=0.10)     │
  └────────────────────────────────────────────────────────────┘

  Bottleneck: ICP specificity (score 0.18, weight 0.35)
  → Improving ICP clarity from 0.18 to 0.60 would move market score to ~3.1
```

The founder now knows exactly what to do. The roadmap engine can surface ICP-specific actions. The score number is no longer an oracle — it's a decomposable, arguable, improvable quantity.

---

## 4. Concept Set Definition — All 9 Axes

These are the named micro-concepts per axis. Each concept is a yes/no question rephrased as a 0–1 activation.

### Ideation
| # | Concept | What it measures |
|---|---|---|
| 1 | `problem_clarity` | Is the problem being solved well-defined and specific? |
| 2 | `solution_originality` | Does the solution approach differ meaningfully from what exists? |
| 3 | `founder_domain_fit` | Does the team have relevant domain knowledge or experience? |
| 4 | `idea_testability` | Can the core hypothesis be tested quickly and cheaply? |

### Market
| # | Concept | What it measures |
|---|---|---|
| 1 | `tam_evidence` | Is there data or credible estimates of total addressable market size? |
| 2 | `icp_specificity` | Is the ideal customer profile described concretely (who, where, why)? |
| 3 | `wtp_signal` | Is there evidence customers would pay, at what price? |
| 4 | `competitive_differentiation` | How distinct is the offering vs. known alternatives? |
| 5 | `market_timing` | Is there a reason this works now that didn't exist 2 years ago? |

### Product
| # | Concept | What it measures |
|---|---|---|
| 1 | `mvp_existence` | Is there a working prototype, MVP, or demo? |
| 2 | `technical_feasibility` | Can this be built with available technology and team skills? |
| 3 | `core_features_defined` | Are the must-have features clearly specified? |
| 4 | `ux_considered` | Has the user experience been explicitly designed or tested? |

### Brand & Innovation
| # | Concept | What it measures |
|---|---|---|
| 1 | `brand_identity` | Does the venture have a distinct name, visual identity, and positioning? |
| 2 | `innovation_degree` | How novel is this relative to incumbent solutions? |
| 3 | `ip_awareness` | Has the team considered patents, trademarks, or trade secrets? |

### Business Model
| # | Concept | What it measures |
|---|---|---|
| 1 | `revenue_model_clarity` | Is there a clear, specific way the venture makes money? |
| 2 | `unit_economics_viability` | Are LTV/CAC or equivalent metrics defined and plausible? |
| 3 | `pricing_strategy` | Is pricing justified relative to value delivered and competitors? |
| 4 | `path_to_profitability` | Is there a plausible timeline to positive margins? |

### Legal & Environmental
| # | Concept | What it measures |
|---|---|---|
| 1 | `corporate_structure` | Is the entity properly registered (or is there a plan to)? |
| 2 | `regulatory_compliance` | Are the applicable local regulations identified and addressed? |
| 3 | `ip_protection` | Are key IP assets legally protected or in the process of being protected? |
| 4 | `environmental_awareness` | Has environmental impact been considered in the business model? |

### Operations
| # | Concept | What it measures |
|---|---|---|
| 1 | `team_completeness` | Do the founders collectively cover key skill areas (tech, biz, domain)? |
| 2 | `process_definition` | Are core operational processes documented or planned? |
| 3 | `supplier_readiness` | Are key suppliers, vendors, or partners identified? |
| 4 | `operational_capacity` | Can the team handle near-term growth without immediate hiring? |

### Marketing
| # | Concept | What it measures |
|---|---|---|
| 1 | `gtm_strategy` | Is there a specific plan for reaching the first 100 customers? |
| 2 | `channel_identification` | Are the most effective acquisition channels identified? |
| 3 | `messaging_clarity` | Is the value proposition communicated in one clear sentence? |
| 4 | `content_presence` | Is there any existing content, community, or audience? |

### Sales
| # | Concept | What it measures |
|---|---|---|
| 1 | `pipeline_existence` | Are there identified leads, prospects, or signed pilots? |
| 2 | `sales_process_defined` | Is there a repeatable process from lead to close? |
| 3 | `conversion_evidence` | Has anyone actually paid or committed to pay? |
| 4 | `revenue_traction` | Is there any recurring revenue or signed contracts? |

---

## 5. Implementation Plan

The implementation has four layers:

```
[Profile] → [LLM concept scoring] → [Rust weight layer] → [Score + bottleneck]
                  Python                   Rust                  both
```

### Layer 1 — Concept Config (JSON, already all you need)

A single config file `backend/orchestrator/app/cbm/concepts.json` enumerates all concepts per axis with their natural-language prompt template:

```json
{
  "market": [
    {
      "id": "tam_evidence",
      "label": "TAM Evidence",
      "prompt": "Does the startup profile contain evidence or estimates of the total addressable market size? Score 0.0 (no mention) to 1.0 (specific, sourced figures)."
    },
    {
      "id": "icp_specificity",
      "label": "ICP Specificity",
      "prompt": "How specifically is the ideal customer profile described? Score 0.0 (generic 'SMEs') to 1.0 (specific segment, geography, pain point, and buying trigger)."
    }
  ]
}
```

### Layer 2 — LLM Concept Scorer (Python, new file `cbm/scorer.py`)

```python
# backend/orchestrator/app/cbm/scorer.py
import asyncio, json
from pathlib import Path
from ..llm_json import generate_json

CONCEPTS = json.loads((Path(__file__).parent / "concepts.json").read_text())

async def score_concepts(axis: str, profile_text: str) -> dict[str, float]:
    """
    Ask Ollama to score each concept for this axis.
    Returns { concept_id: float in [0, 1] }.
    """
    axis_concepts = CONCEPTS.get(axis, [])
    
    async def _score_one(concept: dict) -> tuple[str, float]:
        prompt = (
            f"You are evaluating a startup profile for the '{axis}' diagnostic axis.\n"
            f"Task: {concept['prompt']}\n\n"
            f"Profile:\n{profile_text}\n\n"
            f"Respond with JSON only: {{\"score\": <float 0.0–1.0>}}"
        )
        result = await generate_json(prompt, temperature=0.1)
        return concept["id"], float(result.get("score", 0.5))
    
    results = await asyncio.gather(*[_score_one(c) for c in axis_concepts])
    return dict(results)
```

**Key decision:** concepts within one axis are scored in parallel (`asyncio.gather`). 4–5 concepts × ~300ms per Ollama call = ~400ms total (same as one full axis call today, since they run concurrently).

### Layer 3 — Rust Weight Layer (`signal/src/cbm.rs`)

The Rust binary `moufida-signal` (or a dedicated `moufida-cbm`) exposes:

```
POST /cbm/score
  {
    "axis": "market",
    "concepts": { "tam_evidence": 0.62, "icp_specificity": 0.18, ... }
  }
  →
  {
    "score": 2.31,
    "weighted_contributions": { "tam_evidence": 0.31, "icp_specificity": 0.16, ... },
    "bottleneck": {
      "concept_id": "icp_specificity",
      "label": "ICP Specificity",
      "current": 0.18,
      "weight": 0.35,
      "score_at_0_60": 3.08,
      "score_at_1_00": 3.72
    }
  }

POST /cbm/calibrate
  {
    "axis": "market",
    "observations": [
      { "concepts": { "tam_evidence": 0.7, ... }, "actual_score": 3.2 },
      ...
    ]
  }
  → { "weights": { ... }, "bias": float, "r_squared": float }
```

**Rust implementation of `/cbm/score`:**

```rust
// signal/src/cbm.rs

use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct ScoreRequest {
    pub axis: String,
    pub concepts: HashMap<String, f64>,
}

#[derive(Serialize)]
pub struct Bottleneck {
    pub concept_id: String,
    pub label: String,
    pub current: f64,
    pub weight: f64,
    pub score_if_fixed: f64,   // score if this concept goes to 0.80
}

#[derive(Serialize)]
pub struct ScoreResponse {
    pub score: f64,
    pub weighted_contributions: HashMap<String, f64>,
    pub bottleneck: Option<Bottleneck>,
}

pub fn compute_score(
    weights: &HashMap<String, f64>,
    bias: f64,
    concepts: &HashMap<String, f64>,
) -> ScoreResponse {
    let mut raw = bias;
    let mut contributions = HashMap::new();
    let mut bottleneck_candidate: Option<(String, f64, f64)> = None; // (id, concept_val, weight)

    for (concept_id, &concept_val) in concepts {
        let w = weights.get(concept_id).copied().unwrap_or(0.0);
        let contribution = w * concept_val;
        raw += contribution;
        contributions.insert(concept_id.clone(), contribution);

        // Bottleneck: concept with largest weight × (1 - current_value) = most improvement potential
        let potential = w.abs() * (1.0 - concept_val);
        let current_best = bottleneck_candidate
            .as_ref()
            .map(|(_, _, p)| *p)
            .unwrap_or(0.0);
        if w > 0.0 && potential > current_best {
            bottleneck_candidate = Some((concept_id.clone(), concept_val, potential));
        }
    }

    // Map raw logit to [0, 5] via sigmoid
    let score = (1.0 / (1.0 + (-raw).exp())) * 5.0;

    let bottleneck = bottleneck_candidate.map(|(concept_id, current, _)| {
        let w = weights[&concept_id];
        // Project: what if this concept improves to 0.80?
        let delta = w * (0.80 - current);
        let new_raw = raw + delta;
        let fixed_score = (1.0 / (1.0 + (-new_raw).exp())) * 5.0;
        Bottleneck {
            label: concept_id.clone(), // enriched with label from config at HTTP layer
            concept_id,
            current,
            weight: w,
            score_if_fixed: (fixed_score * 100.0).round() / 100.0,
        }
    });

    ScoreResponse {
        score: (score * 100.0).round() / 100.0,
        weighted_contributions: contributions,
        bottleneck,
    }
}
```

**Calibration (`/cbm/calibrate`) — Ridge Regression in Rust:**

```rust
// Given N observations of (concept_vector, actual_score),
// solve: min_w ||Cw - y||² + λ||w||²
// where C is the N×k concept matrix, y is the N×1 score vector.
// Solution: w = (CᵀC + λI)⁻¹Cᵀy
// Implementable with the `nalgebra` crate — matrix inverse on a k×k matrix
// where k ≤ 5, so extremely fast.
```

### Layer 4 — Weight Bootstrapping (No Historical Data Yet)

On first run, before any `score_snapshots` exist, use **domain-prior weights** defined in `concepts.json`:

```json
{
  "market": {
    "weights": {
      "tam_evidence": 0.20,
      "icp_specificity": 0.35,
      "wtp_signal": 0.25,
      "competitive_differentiation": 0.10,
      "market_timing": 0.10
    },
    "bias": -1.2
  }
}
```

These prior weights encode domain knowledge (ICP specificity and WTP signal are the most diagnostic for early-stage market validation). As `score_snapshots` accumulates (≥ 20 rows per axis), the Rust calibration endpoint learns data-driven weights that override the priors.

### Layer 5 — Orchestrator Integration

In `backend/orchestrator/app/diagnostic_router.py`, after each axis call returns a score, add:

```python
# After getting axis_result from the axis microservice:
from .cbm.scorer import score_concepts

concept_scores = await score_concepts(axis_name, profile_text)

async with httpx.AsyncClient() as client:
    cbm_resp = await client.post(
        f"{SIGNAL_URL}/cbm/score",
        json={"axis": axis_name, "concepts": concept_scores}
    )
cbm_data = cbm_resp.json()

# Store concept scores and bottleneck in axis_outputs JSONB
axis_result["concept_scores"] = concept_scores
axis_result["cbm_score"] = cbm_data["score"]
axis_result["bottleneck"] = cbm_data["bottleneck"]
```

The axis microservice score and the CBM score run in parallel — we display both and over time validate that they agree (they should converge as calibration improves).

### New DB migration — `020_concept_scores.sql`

```sql
CREATE TABLE concept_scores (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    axis        TEXT NOT NULL,
    concepts    JSONB NOT NULL,   -- { concept_id: float }
    cbm_score   REAL,
    bottleneck  JSONB,            -- { concept_id, weight, current, score_if_fixed }
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON concept_scores (project_id, axis, created_at DESC);
```

---

## 6. UI/UX Integration

### Axis score card — expanded view

```
┌─────────────────────────────────────────────────────────┐
│  Market                                     2.3 / 5     │
│                                                         │
│  [▼ Concept breakdown]                                  │
│                                                         │
│  TAM Evidence         ▓▓▓▓▓▓▓░░░░░░  0.62   ×0.20      │
│  ICP Specificity      ▓▓░░░░░░░░░░░  0.18   ×0.35  ◄── │
│  WTP Signal           ▓▓▓▓▓░░░░░░░░  0.38   ×0.25      │
│  Competitive Diff.    ▓▓▓▓▓▓▓░░░░░░  0.54   ×0.10      │
│  Market Timing        ▓▓▓▓▓▓▓▓▓▓░░  0.80   ×0.10      │
│                                                         │
│  ⚡ Bottleneck: ICP Specificity                         │
│     Improving this from 0.18 → 0.60 would move your    │
│     market score from 2.3 to 3.1                        │
│                                                         │
│  [→ See ICP recommendations]                           │
└─────────────────────────────────────────────────────────┘
```

### Roadmap integration

The bottleneck concept becomes the top-priority roadmap item for that axis. The roadmap engine receives `bottleneck.concept_id` and generates recommendations scoped to that specific concept, not the entire axis.

### 2D character integration

When the CBM analysis completes and a bottleneck is found, the character points at the bottleneck card and says (speech bubble): *"ICP clarity is what's holding your market score back — everything else is decent."* Character state: `"presenting"`.

---

## 7. What This Is NOT

- **Not a neural concept bottleneck.** We are not training a neural network. The concept scorer is the LLM (Ollama). The bottleneck layer is a simple linear weight vector calibrated by ridge regression on score history.
- **Not an explanation post-hoc.** The concepts run as part of the scoring pipeline, not as an afterthought explanation of a black-box score.
- **Not reinventing CBMs.** The contribution is applying the Label-Free CBM paradigm to startup diagnostic scoring — a domain where named micro-concepts map cleanly to the evaluation rubric — and using ridge regression over diagnostic history as the calibration mechanism.

---

## 8. Files to Create

```
backend/orchestrator/app/
  cbm/
    __init__.py
    scorer.py          ← LLM concept scoring (parallel asyncio calls)
    concepts.json      ← concept definitions + prior weights per axis

signal/               ← Rust binary (or moufida-signal if already exists)
  src/
    cbm.rs             ← score computation + ridge calibration
    cbm_weights.json   ← live weight store (written by /cbm/calibrate)

db/migrations/
  020_concept_scores.sql

frontend/src/components/dashboard/
  ConceptBreakdown.tsx ← expandable axis card sub-panel
  BottleneckAlert.tsx  ← bottleneck highlight + CTA
```
