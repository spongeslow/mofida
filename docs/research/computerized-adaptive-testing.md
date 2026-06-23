# Computerized Adaptive Testing for Startup Stage Identification

## Papers to Read

**Primary — IRT model and Fisher information for item selection:**
> Lord, F. M. (1977).
> **"Practical applications of item characteristic curve theory."**
> *Journal of Educational Measurement, 14*(2), 117–138.

**Adaptive ability estimation — the EAP update rule:**
> Bock, R. D., & Mislevy, R. J. (1982).
> **"Adaptive EAP estimation of ability in a microcomputer environment."**
> *Applied Psychological Measurement, 6*(4), 431–444.
> https://doi.org/10.1177/014662168200600402

**CAT system design — stopping rules, content balancing, exposure control:**
> Wainer, H. (Ed.). (2000).
> **"Computerized Adaptive Testing: A Primer"** (2nd ed.).
> *Lawrence Erlbaum Associates.*

**Extension to polytomous (graded-scale) responses:**
> Samejima, F. (1997).
> **"The graded response model."**
> In W. J. van der Linden & R. K. Hambleton (Eds.), *Handbook of Modern Item Response Theory.* Springer.
> https://doi.org/10.1007/978-1-4757-2691-6_5

**Deep learning reinterpretation — neural IRT:**
> Tsutsumi, E., Kinoshita, R., & Ueno, M. (2021).
> **"Deep Item Response Theory as a Novel Test Theory Based on Deep Neural Networks."**
> *Electronics, 10*(9), 1020.
> https://doi.org/10.3390/electronics10091020

---

## 1. The Core Idea — Plain Language

Imagine you are a doctor trying to determine whether a patient has mild, moderate, or severe hypertension. You have 40 diagnostic tests available. A bad doctor would run all 40 every time. A good doctor starts with a blood pressure reading. If it's normal, they stop — no further tests needed. If it's elevated, they run the next most informative test for *this patient's specific reading*. They converge on a precise diagnosis in 6 tests instead of 40, because each test is chosen based on what is already known.

That is **Computerized Adaptive Testing (CAT)**. Instead of giving every student — or every founder — the same fixed questionnaire, CAT dynamically selects the next question that provides maximum information about the person's underlying position on the measured trait. The underlying math is **Item Response Theory (IRT)**, a psychometric model that has underpinned standardized adaptive testing (GMAT, GRE, TOEFL, PISA) since the 1980s.

### The Key Insight: Items Have Difficulty and Discrimination

In a fixed diagnostic form, all questions are treated as equally informative. IRT recognizes that they are not. Each question (called an *item* in IRT) is characterized by two parameters:

- **Discrimination (a):** How sharply does this question separate founders at different stages? A question like "Do you have paying customers?" cleanly separates Stage 2 founders (no) from Stage 4 founders (yes). It has high discrimination. A question like "Are you passionate about your idea?" discriminates nothing — everyone says yes.

- **Difficulty (b):** At what stage level does the typical founder give a strong positive answer? "Have you thought about the problem you're solving?" has low difficulty — even Stage 1 founders say yes. "Do you have MoM revenue growth above 10%?" has high difficulty — only Stage 5/6 founders say yes.

The core idea is: **ask a question at the right difficulty for where you think the founder is.** If you estimate they are at Stage 2, asking a Stage 5 question gives almost no information (everyone at Stage 2 answers no, so you learn nothing new). Asking a Stage 2 question is maximally informative — their answer genuinely discriminates between early-Stage-2 and late-Stage-2.

### The CAT Loop

```
Start: θ̂ = 0 (neutral prior — no idea where they are yet)

    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │  1. Select item j* with maximum information at θ̂    │
    │  2. Ask the founder question j*                      │
    │  3. Record response u_j* ∈ {0, 1}                   │
    │  4. Update θ̂ using Bayesian EAP rule                │
    │  5. Check stopping criterion                         │
    │     → if SE(θ̂) < 0.35 OR 12 items answered: STOP   │
    │     → otherwise: go to step 1                        │
    │                                                      │
    └──────────────────────────────────────────────────────┘

End: θ̂ → map to one of 6 stages
```

This loop converges on a precise stage estimate in **8–12 questions** instead of 30+. Founders whose answers are consistent (clearly Stage 2, clearly Stage 5) terminate even earlier. Only founders near a stage boundary — where precision matters most — receive more questions.

### Why the Analogy to GMAT Is Exact

The GMAT has been adaptive since 1997. A test-taker who answers the first question correctly gets a harder second question. One who answers incorrectly gets an easier one. After ~37 questions, the system has a precise estimate of verbal and quantitative ability. The same logic applies here, with "startup maturity" replacing "verbal ability" and "diagnostic questions" replacing "reading comprehension items."

The Moufida difference: the GMAT estimates a single latent trait (ability). Moufida estimates a latent trait (stage/maturity) **and** must collect information across 10 diagnostic axes. This creates a two-phase design, described in Section 4.

---

## 2. The Math

### 2.1 The 2-Parameter Logistic (2PL) Model

Let `θ` be the latent startup maturity — a continuous variable on a standardized scale. Let item `j` be characterized by discrimination `a_j > 0` and difficulty `b_j ∈ ℝ`.

The probability that a founder with latent maturity `θ` gives a positive response to item `j` is:

```
P_j(θ) = 1 / (1 + exp(−a_j (θ − b_j)))
```

This is a logistic function:
- When `θ = b_j`: `P_j = 0.5` — the question is at exactly the right difficulty
- When `θ ≫ b_j`: `P_j → 1` — too easy, almost certainly answered positively
- When `θ ≪ b_j`: `P_j → 0` — too hard, almost certainly answered negatively
- `a_j` controls the steepness: high `a_j` = sharp transition = high discrimination

```
P_j(θ)
  1.0 ┤                                        ╭─────────────
      │                                    ╭───╯
  0.5 ┤─────────────────────── ╭───────────╯  ← b_j (difficulty)
      │                    ╭───╯
  0.0 ┤───────────────╭────╯
      └──────────────────────────────────────── θ (startup maturity)
       Stage 1      Stage 2      Stage 3      Stage 4
```

### 2.2 Fisher Information for a Single Item

The **Fisher information** of item `j` at ability level `θ` measures how much that item reduces our uncertainty about `θ`:

```
I_j(θ) = a_j² × P_j(θ) × (1 − P_j(θ))
```

This is maximized when `P_j(θ) = 0.5`, i.e., when `θ = b_j`. An item gives maximum information about a founder when that founder is right at the item's difficulty level — neither too easy nor too hard.

**Item selection rule (Maximum Information):**
```
j* = argmax_j  I_j(θ̂)   over all unanswered items
```

### 2.3 The Log-Likelihood

Given responses `u = {u₁, u₂, …, uₖ}` to items answered so far, the log-likelihood of a specific `θ` value is:

```
ℓ(θ | u) = Σ_{j answered} [ u_j log P_j(θ) + (1 − u_j) log(1 − P_j(θ)) ]
```

Because items are conditionally independent given `θ` (the fundamental IRT assumption), the joint likelihood factorizes into a product — or equivalently, the log-likelihood is a sum.

### 2.4 The EAP Estimator (Bock & Mislevy, 1982)

Maximum Likelihood Estimation of `θ` is undefined when all responses so far are 0 or all are 1 (which is common early in a CAT session). The **Expected A Posteriori (EAP)** estimator avoids this by incorporating a prior:

```
Prior:  π(θ) = Normal(0, 1)   [standardized, centered at Stage 3 of 6]

Posterior ∝ L(u | θ) × π(θ)
```

Evaluate numerically over a grid `Θ = {−4.0, −3.9, …, 3.9, 4.0}` (81 points, step = 0.1):

```
w_k = exp( ℓ(θ_k | u) ) × π(θ_k)     for each grid point k

θ̂_EAP = Σ_k θ_k × w_k / Σ_k w_k

SE²(θ̂) = Σ_k (θ_k − θ̂_EAP)² × w_k / Σ_k w_k
SE(θ̂)  = √SE²(θ̂)
```

Use log-sum-exp to avoid numerical underflow:

```python
log_weights = log_likelihood_grid(u, theta_grid) + log_prior(theta_grid)
log_Z = logsumexp(log_weights)
weights = exp(log_weights - log_Z)    # normalized to sum to 1
theta_hat = dot(theta_grid, weights)
se = sqrt(dot((theta_grid - theta_hat)**2, weights))
```

**Convergence behavior:** With a single answered item, `SE ≈ 0.9` (high uncertainty). After 4 consistent answers, `SE ≈ 0.45`. After 8 items, `SE ≈ 0.30` for founders clearly in one stage. The stopping criterion `SE < 0.35` is typically met in 8–12 items.

### 2.5 Stage Boundaries

The continuous estimate `θ̂` maps to the 6-stage Moufida taxonomy via fixed boundary parameters:

```
θ < −1.75   →  Stage 1: Ideation
−1.75 ≤ θ < −0.75  →  Stage 2: Market Validation
−0.75 ≤ θ < 0.25   →  Stage 3: Structuration
 0.25 ≤ θ < 1.25   →  Stage 4: Fundraising Ready
 1.25 ≤ θ < 2.25   →  Stage 5: Launch Planning
θ ≥ 2.25    →  Stage 6: Growth
```

These boundaries are evenly spaced on the standardized scale (1.0 unit per stage), with the prior centered on Stage 3 (θ = 0). They can be calibrated from data once `diagnostic_sessions` accumulates ≥ 100 complete assessments.

---

## 3. Why This Matters for Moufida

### The Current Problem: Fixed Questions, No Adaptation

The current intake form presents a fixed sequence of questions in a predetermined order. Every founder, regardless of how they answer early questions, receives the same follow-up questions. This has three concrete costs:

**1. Wasted questions.** A founder who immediately reveals they have 200 paying customers and €50K MRR is still asked "Have you thought about who your customer is?" — an insulting question at Stage 5. Conversely, a Stage 1 founder who hasn't named their problem yet is asked "What's your CAC?" — a meaningless question.

**2. Imprecise stage assignment.** The current stage is inferred from the distribution of axis scores after all questions are answered. A long fixed intake with many off-target questions creates noise: the model has to average over both highly informative and completely uninformative responses.

**3. Poor first impression.** A 30-question fixed form feels like an administrative survey. A 10-question form that clearly adapts to your answers — getting harder or more specific as you respond — signals that Moufida understands your situation in real time. This is a qualitative product experience difference.

### What CAT Adds

```
Current intake:
  Question 1  → Question 2  → Question 3  →  …  → Question 30
  [fixed]        [fixed]        [fixed]            [fixed]
                                                    Stage assigned

CAT intake:
  Q1 (b=0.0) → "Yes"  →  θ̂: 0.5
  Q2 (b=1.0) → "Yes"  →  θ̂: 1.1
  Q3 (b=1.5) → "No"   →  θ̂: 0.9
  Q4 (b=1.3) → "Yes"  →  θ̂: 1.2
  SE = 0.31 < 0.35  →  STOP after 4 items  →  Stage 4 (Fundraising Ready)
```

A founder clearly at Stage 4 is identified in 4 questions. The saved 26 questions do not disappear — they are replaced by **targeted axis questions** selected specifically for Stage 4 (Phase 2, described in Section 4). This makes the total intake shorter AND more precise.

### Perception Gap Enhancement

The CAT-estimated `θ̂` becomes a ground-truth stage estimate independent of the founder's self-declared stage. The **perception gap** is then the difference between:
- The stage the founder *claims* to be in (self-declared at intake start)
- The stage Moufida *infers* from their item responses (`θ̂` → stage mapping)

This is more rigorous than the current perception gap, which compares self-assessment on individual axes. A CAT-derived perception gap says: "You believe you're in Stage 4 (Fundraising Ready), but your response pattern places you at Stage 2 (Market Validation) with 87% posterior probability."

---

## 4. Two-Phase Intake Architecture

The CAT addresses stage identification efficiently. But Moufida also needs to score all 10 diagnostic axes. These two goals require different question sets. The solution is a two-phase intake:

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 1 — Stage CAT  (8–12 items)                                  │
│                                                                     │
│  Goal: estimate θ̂ (startup maturity) with SE < 0.35               │
│  Item bank: 24 stage-discriminating items (a, b calibrated)         │
│  Output: θ̂, SE, stage assignment, posterior distribution           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    stage estimate θ̂
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2 — Targeted Axis Assessment  (2 items × 10 axes = 20 items) │
│                                                                     │
│  Goal: score each of the 10 diagnostic axes                         │
│  Item selection: for each axis, pick the 2 items closest to θ̂      │
│  (i.e., b_j closest to θ̂ — most informative for this stage)       │
│  Output: raw evidence per axis → fed to 10 axis microservices       │
└─────────────────────────────────────────────────────────────────────┘
```

**Total questions: 28–32, down from 40+.** More importantly, the Phase 2 questions are always at the right difficulty for the founder's actual stage — a Stage 2 founder never answers fundraising questions, a Stage 5 founder never answers ideation questions.

### Item Bank Design

The question bank is organized into two pools, stored in `backend/orchestrator/app/cat/item_bank.json`:

**Phase 1 Pool — Stage Discriminators (24 items)**

Ordered by difficulty `b` (Stage 1 → Stage 6):

| id | Question | a | b | Stage |
|---|---|---|---|---|
| `p1_problem_articulation` | Can you describe in one sentence the specific problem you're solving? | 1.1 | −2.2 | 1 |
| `p1_target_user_named` | Have you identified who exactly experiences this problem? | 1.3 | −1.8 | 1 |
| `p1_customer_interviews` | Have you spoken directly with at least 3 potential customers? | 1.6 | −1.4 | 1–2 |
| `p1_wtp_signal` | Has anyone expressed willingness to pay for your solution? | 1.9 | −0.8 | 2 |
| `p1_mvp_exists` | Do you have a working prototype or MVP that users can try? | 1.7 | −0.5 | 2 |
| `p1_registered` | Is your company officially registered (APII, RNE, or equivalent)? | 1.5 | 0.1 | 3 |
| `p1_revenue_model` | Do you have a documented business model with a clear revenue stream? | 1.6 | 0.3 | 3 |
| `p1_team_complete` | Do you have a co-founder or team covering both technical and business skills? | 1.2 | 0.0 | 3 |
| `p1_pitch_deck` | Do you have a formal investor pitch deck with financial projections? | 1.4 | 0.9 | 4 |
| `p1_external_funding` | Have you raised external funding (grant, angel, Startup Act, BFPME)? | 2.1 | 1.2 | 4 |
| `p1_ip_filed` | Have you filed for trademark, patent, or copyright protection? | 1.1 | 1.0 | 3–4 |
| `p1_signed_customers` | Do you have signed contracts or paying customers beyond friends/family? | 2.3 | 1.5 | 4–5 |
| `p1_sales_pipeline` | Do you have a structured sales pipeline with tracked leads? | 1.8 | 1.8 | 5 |
| `p1_pmf_evidence` | Do you have evidence of product-market fit (e.g., NPS > 40, retention > 40%)? | 2.0 | 2.2 | 5 |
| `p1_mom_growth` | Are you achieving month-over-month revenue growth above 10%? | 2.4 | 2.5 | 5–6 |
| `p1_cac_defined` | Do you know your exact customer acquisition cost (CAC)? | 1.9 | 2.3 | 5–6 |
| `p1_multi_segment` | Have you expanded to a second customer segment or geographic market? | 1.8 | 2.8 | 6 |
| `p1_team_gt5` | Does your team have more than 5 full-time employees? | 1.6 | 2.6 | 6 |

(24 items total; trimmed here for clarity. Full bank in `item_bank.json`.)

**Phase 2 Pool — Axis Targeters (4 items × 10 axes = 40 items)**

Each axis has 4 items at different difficulty levels. Phase 2 selects the 2 closest to `θ̂` for each axis.

Example for the `market` axis:
| id | Question | a | b |
|---|---|---|---|
| `mkt_s1` | Who is your target customer and what specific problem do they have? | 1.2 | −2.0 |
| `mkt_s2` | What evidence do you have for total addressable market size in Tunisia? | 1.5 | −0.5 |
| `mkt_s3` | Who are your top 3 competitors and what is your differentiation? | 1.6 | 0.8 |
| `mkt_s4` | What is your estimated market share and expansion timeline? | 1.4 | 2.0 |

If `θ̂ = 0.3` (Stage 3), Phase 2 picks `mkt_s2` (b=−0.5, distance 0.8) and `mkt_s3` (b=0.8, distance 0.5) for the market axis. A Stage 1 founder would get `mkt_s1` and `mkt_s2` instead.

---

## 5. Algorithm Implementation (Python)

The CAT session manager lives in the orchestrator. It exposes a stateless interface: given a session's item history, return the next item. Session state is stored in `diagnostic_sessions.cat_state` (JSONB column).

### `backend/orchestrator/app/cat/irt.py`

```python
# Pure IRT numerics — no database, no I/O, no Ollama.
import json
import math
from pathlib import Path

import numpy as np

THETA_GRID = np.linspace(-4.0, 4.0, 81)          # 81 points, step 0.1
LOG_PRIOR  = -0.5 * THETA_GRID ** 2 - 0.5 * math.log(2 * math.pi)   # log N(0,1)

ITEM_BANK: dict = json.loads(
    (Path(__file__).parent / "item_bank.json").read_text()
)


def _p(theta: np.ndarray, a: float, b: float) -> np.ndarray:
    """2PL item response function: P(u=1 | θ, a, b)."""
    return 1.0 / (1.0 + np.exp(-a * (theta - b)))


def log_likelihood_grid(responses: list[tuple[str, int]]) -> np.ndarray:
    """
    responses: [(item_id, u), ...] where u ∈ {0, 1}
    Returns log L(u | θ) for each point in THETA_GRID.
    """
    log_l = np.zeros(len(THETA_GRID))
    for item_id, u in responses:
        item = ITEM_BANK[item_id]
        p = _p(THETA_GRID, item["a"], item["b"])
        p = np.clip(p, 1e-9, 1 - 1e-9)      # numerical safety
        log_l += u * np.log(p) + (1 - u) * np.log(1 - p)
    return log_l


def eap_estimate(responses: list[tuple[str, int]]) -> tuple[float, float]:
    """
    Returns (θ̂_EAP, SE) given the current response history.
    """
    log_w = log_likelihood_grid(responses) + LOG_PRIOR
    # Log-sum-exp for numerical stability
    log_z = log_w.max() + np.log(np.exp(log_w - log_w.max()).sum())
    weights = np.exp(log_w - log_z)           # sums to 1

    theta_hat = float(np.dot(THETA_GRID, weights))
    variance   = float(np.dot((THETA_GRID - theta_hat) ** 2, weights))
    se         = math.sqrt(variance)
    return theta_hat, se


def item_information(item_id: str, theta: float) -> float:
    """Fisher information of item j at ability θ: I_j(θ) = a² P(1−P)."""
    item = ITEM_BANK[item_id]
    p = _p(np.array([theta]), item["a"], item["b"])[0]
    return item["a"] ** 2 * p * (1 - p)


def select_next_item(
    responses: list[tuple[str, int]],
    theta_hat: float,
    pool: str = "phase1",           # "phase1" or axis name for phase2
    max_per_pool: int | None = None,
) -> str | None:
    """
    Returns the item_id with maximum Fisher information at theta_hat,
    excluding already-answered items.
    Content balancing: if max_per_pool is set, cap items from this pool.
    """
    answered = {item_id for item_id, _ in responses}
    candidates = [
        item_id for item_id, item in ITEM_BANK.items()
        if item["pool"] == pool and item_id not in answered
    ]
    if not candidates:
        return None

    return max(candidates, key=lambda iid: item_information(iid, theta_hat))


def theta_to_stage(theta: float) -> int:
    """Map continuous θ to 1–6 stage integer."""
    boundaries = [-1.75, -0.75, 0.25, 1.25, 2.25]
    for stage, boundary in enumerate(boundaries, start=1):
        if theta < boundary:
            return stage
    return 6
```

### `backend/orchestrator/app/cat/session.py`

```python
import asyncio
from dataclasses import dataclass, field

from .irt import eap_estimate, select_next_item, theta_to_stage

SE_THRESHOLD  = 0.35    # stop when estimate is this precise
MAX_PHASE1    = 12      # hard ceiling on Phase 1 items
AXES          = [
    "ideation", "market", "product", "brand", "business_model",
    "legal", "operations", "marketing", "sales", "scalability",
]
PHASE2_PER_AXIS = 2     # ask this many targeted questions per axis


@dataclass
class CatState:
    phase: int = 1                          # 1 or 2
    responses: list[tuple[str, int]] = field(default_factory=list)
    theta_hat: float = 0.0
    se: float = 1.2                         # prior SE before any items
    stage: int | None = None
    phase2_answered: dict[str, int] = field(default_factory=dict)   # axis → count
    complete: bool = False


def next_item(state: CatState) -> str | None:
    """
    Given the current CAT state, return the next item_id to present,
    or None if the test is complete.
    """
    if state.complete:
        return None

    if state.phase == 1:
        if state.responses:
            state.theta_hat, state.se = eap_estimate(state.responses)

        # Stopping criterion for Phase 1
        phase1_count = sum(
            1 for iid, _ in state.responses
            if _is_phase1(iid)
        )
        if state.se < SE_THRESHOLD or phase1_count >= MAX_PHASE1:
            state.stage = theta_to_stage(state.theta_hat)
            state.phase = 2
            return next_item(state)   # recurse into Phase 2

        return select_next_item(state.responses, state.theta_hat, pool="phase1")

    # Phase 2: pick the axis with fewest answered items, select its best item
    for axis in AXES:
        answered_for_axis = state.phase2_answered.get(axis, 0)
        if answered_for_axis < PHASE2_PER_AXIS:
            item_id = select_next_item(
                state.responses, state.theta_hat, pool=axis
            )
            if item_id:
                return item_id

    # All axes saturated
    state.complete = True
    return None


def record_response(state: CatState, item_id: str, response: int) -> None:
    """Record a 0/1 response and update phase2 axis counter if applicable."""
    state.responses.append((item_id, response))
    axis = _item_axis(item_id)
    if axis in AXES:
        state.phase2_answered[axis] = state.phase2_answered.get(axis, 0) + 1


def _is_phase1(item_id: str) -> bool:
    from .irt import ITEM_BANK
    return ITEM_BANK.get(item_id, {}).get("pool") == "phase1"


def _item_axis(item_id: str) -> str | None:
    from .irt import ITEM_BANK
    return ITEM_BANK.get(item_id, {}).get("pool")  # pool == axis name in Phase 2
```

---

## 6. Rust Endpoint in `moufida-signal`

The numerically expensive part of the EAP update (81-point grid × N answered items) runs in Python, but for higher throughput or real-time updates, it can be offloaded to a new `signal` endpoint. Following the pattern of `/cbm/score`, add `POST /cat/eap`:

```rust
// signal/src/cat.rs

use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct ItemResponse {
    pub a: f64,       // discrimination
    pub b: f64,       // difficulty
    pub u: u8,        // 0 or 1
}

#[derive(Deserialize)]
pub struct EapRequest {
    pub responses: Vec<ItemResponse>,
}

#[derive(Serialize)]
pub struct EapResponse {
    pub theta_hat: f64,
    pub se: f64,
    pub stage: u8,
    pub posterior: Vec<f64>,     // optional: 81-point posterior for UI visualization
}

const GRID_MIN: f64 = -4.0;
const GRID_MAX: f64 =  4.0;
const GRID_N:   usize = 81;
const GRID_STEP: f64 = (GRID_MAX - GRID_MIN) / (GRID_N as f64 - 1.0);

pub fn eap(req: &EapRequest) -> EapResponse {
    // Build log-weight vector: log L(u | θ_k) + log π(θ_k)
    let mut log_w = [0.0_f64; GRID_N];
    for (k, lw) in log_w.iter_mut().enumerate() {
        let theta = GRID_MIN + k as f64 * GRID_STEP;
        // log N(0,1) prior
        *lw = -0.5 * theta * theta - 0.5 * (2.0 * std::f64::consts::PI).ln();
        // log likelihood
        for resp in &req.responses {
            let logit = resp.a * (theta - resp.b);
            let log_p = -(-logit).exp().ln_1p();     // log sigmoid(logit)
            let log_1mp = -(logit).exp().ln_1p();    // log (1 - sigmoid(logit))
            *lw += if resp.u == 1 { log_p } else { log_1mp };
        }
    }

    // Log-sum-exp normalization
    let log_z = log_w.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
        + log_w.iter().map(|&x| (x - log_w.iter().cloned().fold(f64::NEG_INFINITY, f64::max)).exp()).sum::<f64>().ln();
    let weights: Vec<f64> = log_w.iter().map(|&lw| (lw - log_z).exp()).collect();

    // EAP mean and SE
    let mut theta_hat = 0.0_f64;
    let mut variance  = 0.0_f64;
    for (k, &wk) in weights.iter().enumerate() {
        let theta = GRID_MIN + k as f64 * GRID_STEP;
        theta_hat += theta * wk;
    }
    for (k, &wk) in weights.iter().enumerate() {
        let theta = GRID_MIN + k as f64 * GRID_STEP;
        variance += (theta - theta_hat).powi(2) * wk;
    }
    let se = variance.sqrt();

    EapResponse {
        theta_hat: (theta_hat * 1000.0).round() / 1000.0,
        se:        (se * 1000.0).round() / 1000.0,
        stage:     theta_to_stage(theta_hat),
        posterior: weights,
    }
}

fn theta_to_stage(theta: f64) -> u8 {
    match theta {
        t if t < -1.75 => 1,
        t if t < -0.75 => 2,
        t if t < 0.25  => 3,
        t if t < 1.25  => 4,
        t if t < 2.25  => 5,
        _               => 6,
    }
}
```

**Latency:** 81 grid points × N items ≤ 12 = ≤ 972 floating-point operations. This executes in under 50 microseconds — effectively free compared to any network round-trip.

---

## 7. Orchestrator API — New Endpoints

Two endpoints added to `backend/orchestrator/app/intake_router.py`:

```
POST /intake/next
  Request:  { "session_id": UUID, "last_response": { "item_id": str, "value": int } | null }
  Response: {
    "item_id": str,
    "question": str,
    "phase": 1 | 2,
    "axis": str | null,          # null in Phase 1
    "theta_hat": float,          # current stage estimate (shown to user as stage progress)
    "se": float,
    "items_answered": int,
    "complete": false
  }
  OR (when complete):
  {
    "complete": true,
    "stage": 1–6,
    "theta_hat": float,
    "posterior": [81 floats],    # full posterior for UI distribution plot
    "axis_evidence": { axis: [question+answer pairs] }
  }

GET /intake/calibrate
  Triggers offline re-estimation of (a, b) parameters from score_snapshots.
  Writes updated item_bank.json. Admin-only.
```

The session state (`CatState`) is serialized to JSONB and stored in `diagnostic_sessions.cat_state`. Each call to `/intake/next` is stateless from the API's perspective — the full history is embedded in the state.

---

## 8. Item Parameter Calibration (Offline)

The initial `(a, b)` parameters are domain-expert priors. As `diagnostic_sessions` accumulates responses, they can be calibrated from data using **Marginal Maximum Likelihood Estimation (MMLE)** — the standard IRT calibration method.

### Calibration script: `scripts/calibrate_item_bank.py`

```python
"""
Calibrate IRT item parameters from accumulated session data.
Requires: scipy (optimize), numpy.
Run periodically when sessions table has ≥ 200 complete diagnostics.
"""
import json
import numpy as np
from scipy.optimize import minimize
from db import fetch_item_responses   # returns List[{item_id, u, session_theta}]

def nll_2pl(params, responses_for_item):
    """Negative log-likelihood for one item's (a, b) given response data."""
    a, b = params
    a = max(a, 0.1)                 # discrimination must be positive
    total_nll = 0.0
    for theta, u in responses_for_item:
        p = 1.0 / (1.0 + np.exp(-a * (theta - b)))
        p = np.clip(p, 1e-9, 1 - 1e-9)
        total_nll -= u * np.log(p) + (1 - u) * np.log(1 - p)
    return total_nll

def calibrate(item_bank_path: str):
    item_bank = json.load(open(item_bank_path))
    all_responses = fetch_item_responses()   # grouped by item_id

    for item_id, item in item_bank.items():
        item_responses = [
            (r["session_theta"], r["u"])
            for r in all_responses
            if r["item_id"] == item_id and r["session_theta"] is not None
        ]
        if len(item_responses) < 30:
            continue    # not enough data; keep prior

        result = minimize(
            nll_2pl,
            x0=[item["a"], item["b"]],
            args=(item_responses,),
            method="L-BFGS-B",
            bounds=[(0.1, 3.0), (-4.0, 4.0)],
        )
        if result.success:
            item["a"] = round(result.x[0], 3)
            item["b"] = round(result.x[1], 3)
            item["calibrated"] = True

    json.dump(item_bank, open(item_bank_path, "w"), indent=2)
    print(f"Calibrated {sum(1 for i in item_bank.values() if i.get('calibrated'))} items.")
```

The `session_theta` field (the EAP estimate at session end) serves as the proxy for the "true" latent ability — the standard approach for calibration when no independent ability measure exists (known as *anchored calibration*).

---

## 9. UI/UX Integration

### Adaptive intake screen

The intake renders questions one at a time. Below the question, a subtle progress indicator shows — not a fixed "question N of 30," but a **stage probability distribution**:

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Do you have evidence that potential customers would pay         │
│  for your solution?                                              │
│                                                                  │
│  ○ Yes, explicit verbal commitment or signed LOI                 │
│  ○ Some indirect signals (interest, follows, waitlist)           │
│  ○ Not yet — still exploring                                     │
│                                                                  │
│  ─────────────────────────────────────────────────────────────   │
│  Moufida is learning where you are:                             │
│                                                                  │
│  Stage 1 ░░░░ 2%                                                │
│  Stage 2 ████████░░░░ 38%  ◄──                                  │
│  Stage 3 ███████░░░░░ 35%                                        │
│  Stage 4 ████░░░░░░░░ 19%                                        │
│  Stage 5 ░░░░░░░░░░░░  5%                                        │
│  Stage 6 ░░░░░░░░░░░░  1%                                        │
│                                                                  │
│  Question 4 of ~10  ·  Getting clearer...                       │
└──────────────────────────────────────────────────────────────────┘
```

The distribution bar directly shows the posterior `weights[81]` collapsed into 6 stage buckets. It updates after every response. Founders experience it as Moufida visibly forming an opinion about them — a qualitatively different feeling from filling out a form.

### Phase transition reveal

When Phase 1 completes, there is a brief reveal moment before Phase 2 begins:

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  [Moufida pixel character — excited pose]                        │
│                                                                  │
│  "Based on your answers, I think you're at                      │
│   Stage 3: Structuration."                                       │
│                                                                  │
│  Market Validation ✓  →  Structuration [You are here]  →  ...   │
│                                                                  │
│  Now I'll ask a few more targeted questions to understand        │
│  each dimension of your startup. This will take ~3 minutes.     │
│                                                                  │
│  [Continue →]                                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

This reveal is a natural break that reduces fatigue and creates a sense of progress. The founder feels validated — Moufida has already understood their stage — before the deeper axis questions begin.

### Perception gap display (post-assessment)

At results time, if the founder self-declared a stage at intake start:

```
You told us: Stage 4 (Fundraising Ready)
Moufida's assessment: Stage 2–3 boundary (θ̂ = −0.42)

  Perception gap: You're approximately 1.5 stages ahead of where
  your responses place you.

  This is very common. It suggests either:
  · Some Stage 3 milestones haven't been completed yet
  · Or some completed milestones lack external evidence

  [See exact gaps →]
```

---

## 10. New DB Column

A single column addition to the existing `diagnostic_sessions` table:

```sql
-- db/migrations/021_cat_state.sql
ALTER TABLE diagnostic_sessions
  ADD COLUMN cat_state      JSONB,      -- serialized CatState (session history)
  ADD COLUMN cat_theta_hat  REAL,       -- final θ̂ at session completion
  ADD COLUMN cat_se         REAL,       -- final SE
  ADD COLUMN cat_stage      SMALLINT;   -- 1–6, derived from theta_hat

CREATE INDEX ON diagnostic_sessions (cat_stage)
  WHERE cat_stage IS NOT NULL;
```

The `cat_state` JSONB stores the complete item response history (item_id + response pairs), enabling session resumability and post-hoc calibration. No separate table is needed.

---

## 11. What This Is NOT

**Not a neural network.** The IRT model is a simple logistic function with two parameters per item. There is no training, no backpropagation, no GPU. The Python implementation is ~80 lines; the Rust endpoint is ~60 lines. The complexity is in the statistical reasoning, not the computation.

**Not gamification.** The stage distribution UI looks like a game mechanic, but it is directly derived from the posterior probability over `θ`. Every bar represents the genuine Bayesian belief that the founder is in that stage. The display is honest, not theatrical.

**Not a replacement for axis microservices.** The 10 axis services (`/market/execute`, `/sales/execute`, etc.) still run. The CAT changes what questions they receive as input — targeted, stage-appropriate questions rather than a fixed universal set. Their scoring logic is untouched.

**Not a fixed branching tree.** Branching intake forms ("if you answer yes to Q1, go to Q3; otherwise go to Q7") are handcrafted decision trees. CAT is principled: item selection is always `argmax_j I_j(θ̂)`, derived from the data, not from editorial judgment. Any question can follow any other depending on the founder's responses.

**Not reinventing the GMAT.** GMAT adaptive testing optimizes for a single cognitive ability trait under strict fairness and exposure control constraints (every test-taker must receive a statistically equivalent test). Moufida's application is simpler: a single stage estimate, a small item bank (64 items), no fairness constraints, and a second phase that is explicitly not adaptive. The IRT math is the same; the deployment context is much simpler.

---

## 12. Files to Create / Modify

```
backend/orchestrator/app/
  cat/
    __init__.py
    irt.py              ← 2PL functions: P_j, information, EAP, theta_to_stage
    session.py          ← CatState dataclass, next_item(), record_response()
    item_bank.json      ← 64 items with (a, b, pool, question_text, axis)
  intake_router.py      ← add POST /intake/next, GET /intake/calibrate

signal/src/
  cat.rs                ← EapRequest/EapResponse, eap() Rust impl
  main.rs               ← add POST /cat/eap route

scripts/
  calibrate_item_bank.py    ← offline MMLE calibration from session history

db/migrations/
  021_cat_state.sql         ← ADD COLUMN cat_state, cat_theta_hat, cat_se, cat_stage

frontend/src/components/intake/
  AdaptiveIntake.tsx         ← one-question-at-a-time UI with posterior bars
  StagePosteriorBar.tsx      ← 6-bar posterior distribution component
  PhaseReveal.tsx            ← transition screen between Phase 1 and Phase 2
```

---

## 13. Relationship to the Other Research Contributions

CAT slots at the beginning of the pipeline. The three papers now cover intake → retrieval → scoring end-to-end:

```
                    ┌──────────────────────────────────────────┐
                    │  Computerized Adaptive Testing            │
                    │  (this document)                          │
                    │                                           │
  founder ───────► │  Phase 1: stage estimate (θ̂)             │
                    │  Phase 2: targeted axis questions         │
                    │  → structured evidence per axis           │
                    └──────────────────┬───────────────────────┘
                                       │ axis evidence + θ̂
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │  Contrastive Axis Direction Probe         │
                    │  (contrastive-axis-directions-embedding)  │
                    │                                           │
                    │  For each axis query: retrieve KB chunks  │
                    │  re-ranked by on-axis direction score     │
                    │  → axis-aligned evidence from KB          │
                    └──────────────────┬───────────────────────┘
                                       │ axis evidence + KB chunks
                                       ▼
                    ┌──────────────────────────────────────────┐
                    │  Concept Bottleneck Layer                 │
                    │  (concept-bottleneck-diagnostic-layer)    │
                    │                                           │
                    │  LLM scores each concept                  │
                    │  Rust computes weighted axis score        │
                    │  → bottleneck concept identified          │
                    └──────────────────────────────────────────┘
```

CAT improves what goes **in** (stage-appropriate questions, targeted evidence).
RepE improves the **retrieval** (axis-aligned knowledge).
CBM improves what comes **out** (decomposable, bottleneck-identified scores).

The `θ̂` from CAT also enriches CBM: prior weights in `cbm_weights.json` can be stage-conditioned — at Stage 1, `icp_specificity` weight should be high; at Stage 5, `revenue_traction` weight should dominate. CAT provides the stage context that makes CBM's weights situationally appropriate.
