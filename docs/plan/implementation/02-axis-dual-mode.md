# 02 — Axis Services: True Dual Mode (`generate` + `evaluate`)

> Implements new-logic.md §1, §2.2, §7. This is the **core backend unlock** —
> everything in creation mode and continuous updates depends on real generation.

---

## 1. Current state

Every axis service (`backend/services/<svc>/app/main.py`) exposes:
- `POST /diagnose` → **works** (evaluate): `score`, `confidence`, `evidence`,
  `blockers`, `justification`, `due_diligence`.
- `POST /execute` → **stub**: `{"mode":"execute","status":"not_implemented"}`.
- `POST /metric_update` → daemon hook.

The orchestrator never calls `/execute`; `CreationFlow.tsx` fakes creation from
diagnostic output (documented compromise). We replace the stub with a real
generation endpoint and teach the orchestrator to choose per `mode`.

---

## 2. Target contract

Add `POST /generate` to **all ten** axis surfaces (rename the `/execute` stub;
keep a 308/alias if anything still calls it). Keep `/diagnose` as-is.

### Request (orchestrator → axis)
```jsonc
{
  "language": "fr",
  "idea": "raw founder idea text",          // creation seed
  "profile": { ... },                         // StartupProfile JSONB
  "upstream": {                               // approved outputs of prior axes
    "ideation": { ...content... },
    "market":   { ...content... }
  },
  "constraints": "user edit text or null",   // Edit action feeds this back
  "mode": "generate"                          // 'generate' | 'regenerate'
}
```

### Response (axis → orchestrator)
```jsonc
{
  "axis": "market",
  "mode": "generate",
  "content": { /* axis-specific structured proposal, see §3 */ },
  "summary": "Three target segments; SAM ≈ 12k SMEs; differentiate on price",
  "assumptions": ["..."],          // what the model inferred / needs confirming
  "needs_input": ["..."]           // optional clarifying questions for the user
}
```
`content` is stored verbatim in `plan_sections.content` (`01 §2`).

**Edit / Retry semantics** (drives `03-creation-flow.md`):
- **Approve** → persist `content` as the live `plan_sections` row (`approved=true`).
- **Edit** → re-call `/generate` with `constraints` = user's edit text and the
  same `upstream`; new proposal returned.
- **Retry** → re-call `/generate` with `constraints=null` (fresh sample;
  raise temperature slightly).

---

## 3. Per-axis `content` schemas

Each axis owns a stable JSON shape so the frontend document view and the
dependency engine can read fields. Defined once in a shared module
`backend/services/_shared/plan_schemas.py` (or duplicated per service if the
repo has no shared package — check `pyproject.toml` layout first).

| Axis | `content` key fields (creation `generate`) |
|------|---------------------------------------------|
| ideation | `refined_idea`, `vision`, `problem`, `solution_fit`, `positioning` |
| market | `segments[]`, `market_size`, `competitors[]`, `differentiation` |
| product | `mvp_features[]`, `user_stories[]`, `tech_stack[]` |
| brand | `values[]`, `tone`, `visual_direction` |
| business-model | `revenue_streams[]`, `pricing`, `cost_structure`, `unit_economics` |
| legal | `legal_structure`, `ip_strategy`, `regulatory[]` |
| operations | `team[]`, `processes[]`, `tools[]`, `timeline` |
| marketing | `channels[]`, `content_strategy`, `launch_plan` |
| sales | `sales_channels[]`, `pipeline_model`, `partnerships[]` |
| roadmap | (virtual axis — see §4; produced by RAG generator, not a service) |

Keep shapes shallow and explicit so the diff viewer (`06`) can render
field-level before/after.

---

## 4. Axis 10 reconciliation (`gtm` → `roadmap` + keep `operations`)

`axis_registry.py` today lists axis 10 = `gtm` (go-to-market-service, port 8110)
and `operations` = axis 9. The design doc's ten axes are Ideation, Market,
Product, Brand, Business Model, Legal, **Operations**, Marketing, Sales,
**Roadmap** — no standalone `gtm`.

**Plan:**
1. Promote `operations` to a first-class scoring/generating axis (it already
   has a service — no new service needed).
2. Treat **Roadmap** as the orchestrator's RAG generator (`backend/rag` +
   `diagnostic_router._call_roadmap`), *not* a network service. It is "axis 10"
   conceptually only.
3. Fold GTM concerns into `marketing` (channels/launch) and `sales`
   (pipeline/partnerships) prompts. **Keep the `go-to-market-service`
   container running** but stop routing it as a distinct axis — least-risk for
   the demo. Remove it only in a later cleanup.
4. Update `axis_registry.AXES` so the generate/evaluate fan-out iterates the
   nine network axes + the virtual roadmap. Update `METRIC_ROUTES` (`milestone`
   currently routes to `gtm`) to route to `operations`/`product`.

> This is a small but load-bearing change — do it first in Phase A so every
> downstream loop iterates a consistent axis set.

---

## 5. Generation prompts

Each service gets a `generate` system prompt distinct from its diagnose prompt.
Guidelines:
- Feed `idea` + `profile` + `upstream` as context; instruct the model to emit
  **only** the JSON shape in §3 (reuse the existing `_parse_llm_json` /
  `_normalise` salvage helpers already in `ideation-service/app/main.py`).
- Honour `constraints` as hard requirements when present (the Edit loop).
- Keep prompts bilingual-aware (`language`), consistent with the diagnose
  prompts. Tunisian-context grounding stays (sectors, local realities).
- Temperature: low for generate (0.3–0.5), bump on Retry.

Wire to the same Ollama endpoint pattern already used in `/diagnose`
(`OLLAMA_BASE_URL`, `OLLAMA_MODEL`). No new infra.

---

## 6. Orchestrator: mode-aware fan-out

New module `backend/orchestrator/app/generation/runner.py` mirroring
`diagnostic/runner.py`:
- `run_generation_step(project_id, axis_slug, constraints=None)` — loads
  `profile` + approved upstream `plan_sections`, calls the axis `/generate`,
  returns the proposal (does **not** persist until Approve).
- `persist_section(project_id, axis_slug, content, source)` — applies the
  supersede-and-insert write rule (`01 §2`).
- Respects dependency order from `05-dependency-engine.md` when running multiple
  axes (re-runs).

`diagnostic/runner.py` is the model for SSE progress + the asyncpg pool reuse
(`state_router.get_pool`).

---

## 7. Checklist

- [ ] Define `content` schemas (`_shared/plan_schemas.py` or per-service)
- [ ] Replace `/execute` stub with real `/generate` in all 9 network axes
- [ ] Add per-axis `generate` system prompts; reuse JSON-salvage helpers
- [ ] Reconcile axis 10 in `axis_registry.py` (operations in, gtm out of routing)
- [ ] Update `METRIC_ROUTES` for the new axis set
- [ ] `generation/runner.py` in orchestrator (fan-out + persist + SSE)
- [ ] Unit-smoke each axis `/generate` returns valid `content` for a sample idea
- [ ] Keep `/diagnose` + `due_diligence` untouched
