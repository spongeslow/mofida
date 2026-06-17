# Phase 3 — Knowledge Base & RAG Service

> 📍 Plan order: after [phase2-completion](./phase2-completion.md). KB curation can start in parallel on day 1. See [README](./README.md) for the dependency graph.

**Goal:** Axis 10 (go-to-market service) can retrieve real, traceable Tunisian resources for any combination of maturity stage, score dimension, and sector, and produce a personalised time-horizoned action roadmap.

**Prerequisites:** Phase 2 diagnostic runner is complete (aggregator outputs blockers, low scores, maturity stage — these are the inputs to the RAG queries).

---

## Overview of What Needs to Be Built

| Component | File | Status |
|---|---|---|
| Resource documents | `rag/knowledge-base/resources/` | ❌ Empty (0 of 80–100 needed) |
| Ingest pipeline | `rag/app/ingest.py` | ❌ Stub |
| Hybrid retrieval | `rag/app/retrieve.py` | ❌ Stub |
| Admin endpoint | `rag/app/admin.py` | ❌ Stub |
| RAG service main | `rag/app/main.py` | ❌ Stubs only |
| Axis 10 roadmap | `services/go-to-market-service/app/main.py` | ❌ Stub |
| Tier 3 eval dataset | `eval/tier3-rag/query_pairs.json` | ❌ Missing |
| Tier 3 eval runner | `eval/tier3-rag/run_eval.py` | ❌ Missing |
| Ingest script | `scripts/ingest-kb.sh` | Exists (calls stub) |

---

## Step 1 — Curate the Knowledge Base (80–100 Resources)

### Resource Schema

Every resource is a JSON file in `rag/knowledge-base/resources/`. Use the Listing 1 schema:

```json
{
  "id": "apii-startup-act-innovation-grant",
  "title": "Startup Act — Prime à l'Innovation (APII)",
  "type": "financing",
  "stage": ["ideation", "market_validation", "structuration"],
  "sector": ["cross-sector"],
  "score_dimensions": ["innovation", "scalability"],
  "url": "https://www.apii.tn/...",
  "language": "fr",
  "last_verified": "2026-06-01",
  "provider": "APII",
  "body": "Full text of the resource (1–5 paragraphs). This is what gets embedded."
}
```

**Mandatory fields:** `id`, `title`, `type`, `stage[]`, `sector[]`, `score_dimensions[]`, `url`, `last_verified`, `body`.

### Coverage Target

**Minimum floor:** 2 resources per `(Stage × Type)` cell = 6 stages × 5 types × 2 = **60 resources**.

| Stage | Financing | Legal/Regulatory | Training/Coaching | Networking | Technical |
|---|---|---|---|---|---|
| Ideation | 2 | 2 | 2 | 2 | 2 |
| Market Validation | 2 | 2 | 2 | 2 | 2 |
| Structuration | 2 | 2 | 2 | 2 | 2 |
| Fundraising | 2 | 2 | 2 | 2 | 2 |
| Launch Planning | 2 | 2 | 2 | 2 | 2 |
| Growth | 2 | 2 | 2 | 2 | 2 |

**Additional 20–40 resources:** sector-specific for `agri-food`, `digital-tech`, `industry`.

### Authoritative Sources to Mine

| Provider | Type | Relevant Stages |
|---|---|---|
| APII (Startup Act, innovation grants) | Financing, Legal | Ideation → Structuration |
| BFPME (loans for SMEs) | Financing | Structuration → Growth |
| BTS (Banque Tunisienne de Solidarité, micro-loans) | Financing | Ideation → Market Validation |
| ANPE (Emploi des Jeunes programme) | Training | Ideation → Structuration |
| Smart Capital / CDC (VC ecosystem) | Financing | Fundraising → Growth |
| Tunisia Startup Act (legal framework) | Legal/Regulatory | Ideation → Fundraising |
| INNORPI (patent & trademark registration) | Legal | Any |
| ONAGRI (agri-food certification) | Technical, Legal | Agri-food specific |
| AFI (digital infrastructure, IoT) | Technical | Digital-tech specific |
| Réseau Entreprendre Tunisie (mentoring) | Networking | Market Validation → Structuration |
| Orange Fab, Flat6Labs, Impact Fund (incubators) | Networking | Ideation → Market Validation |
| Tunisian-EU Business Association | Networking, Financing | Fundraising → Growth |
| UNDP Tunisia (social enterprise grants) | Financing | Cross-sector |
| EU4Innovation / Horizon Europe (for TN entities) | Financing | Market Validation → Growth |
| GDPR / Tunisian Law 2004-63 (data protection guide) | Legal/Regulatory | Market Validation → Launch |
| Startup Act administrative procedure guide | Legal/Regulatory | Structuration |
| Business plan templates (APII/BFPME format) | Training | Market Validation → Structuration |

### Resource File Naming Convention

`{provider-slug}-{topic-slug}.json`, e.g., `apii-startup-act-grant.json`, `bts-micro-loan.json`.

---

## Step 2 — RAG Service: Ingestion Pipeline

**File:** `rag/app/ingest.py`

**Dependencies to add to `rag/pyproject.toml`:**
- `qdrant-client>=1.9`
- `httpx` (already present)
- `rank-bm25`

### What It Does

1. Reads all `.json` files from `rag/knowledge-base/resources/`.
2. Splits `body` into paragraph chunks (split on `\n\n`, keep metadata per chunk).
3. Embeds each chunk via `POST http://{OLLAMA_BASE_URL}/api/embed` with model `nomic-embed-text`.
4. Upserts into Qdrant collection `moufida_kb` with payload = full resource metadata + chunk index.

### Qdrant Schema

```python
# Collection: moufida_kb
# Vector size: 768 (nomic-embed-text)
# Distance: Cosine

# Payload per point:
{
  "resource_id": str,
  "title": str,
  "type": str,                         # financing | legal_regulatory | training_coaching | networking | technical
  "stage": list[str],                  # maturity stages this resource applies to
  "sector": list[str],                 # agri-food | digital-tech | industry | cross-sector
  "score_dimensions": list[str],       # market | commercial_offer | innovation | scalability | green
  "url": str,
  "language": str,
  "last_verified": str,
  "provider": str,
  "chunk_index": int,
  "chunk_text": str,
  "needs_review": bool                 # set to True by daemon staleness checker
}
```

### ingest.py Implementation

```python
# Pseudocode structure
def ingest_all():
    resources = load_all_json("rag/knowledge-base/resources/")
    qdrant = QdrantClient(url=QDRANT_URL)
    ensure_collection(qdrant, "moufida_kb", vector_size=768)
    
    for resource in resources:
        chunks = split_paragraphs(resource["body"])
        for i, chunk in enumerate(chunks):
            embedding = embed(chunk, model="nomic-embed-text")
            payload = {**resource_metadata(resource), "chunk_index": i, "chunk_text": chunk}
            qdrant.upsert(collection="moufida_kb", points=[PointStruct(
                id=f"{resource['id']}-{i}",
                vector=embedding,
                payload=payload
            )])
```

**Expose via endpoint:**
```python
@app.post("/ingest")
def ingest():
    count = ingest_all()
    return {"status": "ok", "ingested": count}
```

---

## Step 3 — RAG Service: Hybrid Retrieval Pipeline

**File:** `rag/app/retrieve.py`

### Three-Step Pipeline

**Step 1 — Metadata pre-filter:**
Filter Qdrant candidate set to points where:
- `stage` list intersects the diagnosed maturity stage
- `score_dimensions` list intersects the low-score dimensions (score < 2.5/5)
- `needs_review == false`

```python
qdrant_filter = Filter(must=[
    FieldCondition(key="stage", match=MatchAny(any=[diagnosed_stage])),
    FieldCondition(key="score_dimensions", match=MatchAny(any=low_score_dimensions)),
    FieldCondition(key="needs_review", match=MatchValue(value=False)),
])
```

**Step 2 — Hybrid retrieval (dense + BM25 + RRF):**
- Dense: embed the query with `nomic-embed-text`, cosine search over the filtered set, return top-20.
- Sparse (BM25): build BM25 index over `chunk_text` of filtered candidates, score the query, return top-20.
- Merge with Reciprocal Rank Fusion: `RRF_score(d) = Σ 1/(k + rank_i(d))` with k=60.

**Step 3 — Sector boost:**
For resources whose `sector` matches the entrepreneur's declared sector, multiply their RRF score by 1.3.

Return top-k results (default 3) with fields: `resource_id`, `title`, `url`, `provider`, `chunk_text`, `relevance_score`, `stage`, `type`.

### retrieve.py API

```python
class RetrieveRequest(BaseModel):
    query: str
    stage: str                     # diagnosed maturity stage
    dimensions: list[str] = []     # low-score dimensions to filter on
    sector: str | None = None      # entrepreneur's sector for boost
    resource_type: str | None = None  # optional type filter
    top_k: int = 3

@app.post("/retrieve")
def retrieve(req: RetrieveRequest) -> dict:
    results = retrieval_pipeline(req)
    return {"query": req.query, "results": results}
```

---

## Step 4 — RAG Service: Admin Endpoint

**File:** `rag/app/admin.py`

```python
@app.post("/admin/resource")
def add_resource(resource: dict):
    """Add a new resource and immediately ingest it into Qdrant."""
    # Validate required fields
    # Write JSON to knowledge-base/resources/
    # Run ingest for this single resource
    return {"status": "ok", "id": resource["id"]}

@app.post("/admin/flag/{resource_id}")
def flag_resource(resource_id: str):
    """Mark a resource needs_review=True (called by daemon staleness checker)."""
    # Update all Qdrant points for this resource_id
    return {"status": "flagged", "resource_id": resource_id}
```

---

## Step 5 — Axis 10: Roadmap Endpoint

**File:** `services/go-to-market-service/app/main.py`

**Add endpoint:** `POST /roadmap`

### Input

```python
class RoadmapRequest(BaseModel):
    project_id: str
    maturity_stage: str
    sector: str = "cross-sector"
    language: str = "fr"
    blockers: list[dict] = []        # from aggregator
    low_scores: dict[str, float] = {}  # score_name -> score (only those < 2.5)
    profile: dict = {}
```

### Implementation

For each low-scoring dimension and each critical blocker, call `POST /retrieve` on the RAG service with the appropriate query, stage, and dimension filters. Collect all retrieved resources.

Then call `llama3.1:8b` with a structured prompt that:
1. Lists the gaps/blockers in order of severity
2. Lists the retrieved resources with their titles and URLs
3. Asks the LLM to organise them into an action plan with three horizons: **Immédiat** (0–2 semaines), **Court terme** (1–3 mois), **Moyen terme** (3–12 mois)
4. Each action must cite a resource title and URL from the retrieved set

**Store result** in `roadmap_versions` table via orchestrator API or direct DB write.

**Return:**
```json
{
  "roadmap": {
    "immediate": [
      {"action": "...", "rationale": "...", "resource": {"title": "...", "url": "..."}}
    ],
    "short_term": [...],
    "medium_term": [...]
  },
  "sources": [{"resource_id": "...", "title": "...", "url": "..."}]
}
```

### Wire Axis 10 into the Diagnostic Pass

Update `orchestrator/app/diagnostic_router.py` to call `POST /roadmap` on `go-to-market-service` after the 3-wave diagnostic pass completes, passing the aggregated results. Store the roadmap in `roadmap_versions`. Push `roadmap_update` SSE event.

---

## Step 6 — Tier 3 Evaluation

**File to create:** `eval/tier3-rag/query_pairs.json`

### Structure

```json
[
  {
    "id": "q01",
    "query": "programme de financement pour startup en phase idéation",
    "stage": "ideation",
    "dimension": "scalability",
    "expected_resource_ids": ["bts-micro-loan", "apii-startup-act-grant"]
  },
  ...
]
```

**Target:** 20 pairs covering all 6 stages and all 5 resource types. At least one pair per stage.

**File to create:** `eval/tier3-rag/run_eval.py`

```python
# Calls POST /retrieve for each query_pair
# Reports:
#   Recall@3: fraction of queries where at least one expected_resource appears in top-3
#   MRR: mean(1 / rank_of_first_expected_result)
# Targets: Recall@3 >= 0.80, MRR >= 0.70
```

**Run:**
```bash
cd eval/tier3-rag
python run_eval.py --url http://localhost:8300
```

---

## Step 7 — Ingest Script Update

**File:** `scripts/ingest-kb.sh`

Update to call `POST http://localhost:8300/ingest` after `docker compose up`, then print the ingestion count.

```bash
#!/bin/bash
echo "Ingesting knowledge base..."
result=$(curl -s -X POST http://localhost:8300/ingest)
echo $result
```

---

## RAG Service Dockerfile Update

Add `qdrant-client` and `rank-bm25` to the pip install in `rag/Dockerfile`. Current Dockerfile only installs `fastapi`, `uvicorn`, `httpx`.

Updated pip install:
```dockerfile
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    httpx \
    "qdrant-client>=1.9" \
    rank-bm25
```

Also add `OLLAMA_BASE_URL` and `QDRANT_URL` to the RAG service's environment in `docker-compose.yml` (they're already there for `qdrant_url`; `OLLAMA_BASE_URL` is missing from the RAG service env block).

---

## Completion Criteria

- [ ] `ls rag/knowledge-base/resources/ | wc -l` → ≥ 60 JSON files
- [ ] `curl -X POST http://localhost:8300/ingest` → `{"status": "ok", "ingested": N}`
- [ ] `curl -X POST http://localhost:8300/retrieve -d '{"query":"financement startup tunisie","stage":"ideation","dimensions":["scalability"]}'` → ≥ 1 result with `url` and `title`
- [ ] `POST http://localhost:8110/roadmap` with sample diagnostic output → structured 3-horizon roadmap
- [ ] `POST http://localhost:8001/api/v1/project/{id}/run-diagnostic` response now includes `roadmap` field
- [ ] Tier 3 eval: `Recall@3 ≥ 0.80`, `MRR ≥ 0.70`
