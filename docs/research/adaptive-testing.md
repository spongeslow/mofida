# Research: Computerized Adaptive Testing (CAT) for Startup Diagnostics

## Papers

**IRT model and Fisher information for item selection:**
> Lord, F. M. (1977). "Practical applications of item characteristic curve theory." *Journal of Educational Measurement, 14*(2), 117–138.

**Adaptive ability estimation — the EAP update rule:**
> Bock, R. D., & Mislevy, R. J. (1982). "Adaptive EAP estimation of ability in a microcomputer environment." *Applied Psychological Measurement, 6*(4), 431–444. [doi.org/10.1177/014662168200600402](https://doi.org/10.1177/014662168200600402)

**CAT system design:**
> Wainer, H. (Ed.). (2000). *Computerized Adaptive Testing: A Primer* (2nd ed.). Lawrence Erlbaum Associates.

**Polytomous (graded-scale) extension:**
> Samejima, F. (1997). "The graded response model." In van der Linden & Hambleton (Eds.), *Handbook of Modern Item Response Theory.* Springer.

---

## The Core Idea — Plain Language

Imagine a doctor trying to determine whether a patient has mild, moderate, or severe hypertension. They have 40 diagnostic tests. A good doctor starts with a blood pressure reading. If it's normal, they stop. If it's elevated, they run the next most informative test *for this specific patient's reading*. They converge on a diagnosis in 6 tests instead of 40.

That is **Computerized Adaptive Testing (CAT)**. Instead of giving every founder the same fixed questionnaire, CAT dynamically selects the next question that provides maximum information about the founder's underlying position on the measured trait (startup maturity stage).

The math is **Item Response Theory (IRT)**, which has underpinned standardised adaptive testing (GMAT, GRE, TOEFL, PISA) since the 1980s.

---

## The Key Insight: Questions Have Difficulty and Discrimination

In a fixed questionnaire, all questions are treated as equally informative. IRT recognises they are not.

**Discrimination (parameter `a`):** How sharply does this question separate founders at different stages?
- "Do you have paying customers?" — high discrimination: clearly separates Stage 2 (no) from Stage 4 (yes)
- "Are you passionate about your idea?" — zero discrimination: everyone says yes

**Difficulty (parameter `b`):** At what stage level does the typical founder give a strong positive answer?
- "Have you thought about the problem?" — low difficulty (even Stage 0 founders say yes)
- "Do you have MoM revenue growth above 10%?" — high difficulty (only Stage 5–6 founders say yes)

**Core principle:** Ask a question at the right difficulty for where you think the founder is. A Stage 5 question for a Stage 2 founder provides no information (everyone at Stage 2 answers no). A Stage 2 question is maximally informative.

---

## The 2-Parameter Logistic (2PL) IRT Model

The probability that a founder at stage θ answers question `j` correctly (positively):

```
P(u_j = 1 | θ) = 1 / (1 + exp(-a_j × (θ - b_j)))
```

Where:
- `a_j` = discrimination parameter for question j
- `b_j` = difficulty parameter for question j
- `θ` = founder's latent maturity stage (−3 to +3 scale, mapped to 0–5 stages)

This is a sigmoid curve: at `θ = b_j`, there is a 50% chance of a positive answer. A high `a_j` makes the curve steep (sharp discrimination). A low `a_j` makes it flat (poor discrimination).

---

## Fisher Information and Item Selection

The information provided by question `j` at ability level `θ`:

```
I_j(θ) = a_j² × P_j(θ) × (1 - P_j(θ))
```

This is highest when `θ ≈ b_j` (difficulty matches ability) and `a_j` is high (sharp discrimination). Item selection rule: **always ask the question with maximum Fisher information at the current θ estimate.**

---

## Bayesian EAP Estimation (Bock & Mislevy, 1982)

After each response, the estimate of θ is updated using Expected A Posteriori (EAP) estimation:

```
θ̂ = ∫ θ × L(θ|u₁,...,uₙ) × p(θ) dθ
     ──────────────────────────────────
     ∫ L(θ|u₁,...,uₙ) × p(θ) dθ
```

Where:
- `L(θ|u₁,...,uₙ)` = likelihood of the observed response sequence given θ
- `p(θ)` = prior over θ (Gaussian with mean 0)

In practice, the integral is approximated over a discrete grid of θ values. The EAP gives both the estimate (`θ̂`) and the posterior standard error (`SE(θ̂)`).

---

## The CAT Loop in Moufida

```
Initial state: θ̂ = 0, SE(θ̂) = 1.0 (maximum uncertainty)

Loop:
  1. Select item j* = argmax_j I_j(θ̂)  [but exclude already-asked items]
  2. Return question j* to the founder (via the UI)
  3. Receive answer u_j* ∈ {0, 1}
  4. Update θ̂ and SE(θ̂) via EAP
  5. If SE(θ̂) < 0.40 OR ≥ 12 items answered:
       → STOP, map θ̂ to one of 6 maturity stages
     Else:
       → Go to step 1

Convergence: typically 8–15 questions
(vs. 30+ questions in a fixed questionnaire)
```

---

## Two-Phase Design

The GMAT estimates a single latent trait (verbal ability). Moufida estimates maturity stage **and** must collect profile fields across 10 diagnostic axes. This requires a two-phase design:

**Phase 1 — Stage Discriminators (pure CAT):**
Questions from the stage discriminator pool. Maximises Fisher information until SE < 0.40. Converges in ~8–12 items. Output: reliable θ̂ and a maturity stage estimate.

**Phase 2 — Axis-Specific Questions (targeted):**
Once the stage is estimated, the system selects questions closest to θ̂ from each axis-specific pool. These collect the specific profile fields needed for scoring (team size, revenue model, customer validation evidence, etc.).

---

## Stateless Architecture

Moufida's CAT implementation is architecturally unusual: **the server is entirely stateless.**

On every call to `POST /intake/next`, the client sends the full response history `[{item_id, answer}, ...]`. The server re-derives θ̂ from scratch on each call.

**Why stateless?**
- No session management on the server
- No Redis or database reads per question
- Horizontally scalable by design
- Simple retry logic (just replay the history)
- The computation is fast (pure Python arithmetic on a tiny grid)

The trade-off is slightly higher network payload per request, which is negligible for the item counts involved (< 15 items, each a small JSON object).

---

## Item Bank

The item bank is a curated set of diagnostic questions, each annotated with:
- `a` (discrimination) and `b` (difficulty) parameters
- `axis` — which diagnostic axis this question populates
- `field` — which profile field the answer maps to
- `language` — `fr`, `ar`, or `both`
- `response_type` — binary / ordinal / free-text

Branching rules: certain questions are gated on prior answers (e.g., "what is your MRR?" only appears if a prior question established that there is some revenue).

---

## Why This Matters Over a Standard Questionnaire

| Fixed questionnaire | Moufida CAT |
|---|---|
| 30+ questions every time | 8–15 questions |
| Same questions for all founders | Questions tailored to the founder's signal |
| No information about measurement precision | SE(θ̂) is known — confidence in the stage estimate |
| Stage assigned by sum score | Stage assigned by maximum-likelihood IRT estimate |
| Bores early-stage founders with growth questions | Only asks relevant-difficulty questions |

A founder who clearly demonstrates Stage 5 (growth) signals in their first 3 answers will never be asked "do you have a legal entity yet?" — that question provides zero information once Stage 5 is established.

---

## Implementation in Moufida

The CAT engine lives in `backend/orchestrator/app/intake_router.py`:
- Pure Python 2PL IRT, no numpy dependency
- EAP computed over a 33-point Gauss-Hermite quadrature grid
- The Rust signal service (`POST /cat/eap`) provides an accelerated fallback

The item bank is stored in `backend/orchestrator/app/item_bank.json`.

Graded (polytomous) responses (yes/no/partially/not yet) use the Samejima Graded Response Model extension — the same IRT framework with additional category threshold parameters.
