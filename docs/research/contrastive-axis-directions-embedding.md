# Contrastive Axis Directions in Embedding Space

## Papers to Read

**Primary — the method:**
> Zou, A., Phan, L., Chen, S., Campbell, J., Guo, P., Ren, R., Pan, A., Yin, X.,
> Mazeika, M., Dombrowski, A. K., Goel, S., Li, N., Byun, M. J., Wang, Z.,
> Mallen, A., Shen, S., Vyas, V., Bhatt, U., Steinhardt, J., Hendrycks, D., &
> Fredrikson, M. (2023).
> **"Representation Engineering: A Top-Down Approach to AI Transparency."**
> *arXiv preprint arXiv:2310.01405.*
> https://arxiv.org/abs/2310.01405

**Theoretical foundation — why linear directions exist:**
> Park, K., Choe, Y. J., & Veitch, V. (2023).
> **"The Linear Representation Hypothesis and the Geometry of Large Language Models."**
> *arXiv preprint arXiv:2311.03658.*
> https://arxiv.org/abs/2311.03658

**Practical probing reference:**
> Gurnee, W., Nanda, N., Pauly, M., Harvey, K., Troyer, B., & Tegmark, M. (2023).
> **"Finding Neurons in a Haystack: Case Studies with Sparse Probing."**
> *Transactions on Machine Learning Research (TMLR 2023).*
> https://arxiv.org/abs/2305.01610

---

## 1. The Core Idea — Plain Language

Every word, sentence, and document that passes through a language model gets turned into a vector — a list of numbers — called an embedding. These vectors live in a high-dimensional space (for `bge-m3`, Moufida's embedding model, that's 1024 dimensions).

The key insight of the **Linear Representation Hypothesis** (Park et al., 2023) is: **concepts are directions in this space, not scattered regions**. If you take all documents about "market validation" and compute their average embedding, then take all documents about *everything else* and compute their average, the difference between these two averages is a *direction* — a single vector that points from "not about market validation" toward "strongly about market validation."

This direction is what **Representation Engineering** (Zou et al., 2023) calls a **Representation Reading Vector (RRV)** or informally a "concept direction". The original paper found directions for abstract concepts like *honesty*, *power*, and *emotion* inside LLM residual stream activations. We apply the same geometry to embedding vectors in Moufida's knowledge base.

### The Contrastive Pairs Intuition

To find the "market" direction, you don't need to understand embedding geometry. You just need:

1. A set of documents that **strongly express** market thinking (positive examples)
2. A set of documents that **don't** (negative examples)

Compute:
```
direction_market = normalize( mean(embeddings_positive) − mean(embeddings_negative) )
```

That's the market direction. It's a unit vector in 1024-dimensional space that, when you project any new document embedding onto it, tells you how much that document "points toward" market-relevant thinking.

### Why This Works

Two documents about "CAC in B2B SaaS" and "customer acquisition cost for enterprise software" will have similar embeddings — they mean the same thing. Their embeddings will both be far in the "market/sales" direction and close to zero in the "legal" direction. This isn't magic: the embedding model (bge-m3) learned this structure from training on vast text. We're just measuring it.

---

## 2. The Math

Let `E_pos = {e₁, e₂, …, eₙ}` be the embeddings of positive examples (documents tagged for axis `a`), and `E_neg` the embeddings of negative examples (documents tagged for *other* axes).

**Step 1 — Compute the contrastive mean:**
```
μ_pos = (1/|E_pos|) Σ eᵢ
μ_neg = (1/|E_neg|) Σ eⱼ
```

**Step 2 — Find the direction:**
```
d_a = μ_pos − μ_neg
```

**Step 3 — Normalize to unit length:**
```
d̂_a = d_a / ||d_a||₂
```

**Step 4 — Project any new embedding onto the direction:**
```
s_a(e) = dot(e, d̂_a)   ∈ ℝ
```

**Step 5 — Normalize the projection to [0, 1]:**

The raw dot product `s_a(e)` can be any real number. Normalize across the training set to get a score in [0, 1]:
```
s̃_a(e) = σ( (s_a(e) − μ_s) / σ_s )
```
where `μ_s` and `σ_s` are the mean and standard deviation of `s_a` over all KB chunks, and `σ` is the sigmoid function.

**For all 9 axes simultaneously**, this is just a matrix multiplication:

```
D = [d̂_ideation | d̂_market | d̂_product | … | d̂_sales]   shape: (1024 × 9)

axis_relevance(e) = normalize( Dᵀ · e )   shape: (9,)
```

---

## 3. Why This Matters for Moufida

### The current retrieval tells you almost nothing

The `retrieve()` function in `backend/rag/app/retrieve.py` returns a score like:

```python
{"score": 0.003847, "matched_chunk": "La BTS propose des micro-crédits..."}
```

That `0.003847` is a Reciprocal Rank Fusion score combining dense cosine rank and BM25 rank. It answers "is this chunk similar to the query?" but not:

- **Why** is it similar? Which business concept drove the match?
- Is it specifically relevant to the **market** axis being diagnosed right now, or did it match because of a coincidentally shared word?
- Should it be weighted more heavily because it's strongly on-axis, or less because it's tangentially related?

### What axis directions add

After computing 9 axis directions from the KB's labeled chunks (which already have `score_dimensions` tags — ready-made supervision), every retrieved chunk gets an **axis relevance vector**:

```
Chunk: "La BTS propose des micro-crédits sans garantie réelle..."
  Retrieved for: market axis query

  Axis decomposition:
  ┌───────────────────────────────────────┐
  │ ideation         0.12  ░░░░░░░░░░    │
  │ market           0.31  ███░░░░░░░    │ ← some relevance (financing is market)
  │ business_model   0.78  ████████░░    │ ← HIGH (this is about funding model)
  │ legal            0.54  █████░░░░░    │ ← medium (BTS has legal conditions)
  │ operations       0.21  ██░░░░░░░░    │
  │ sales            0.09  ░░░░░░░░░░    │
  └───────────────────────────────────────┘
  → This chunk is primarily a business_model resource,
    not a market resource. Down-weight in market axis retrieval.
```

This is a **cross-axis relevance filter**. When the market axis is running, chunks with high `business_model` but low `market` direction scores are deprioritized, even if their BM25/cosine score is high. The retrieval becomes axis-aware, not just query-aware.

### Secondary use — Chunk-to-Axis Routing

Today, KB chunks are retrieved per-axis independently. With axis directions, you can compute the most relevant axis *from the chunk's perspective*: a new ingested document automatically gets tagged to its top-2 axes by projecting its embedding. This replaces manual `score_dimensions` tagging at ingest time.

---

## 4. How to Compute the Directions — Offline Training Step

This is a one-time offline computation in Python using the existing KB data. It runs once when the KB is first built and re-runs whenever the KB is significantly updated (the `kbstaleness` checker in the daemon can trigger it).

### Step 1 — Gather labeled embeddings

The KB chunks already have `score_dimensions` tags (from `taxonomy.json`: `market`, `commercial_offer`, `innovation`, `scalability`, `green`). The 9 diagnostic axes are: `ideation`, `market`, `product`, `brand`, `business-model`, `legal`, `operations`, `marketing`, `sales`.

**Mapping strategy:**
- `market` chunks → positive for `market` axis direction
- `innovation` chunks → positive for `ideation` and `product` axis directions
- `commercial_offer` chunks → positive for `business-model`, `sales` directions
- Chunks tagged `legal_regulatory` type → positive for `legal` direction
- `financing` type → positive for `business-model` direction

This heuristic mapping gives us enough positive/negative pairs from the existing ~80-100 KB resources.

### Step 2 — Pull embeddings from Qdrant

```python
# scripts/compute_axis_directions.py
import asyncio
import json
import numpy as np
from qdrant_client import AsyncQdrantClient

AXIS_TO_SCORE_DIM = {
    "market":         ["market"],
    "business-model": ["commercial_offer", "scalability"],
    "ideation":       ["innovation"],
    "product":        ["innovation"],
    "brand":          ["innovation"],
    "legal":          [],          # use resource type "legal_regulatory" instead
    "operations":     ["scalability"],
    "marketing":      ["market", "commercial_offer"],
    "sales":          ["commercial_offer"],
}

AXIS_TO_RESOURCE_TYPE = {
    "legal": ["legal_regulatory"],
    "operations": ["technical_infrastructure"],
}

async def fetch_embeddings_by_axis(qdrant_url: str, collection: str):
    client = AsyncQdrantClient(url=qdrant_url)
    
    # Scroll all points with payload
    all_points, _ = await client.scroll(
        collection_name=collection,
        with_vectors=True,
        with_payload=True,
        limit=10_000,
    )
    await client.close()
    
    axis_embeddings = {axis: {"pos": [], "neg": []} for axis in AXIS_TO_SCORE_DIM}
    
    for point in all_points:
        embedding = np.array(point.vector, dtype=np.float32)
        dims = set(point.payload.get("score_dimensions", []))
        rtype = point.payload.get("type", "")
        
        for axis, pos_dims in AXIS_TO_SCORE_DIM.items():
            pos_types = AXIS_TO_RESOURCE_TYPE.get(axis, [])
            is_positive = bool(dims & set(pos_dims)) or rtype in pos_types
            
            if is_positive:
                axis_embeddings[axis]["pos"].append(embedding)
            else:
                axis_embeddings[axis]["neg"].append(embedding)
    
    return axis_embeddings


def compute_directions(axis_embeddings: dict) -> dict[str, np.ndarray]:
    directions = {}
    for axis, groups in axis_embeddings.items():
        pos = np.stack(groups["pos"]) if groups["pos"] else None
        neg = np.stack(groups["neg"]) if groups["neg"] else None
        
        if pos is None or neg is None:
            print(f"WARNING: insufficient data for axis {axis}")
            continue
        
        mu_pos = pos.mean(axis=0)
        mu_neg = neg.mean(axis=0)
        direction = mu_pos - mu_neg
        direction /= np.linalg.norm(direction)   # unit vector
        directions[axis] = direction
    
    return directions


async def main():
    axis_embs = await fetch_embeddings_by_axis(
        "http://localhost:6333", "moufida-kb"
    )
    directions = compute_directions(axis_embs)
    
    # Compute normalization stats (μ and σ over all chunks per axis)
    all_points_embs = np.array([...])  # from the full scroll above
    stats = {}
    for axis, d in directions.items():
        projections = all_points_embs @ d
        stats[axis] = {"mean": float(projections.mean()), "std": float(projections.std())}
    
    # Save as binary (f32 array, 9 × 1024) + stats JSON
    probe_matrix = np.stack([directions[a] for a in sorted(directions)])
    np.save("probe_directions.npy", probe_matrix.astype(np.float32))
    with open("probe_stats.json", "w") as f:
        json.dump(stats, f)
    
    print(f"Saved {len(directions)} axis directions.")

asyncio.run(main())
```

**Output:** `probe_directions.npy` (9 × 1024 float32 matrix, ~36KB) and `probe_stats.json`. These are committed to the repo under `signal/assets/` and loaded by the Rust binary at startup.

---

## 5. Rust Implementation

The Rust binary is a pure inference engine: no training, no state beyond the pre-loaded probe matrix. It receives an embedding (1024 floats), multiplies by the 9×1024 matrix, normalizes, returns 9 scores.

### Cargo dependencies

```toml
# signal/Cargo.toml
[dependencies]
axum       = "0.7"
tokio      = { version = "1", features = ["full"] }
serde      = { version = "1", features = ["derive"] }
serde_json = "1"
ndarray    = "0.15"    # N-dimensional array, matrix multiply
bytemuck   = "1"       # safe cast &[f32] from .npy bytes
```

### Core projection module (`signal/src/probe.rs`)

```rust
use ndarray::{Array1, Array2, Axis};
use std::collections::HashMap;

/// Axis probe engine loaded once at startup.
pub struct AxisProbe {
    /// Shape: (n_axes, embed_dim) — each row is one axis direction unit vector.
    directions: Array2<f32>,
    /// Axis names in the same row order as `directions`.
    axis_names: Vec<String>,
    /// Per-axis normalization: (mean, std) of projections over training set.
    stats: Vec<(f32, f32)>,
}

impl AxisProbe {
    /// Load from pre-computed .npy file + stats JSON.
    pub fn load(npy_path: &str, stats_path: &str) -> anyhow::Result<Self> {
        let bytes = std::fs::read(npy_path)?;
        // Parse numpy .npy format: 128-byte header + raw f32 data.
        let data_offset = parse_npy_header(&bytes)?;
        let floats: &[f32] = bytemuck::cast_slice(&bytes[data_offset..]);
        
        let stats_json: serde_json::Value =
            serde_json::from_str(&std::fs::read_to_string(stats_path)?)?;
        
        let axis_names: Vec<String> = stats_json
            .as_object().unwrap().keys().cloned().collect();
        let n_axes = axis_names.len();
        let embed_dim = floats.len() / n_axes;
        
        let directions = Array2::from_shape_vec(
            (n_axes, embed_dim),
            floats.to_vec(),
        )?;
        
        let stats: Vec<(f32, f32)> = axis_names.iter().map(|ax| {
            let s = &stats_json[ax];
            (s["mean"].as_f64().unwrap() as f32,
             s["std"].as_f64().unwrap() as f32)
        }).collect();
        
        Ok(Self { directions, axis_names, stats })
    }
    
    /// Project one embedding onto all axis directions.
    /// Returns a HashMap { axis_name: score_0_to_1 }.
    pub fn project(&self, embedding: &[f32]) -> HashMap<String, f32> {
        let e = Array1::from_slice(embedding);
        
        // Matrix multiply: (n_axes, embed_dim) × (embed_dim,) → (n_axes,)
        // This is a single BLAS dgemv call — extremely fast (~1µs for 9×1024).
        let raw_scores = self.directions.dot(&e);
        
        raw_scores.iter()
            .enumerate()
            .map(|(i, &raw)| {
                let (mu, sigma) = self.stats[i];
                // Standardize then sigmoid → [0, 1]
                let normalized = (raw - mu) / (sigma + 1e-8);
                let score = 1.0 / (1.0 + (-normalized).exp());
                (self.axis_names[i].clone(), (score * 1000.0).round() / 1000.0)
            })
            .collect()
    }
    
    /// Find the top-k most relevant axes for this embedding.
    pub fn top_axes(&self, embedding: &[f32], k: usize) -> Vec<(String, f32)> {
        let mut scores: Vec<(String, f32)> = self.project(embedding).into_iter().collect();
        scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        scores.truncate(k);
        scores
    }
}
```

### HTTP endpoint (`signal/src/main.rs`)

```rust
use axum::{extract::State, Json, Router};
use std::sync::Arc;

#[derive(serde::Deserialize)]
struct ProjectRequest {
    embedding: Vec<f32>,       // 1024 floats from bge-m3
    top_k: Option<usize>,
}

#[derive(serde::Serialize)]
struct ProjectResponse {
    axis_relevance: std::collections::HashMap<String, f32>,
    top_axes: Vec<(String, f32)>,
    dominant_axis: String,
}

async fn project_handler(
    State(probe): State<Arc<AxisProbe>>,
    Json(req): Json<ProjectRequest>,
) -> Json<ProjectResponse> {
    let k = req.top_k.unwrap_or(3);
    let axis_relevance = probe.project(&req.embedding);
    let top_axes = probe.top_axes(&req.embedding, k);
    let dominant_axis = top_axes.first().map(|(a, _)| a.clone()).unwrap_or_default();
    
    Json(ProjectResponse { axis_relevance, top_axes, dominant_axis })
}

// Route: POST /probe/project
```

**Latency:** For a 1024-dim embedding, a single matrix-vector multiply (9×1024) executes in < 5 microseconds on any CPU. Even with HTTP overhead, the total roundtrip is < 1ms. This adds zero perceptible latency to the RAG pipeline.

---

## 6. Integration into the RAG Retrieval Pipeline

### Modified `retrieve()` in `backend/rag/app/retrieve.py`

```python
import httpx, os

SIGNAL_URL = os.environ.get("SIGNAL_URL", "http://signal:8010")

async def retrieve(query, stage=None, dimensions=None, sector=None, top_k=3,
                   collection=None, current_axis=None) -> list[dict]:
    """
    current_axis: if provided, axis direction score is used as a re-ranking signal.
    """
    # ... existing dense + BM25 + RRF retrieval ...
    
    if current_axis and results:
        # Project each chunk embedding through the axis probe
        async with httpx.AsyncClient() as http:
            for result in results:
                embedding = result.pop("_embedding", None)  # store embedding during retrieval
                if embedding:
                    resp = await http.post(
                        f"{SIGNAL_URL}/probe/project",
                        json={"embedding": embedding, "top_k": 3},
                        timeout=2.0,
                    )
                    probe_data = resp.json()
                    result["axis_relevance"] = probe_data["axis_relevance"]
                    result["on_axis_score"] = probe_data["axis_relevance"].get(
                        current_axis, 0.5
                    )
                    # Re-rank: blend RRF score with on-axis direction score
                    result["score"] = (
                        0.7 * result["score"] +
                        0.3 * result["on_axis_score"]
                    )
        
        # Re-sort by blended score
        results.sort(key=lambda r: r["score"], reverse=True)
    
    return results
```

The `_embedding` is stored in the result dict during the Qdrant `.search()` call (Qdrant returns the vector when `with_vectors=True`). This costs no extra network call — the vector is already in the response.

### Automatic chunk tagging at ingest time

In `backend/rag/app/ingest.py`, after computing the embedding for a new chunk, call the probe to auto-tag it:

```python
async def _tag_axes(embedding: list[float], http: httpx.AsyncClient) -> list[str]:
    """Return top-2 diagnostic axes for this embedding."""
    try:
        resp = await http.post(
            f"{SIGNAL_URL}/probe/project",
            json={"embedding": embedding, "top_k": 2},
            timeout=2.0,
        )
        return [ax for ax, _ in resp.json()["top_axes"]]
    except Exception:
        return []

# In _upsert_point(), before building PointStruct:
auto_axes = await _tag_axes(embedding, http)
payload["auto_axes"] = auto_axes  # stored alongside manual score_dimensions
```

This means every newly ingested document — from daemon's web scraping, from user-uploaded PDFs, from grant feeds — is automatically classified into diagnostic axes without manual tagging.

---

## 7. New Capability — Chunk Explanation in the UI

### EvidenceTrace enrichment

The existing `EvidenceTrace` component (from the H5 plan) currently shows:
```
[KB] ANPR_2024_agrifood_report.pdf — score: 0.003847
```

After the axis direction integration, it shows:
```
[KB] ANPR_2024_agrifood_report.pdf
     Retrieved for: market axis

     Axis relevance:
     business_model  ████████  0.78   ← dominant (funding model content)
     legal           █████░░░  0.54
     market          ███░░░░░  0.31   ← current axis (moderate match)
     operations      ██░░░░░░  0.21

     Note: This chunk is primarily a business model resource.
     It's included because it contains market-relevant financing data.
```

This gives the founder and the judge full visibility into why each piece of evidence appeared in a diagnostic.

### KB Explorer (new admin panel tab)

In the observability admin panel (H4), add a "KB Explorer" tab:

```
┌─────────────────────────────────────────────────────────────┐
│  KB EXPLORER — Axis Direction Map                           │
│                                                             │
│  Enter any text to see where it sits in axis space:         │
│  [  What is the CAC for B2B SaaS in Tunisia?     ] [Probe] │
│                                                             │
│  Results:                                                   │
│  market          ████████████  0.89                         │
│  sales           ███████░░░░░  0.67                         │
│  business-model  █████░░░░░░░  0.52                         │
│  product         ██░░░░░░░░░░  0.19                         │
│  legal           █░░░░░░░░░░░  0.08                         │
│                                                             │
│  This query is strongly market/sales oriented.              │
│  It will retrieve best results from those axis collections. │
└─────────────────────────────────────────────────────────────┘
```

This is powerful for debugging retrieval quality — you can see exactly how the embedding model "understands" any query in terms of business dimensions.

---

## 8. What This Is NOT

**Not a classifier.** A classifier would predict a single label ("this document is about market"). Axis directions give a continuous score on all 9 dimensions simultaneously — a document can be 0.78 business_model AND 0.54 legal AND 0.31 market at the same time.

**Not topic modeling (LDA/NMF).** Topic models find latent topics from co-occurrence statistics. Axis directions are supervision-driven: they find the specific direction that separates documents labeled for axis `a` from documents labeled for other axes. The directions are grounded in the existing KB taxonomy, not inferred from scratch.

**Not a fine-tuned embedding model.** We are NOT modifying the bge-m3 model. We are learning a lightweight linear probe (9 directions, 9×1024 = 9,216 float32 values) on top of its frozen embeddings. This is the whole point: the geometry we need already exists in the embedding space.

**Not reinventing Representation Engineering.** RepE was applied to LLM residual stream activations to find directions for abstract concepts (honesty, happiness). We apply the same technique to retrieval embeddings in a domain-specific knowledge base to find directions for business diagnostic categories — a different modality, a different domain, a concrete and immediate application.

---

## 9. Files to Create / Modify

```
scripts/
  compute_axis_directions.py    ← offline direction computation (Python)

signal/
  assets/
    probe_directions.npy        ← 9×1024 float32 matrix (generated, committed)
    probe_stats.json            ← per-axis mean/std for normalization
  src/
    probe.rs                    ← AxisProbe struct + project() + top_axes()
    main.rs                     ← POST /probe/project route

backend/rag/app/
  retrieve.py                   ← add axis-aware re-ranking (20 lines)
  ingest.py                     ← add auto_axes tagging via probe (15 lines)

frontend/src/components/shared/
  AxisRelevanceBar.tsx          ← small bar chart for per-axis scores
  EvidenceTrace.tsx             ← enrich with axis_relevance field

frontend/src/components/admin/
  KbExplorer.tsx                ← free-text probe in admin panel
```

---

## 10. Relationship Between the Two Research Contributions

These two tools operate at different layers of the same pipeline and are **mutually reinforcing**:

```
                         ┌─────────────────────────────┐
                         │  Axis Direction Probe         │
                         │  (Idea 3 — this document)     │
                         │                               │
  KB chunks ────embed──► │  projects embedding onto      │
                         │  9 axis directions            │
                         │  → axis_relevance[9]          │
                         └──────────────┬────────────────┘
                                        │ re-ranked chunks
                                        ▼
                         ┌─────────────────────────────┐
                         │  LLM Axis Diagnosis           │
                         │  (existing pipeline)          │
                         │                               │
  profile + chunks  ───► │  Ollama generates text +      │
                         │  raw score                    │
                         └──────────────┬────────────────┘
                                        │ profile + raw score
                                        ▼
                         ┌─────────────────────────────┐
                         │  Concept Bottleneck Layer     │
                         │  (Idea 1 — other document)    │
                         │                               │
                         │  LLM scores each concept      │
                         │  Rust computes weighted score  │
                         │  → bottleneck identified       │
                         └─────────────────────────────┘
```

Idea 3 improves the **input** to the LLM (better, more axis-aligned evidence).
Idea 1 improves the **output** of the LLM (decomposable, bottleneck-identified score).
Together they close the interpretability loop end-to-end.
