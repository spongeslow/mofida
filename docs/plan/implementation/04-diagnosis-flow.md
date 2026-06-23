# 04 — Diagnosis Flow ("Diagnose existing")

> Implements new-logic.md §3. Most of this exists; the new work is **PDF
> upload → text extraction → evidence**, the **per-axis Debate chat**, and the
> **diagnostic history compare** view.

---

## 1. Current state

- Intake is stateless (`intake_router`): `/intake/start`, `/intake/answer` →
  `profile_patch`. Frontend `IntakeWizard.tsx` (supports `mode="update"`).
- `POST /project/{id}/diagnose` flips to `EXISTING`; `POST .../run-diagnostic`
  fans out all axes (evaluate) + roadmap, persists to `diagnostic_history`.
- Dashboard renders scores/blockers/roadmap. `POST .../review` only echoes via
  SSE (no recompute) — this becomes Debate.

So §3.2 (thorough run) and §3.4 history-storage largely exist. Gaps: PDF
upload/extraction (§3.1), Debate recompute (§3.3), history **compare** (§3.4).

---

## 2. PDF upload + text extraction (§3.1, gap G5)

**Intake wizard** gains an optional file step (one or more PDFs: business plan,
pitch deck, financials).

Backend:
- `POST /project/{id}/documents` (multipart) → stores file, extracts text.
  - Extraction: `pypdf`/`pdfplumber` (pure-Python, local). For scanned PDFs,
    OCR is **out of scope** for the demo — accept text-based PDFs, surface a
    "no extractable text" warning.
- Persist extracted text into `knowledge_base` with `source='upload'`,
  `project_id=<id>` (`01 §5`) and embed into Qdrant so it's retrievable.
- Each axis `/diagnose` request gains an `evidence_docs` field = the project's
  uploaded text (or top-k retrieved chunks) so axes cite it.

Frontend: file input in `IntakeWizard.tsx` (reuse the browser File API pattern
already used by `RecentProjectsPicker` — no native dialog plugin). Show parsed
filename + extracted-char count as confirmation.

---

## 3. Diagnostic run (§3.2)

Largely unchanged — `run-diagnostic` already returns
`scores, confidence, evidence, blockers, justifications, due_diligence,
axis_outputs, roadmap`. Additions:
- Pass `evidence_docs` to each axis (above).
- Persist a per-axis evidence/justification snapshot so the history-compare view
  (§5) and the Debate view can read them. `diagnostic_history` stores
  aggregate today; add a child table or extend `evidence` JSONB to hold the
  per-axis breakdown if not already present.

---

## 4. Per-axis Debate chat (§3.3, gap G6)

Replaces the no-op `/review`. For a given axis the user opens a chat arguing the
score.

Backend `POST /project/{id}/axis/{axis}/debate`:
```jsonc
// request
{ "language":"fr", "message":"We actually have 40 signed LOIs", "history":[...] }
// response
{ "reply":"...", "score_changed":true, "new_score":3.8, "locked":true,
  "rationale":"LOIs are verified demand evidence (mi=1.0)" }
```
- The axis service gets a `/debate` (or the orchestrator runs a focused LLM call
  with the axis's current evidence + the user's argument).
- If the model is convinced, it **recomputes** that axis score using the same
  `ci = wi·vi·mi` formula (README), writes a new `diagnostic_history`-linked
  score, **locks** it (no further auto-change this run), and logs an `event`
  (`source='chat'`). If not convinced, score stays; reply explains why.

Frontend: "Debate" button on each axis card opens a chat modal (reuse
`ChatPanel.tsx` styling). Show locked badge + delta when recomputed.

---

## 5. Diagnostic history & compare (§3.4)

- **List** past runs (exists: `mon-parcours/HistoryList.tsx`, `ScoreChart.tsx`).
- **Compare two runs:** new `GET /project/{id}/history/compare?from=&to=`
  returns per-axis score deltas, evidence added/removed, blocker
  resolved/new. Render as a side-by-side table (improvement ▲ / decline ▼).
- Blocker resolution tracking: diff blockers by stable code between runs.

---

## 6. Diagnosis re-run on updates

Per §1 of new-logic.md, diagnosis mode can be re-triggered on demand or when
significant updates occur. Wire the re-run trigger into the continuous-update
pipeline (`06`): a tool/daemon/chat signal on a `diagnosis`-mode project queues
a (quick or full) diagnostic re-run instead of a creation re-generate.

---

## 7. Checklist

- [ ] `POST /project/{id}/documents` upload + `pypdf` extraction → `knowledge_base`
- [ ] Embed uploaded text into Qdrant; pass `evidence_docs` to axis `/diagnose`
- [ ] IntakeWizard optional file step (browser File API)
- [ ] `POST /project/{id}/axis/{axis}/debate` → recompute + lock + event
- [ ] Debate chat modal per axis (replace no-op `/review`)
- [ ] Per-axis evidence snapshot persisted for compare/debate
- [ ] `GET /history/compare` + side-by-side compare UI
- [ ] Diagnosis-mode re-run path hooked to `06`
