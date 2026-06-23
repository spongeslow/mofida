# moufida-signal

Rust interpretability microservice (port **8010**) implementing two research
papers behind one HTTP surface. Both capabilities are **best-effort** from the
callers' point of view: the orchestrator and RAG service degrade gracefully when
this service is down or its assets are absent.

| Paper | Capability | Endpoints |
|---|---|---|
| Concept Bottleneck Models (Koh et al., ICML 2020; Oikarinen et al., ICLR 2023) | Decompose an axis score into named concepts + identify the bottleneck | `POST /cbm/score`, `POST /cbm/calibrate` |
| Representation Engineering (Zou et al., arXiv 2310.01405) | Project a retrieval embedding onto 9 axis directions | `POST /probe/project`, `POST /probe/install`, `POST /probe/reload` |

See the design docs:
- `docs/research/concept-bottleneck-diagnostic-layer.md`
- `docs/research/contrastive-axis-directions-embedding.md`

## Endpoints

### `GET /health`
```json
{ "status": "ok", "service": "moufida-signal", "version": "0.1.0",
  "probe_ready": true, "probe_axes": 9 }
```

### `POST /cbm/score`
```json
// request
{ "axis": "market",
  "concepts": { "tam_evidence": 0.62, "icp_specificity": 0.18, "wtp_signal": 0.38,
                "competitive_differentiation": 0.54, "market_timing": 0.80 } }
// response
{ "axis": "market", "score": 2.4,
  "weighted_contributions": { "icp_specificity": 0.063, ... },
  "bottleneck": { "concept_id": "icp_specificity", "current": 0.18,
                  "weight": 0.35, "score_if_fixed": 2.67 },
  "calibrated": true }
```

### `POST /cbm/calibrate`
Ridge regression over `(concept_vector, actual_score)` observations. Writes the
learned weights for the axis back to `assets/cbm_weights.json`.
```json
{ "axis": "market", "lambda": 1.0,
  "observations": [ { "concepts": {...}, "actual_score": 3.2 }, ... ] }
```

### `POST /probe/install`
The offline script (`scripts/compute_axis_directions.py`) pushes computed
directions here — no shared volume needed. Persisted as `assets/probe.json`.
```json
{ "axis_names": ["brand","business-model",...], "embed_dim": 1024,
  "directions": [[...],[...]],
  "stats": { "brand": { "mean": 0.01, "std": 0.12 }, ... } }
```

### `POST /probe/project`
```json
// request
{ "embedding": [ ...1024 floats... ], "top_k": 3 }
// response
{ "axis_relevance": { "market": 0.89, "sales": 0.67, ... },
  "top_axes": [["market",0.89],["sales",0.67],["business-model",0.52]],
  "dominant_axis": "market" }
```
Returns **503** when directions have not been installed yet.

## Assets

- `assets/cbm_weights.json` — **committed** prior weights for all 9 axes; overwritten
  per-axis by `/cbm/calibrate`.
- `assets/probe.json` — **generated** at runtime by `/probe/install` (git-ignored).
- `assets/probe_directions.npy` + `assets/probe_stats.json` — optional NumPy
  alternative loaded at startup if `probe.json` is absent.

## Run

```bash
cargo run                 # SIGNAL_PORT=8010, SIGNAL_ASSETS_DIR=assets
cargo test                # unit tests for scoring, bottleneck, calibration
docker build -f signal/Dockerfile -t moufida-signal .   # from repo root
```

Environment: `SIGNAL_PORT` (default 8010), `SIGNAL_ASSETS_DIR` (default `assets`).
