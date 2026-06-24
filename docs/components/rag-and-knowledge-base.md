# RAG Service & Knowledge Base

**Location:** `backend/rag/` | **Port:** 8300  
**Stack:** Python 3.12, FastAPI, qdrant-client (async), rank-bm25, httpx, SearXNG

---

## Hybrid Retrieval Pipeline

`POST /retrieve` runs five stages:

```
Query
  │
  ├─ 1. Dense retrieval — embed via Ollama bge-m3 (1024-dim) → Qdrant cosine search → top-40 candidates
  ├─ 2. BM25 sparse retrieval — rank_bm25 over candidate pool text
  ├─ 3. Reciprocal Rank Fusion (RRF, k=60) — score = 1/(k+rank_dense) + 1/(k+rank_bm25)
  ├─ 4. Sector boost — matching sector chunks ×1.3
  └─ 5. Axis-direction re-ranking (when current_axis is given)
           call Signal /probe/project for each chunk's stored embedding
           final_score = 0.7 × rrf_score + 0.3 × axis_relevance[current_axis]
           re-sort by blended score
```

**Why RRF?** Parameter-free combination of dense and sparse ranks (Cormack et al. 2009). Robust to the scale difference between cosine scores and BM25 scores — no learned fusion weights to maintain.

**Why axis-direction re-ranking?** Dense similarity finds chunks semantically close to the query, but "semantically close" ≠ "relevant to the *current* diagnostic axis." A chunk about "BTS micro-credit" matches a market query on keywords yet belongs to the business-model axis. The 30% axis signal demotes it for market-axis retrieval while keeping it accessible for business-model retrieval. See [axis-directions.md](../research/axis-directions.md) for the math.

---

## Live Web Search

`POST /web_search` — SearXNG-backed metasearch. SearXNG is **self-hosted** — it aggregates Google/Bing/DuckDuckGo without any API key and without exposing queries to third parties. Used in creation mode to supplement KB evidence with current information.

---

## Ingest Pipeline

`POST /ingest` processes all resources in `knowledge-base/resources/`:

```
For each resource JSON:
  1. Chunk text (~400 token semantic chunks)
  2. Embed via Ollama bge-m3
  3. Call Signal /probe/project → auto-tag top-2 axes (if probe is calibrated)
  4. Upsert to Qdrant with payload: {text, resource_id, stage, sector, type, score_dimensions, auto_axes}
```

Auto-tagging (step 3) means newly ingested documents — user-uploaded PDFs, daemon-scraped pages, grant notices — are automatically classified into diagnostic axes without manual intervention.

---

## Knowledge Base — 83 Curated Resources

Every resource is tagged with `stage`, `sector`, `type`, and `score_dimensions` to ensure retrieved chunks are context-appropriate (a founder at ideation stage won't receive investor-readiness resources).

### Key Tunisian Institutions Covered

| Institution | Role | Resource types |
|---|---|---|
| **APII** | StartupAct certification, innovation support | legal_regulatory, financing |
| **Smart Capital (SICAR)** | Main VC fund-of-funds | financing |
| **BFPME** | SME long-term loans | financing |
| **BTS** | Micro-credit, solidarity finance | financing |
| **Carthage Business Angels** | Angel investor network | financing |
| **StartupAct** | 2019 startup legal framework (SARL simplifié, BSA, tax incentives) | legal_regulatory |
| **INNORPI** | Patents, trademarks, industrial design | legal_regulatory |
| **CEPEX** | Export promotion, market access | networking_ecosystem |
| **Flat6Labs / Orange Digital Center** | Acceleration, early-stage support | training_coaching |

### Multilingual Retrieval

`bge-m3` was pre-trained on 100+ languages including Arabic and French. A Tunisian Darija voice query correctly retrieves French-language KB resources because both are embedded in the same semantic space. The 18 per-axis resources are available in Arabic, French, and English.

### KB Staleness Monitoring

The daemon's `kbstaleness` watcher checks nightly for resources with `last_verified` > 90 days. Stale flags appear in the admin panel's daemon activity log.

### Adding Resources

Three paths:
1. **Manual JSON** → `scripts/generate_kb.py` / `scripts/generate_kb_axis.py` → `./scripts/ingest-kb.sh`
2. **Admin API** → `POST /rag/admin/resource`
3. **Founder upload** → drag PDF onto companion or dashboard upload button → `POST /project/{id}/documents` → extracted text ingested into project-specific Qdrant collection (not shared with other projects)

After large KB changes, recompute axis-direction vectors:
```bash
docker compose --profile tools run --rm compute-directions
```

---

## Admin Endpoints

- `POST /admin/resource` — add resource
- `POST /admin/flag/{id}` — flag for staleness review
- `GET /admin/resources` — list with metadata (used by daemon staleness watcher and KB browser UI)
