# Research: Contrastive Axis Direction Probe

## Papers

**Primary — the method:**
> Zou, A., et al. (2023). "Representation Engineering: A Top-Down Approach to AI Transparency." *arXiv:2310.01405.* [arxiv.org/abs/2310.01405](https://arxiv.org/abs/2310.01405)

**Theoretical foundation:**
> Park, K., et al. (2023). "The Linear Representation Hypothesis and the Geometry of Large Language Models." *arXiv:2311.03658.*

**Practical probing reference:**
> Gurnee, W., et al. (2023). "Finding Neurons in a Haystack: Case Studies with Sparse Probing." *TMLR 2023.* [arXiv:2305.01610](https://arxiv.org/abs/2305.01610)

---

## The Core Idea — Plain Language

Every piece of text that passes through an embedding model gets turned into a vector — a list of 1024 numbers — in a high-dimensional space. The **Linear Representation Hypothesis** says: *concepts are directions in this space, not scattered regions.*

If you take all documents about "market validation" and compute their average embedding, then take all other documents and compute their average, the *difference* between these two averages is a direction — a vector that points from "not about market validation" toward "strongly about market validation."

**Representation Engineering** (Zou et al., 2023) originally applied this idea to find directions for abstract concepts like *honesty* and *power* inside LLM residual streams. Moufida applies the same geometry to retrieval embeddings in the knowledge base to find directions for the nine diagnostic business axes.

---

## The Contrastive Pairs Intuition

To find the "market" direction, you need:
1. Documents that **strongly express** market thinking (positive examples: chunks tagged `market`)
2. Documents that **don't** (negative examples: all other KB chunks)

Then:
```
direction_market = normalize( mean(embeddings_positive) - mean(embeddings_negative) )
```

That's the market direction. It's a unit vector in 1024-dimensional space that, when projected onto any new document embedding, tells you how much that document "points toward" market-relevant thinking.

---

## The Math

Let `E_pos` be embeddings of positive examples (documents tagged for axis `a`), `E_neg` the rest.

**Step 1 — Compute the contrastive mean:**
```
μ_pos = (1/|E_pos|) Σ eᵢ
μ_neg = (1/|E_neg|) Σ eⱼ
```

**Step 2 — Find the direction and normalise:**
```
d̂_a = normalize(μ_pos - μ_neg)   [unit vector, 1024-dim]
```

**Step 3 — Project any new embedding:**
```
raw_score_a(e) = dot(e, d̂_a)   ∈ ℝ
```

**Step 4 — Normalise to [0, 1]:**
```
s̃_a(e) = sigmoid( (raw_score_a(e) - μ_s) / σ_s )
```
where `μ_s` and `σ_s` are pre-computed from the full KB corpus.

**For all 9 axes simultaneously — one matrix multiply:**
```
D = [d̂_ideation | d̂_market | ... | d̂_sales]   shape: (1024 × 9)
axis_relevance(e) = normalize(Dᵀ · e)           shape: (9,)
```

This executes in < 5 microseconds on any CPU — zero perceptible latency.

---

## Why This Makes Retrieval Better

Standard retrieval asks: "is this chunk similar to the query?" The axis probe asks: "is this chunk relevant to the *current diagnostic axis*?"

These are different questions. Consider:

```
Query: "customer acquisition in Tunisia"
Chunk: "BTS proposes micro-credit without real collateral..."

Dense similarity score: 0.61  (high — both about Tunisian business)
Market axis relevance:  0.31  (low — this is about financing, not customer acquisition)
Business model axis:    0.78  (high — this is fundamentally about funding model)
```

Without the probe, this chunk ranks high in the market axis retrieval because of superficial lexical similarity. With the probe, its low market-axis relevance score down-weights it (30% blend into the final RRF score), and genuinely market-relevant chunks rank higher.

---

## Two Uses in Moufida

### Use 1: Retrieval Re-Ranking

In `backend/rag/app/retrieve.py`, when `current_axis` is provided:

```python
final_score = 0.7 × rrf_score + 0.3 × axis_relevance[current_axis]
```

The 30/70 blend preserves the semantic relevance of BM25+dense while adding axis-awareness. The axis direction signal acts as a soft filter, not a hard gate.

### Use 2: Automatic Chunk Tagging at Ingest

Every newly ingested document — user-uploaded PDF, daemon-scraped competitor page, grant notice — is automatically tagged with its top-2 axes:

```python
auto_axes = await _tag_axes(embedding, signal_client)
# → ["business_model", "legal"]
```

This replaces manual `score_dimensions` tagging for new content. The knowledge base stays self-organising.

---

## Computing the Directions (One-Off Offline Step)

The `scripts/compute_axis_directions.py` script:

1. Scrolls all Qdrant KB vectors with payloads
2. Groups chunks by axis using `score_dimensions` + `type` tags:
   - `market` chunks → positive for market axis
   - `legal_regulatory` type → positive for legal axis
   - `innovation` chunks → positive for ideation + product + brand
3. Computes contrastive means and normalises
4. Computes (mean, std) normalization stats over the full KB
5. Saves `probe_directions.npy` (9×1024 float32 matrix, ~36KB)
6. POSTs to `signal:8010/probe/install`

Run after initial KB ingest:
```bash
docker compose --profile tools run --rm compute-directions
```

Until this runs, the probe returns 503 and retrieval falls back to standard RRF. Nothing breaks.

---

## What This Is NOT

**Not a classifier.** A classifier outputs a single label. The axis probe outputs a continuous score on all 9 axes simultaneously — a document can be 0.78 business_model AND 0.54 legal AND 0.31 market at the same time.

**Not topic modeling (LDA/NMF).** Topic models infer latent topics from co-occurrence. Axis directions are supervision-driven: they find the direction that separates documents labelled for axis `a` from all others. The directions are grounded in the existing KB taxonomy.

**Not fine-tuning the embedding model.** The `bge-m3` model is frozen. We learn a lightweight linear probe (9 directions = 9,216 float32 values) on top of its frozen embeddings. The geometry already exists in the embedding space — we are measuring it.

---

## Relationship to the CBM Layer

These two research contributions operate at different layers of the same pipeline:

```
KB chunks → embed → Axis Direction Probe → axis-aware retrieved chunks
                                                   │
                                         LLM Axis Diagnosis (better evidence)
                                                   │
                                         Concept Bottleneck Layer → bottleneck
```

The axis directions improve the **input** to the LLM (better, more axis-aligned evidence).
The CBM improves the **output** of the LLM (decomposable, bottleneck-identified score).

Together they close the interpretability loop end-to-end: from retrieval to scoring to actionable insight.

---

## Implementation

- `scripts/compute_axis_directions.py` — offline direction computation
- `signal/src/probe.rs` — Rust `AxisProbe` struct with `project()` and `top_axes()`
- `signal/assets/probe_directions.npy` — 9×1024 float32 matrix (generated, committed)
- `signal/assets/probe_stats.json` — per-axis mean/std for normalization
- `backend/rag/app/retrieve.py` — axis-aware re-ranking integration
- `backend/rag/app/ingest.py` — auto-tagging at ingest time
- `frontend/src/components/shared/EvidenceTrace.tsx` — axis relevance display
