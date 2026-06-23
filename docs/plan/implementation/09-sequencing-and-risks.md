# 09 — Sequencing, Milestones & Risks

> Execution order across the workstreams, the hackathon demo cut-line, and the
> risks worth pre-empting.

---

## 1. Dependency between workstreams

```
01 data-model ─┬─► 02 axis dual-mode ─┬─► 03 creation flow ─┐
               │                       │                     ├─► 08 multi-project/frontend
               ├─► 05 dependency engine┘                     │
               ├─► 04 diagnosis flow ───────────────────────┘
               └─► 06 continuous updates ──► 07 roadmap engine
```
- `01` unblocks everything (schemas).
- `02` (real generate) unblocks `03` and the creation-mode re-runs in `05`/`06`.
- `05` unblocks `06` (all sources call the scheduler).
- `07` consumes `05`/`06` triggers (stale flag, score deltas) and `04` (uploads → KB).

---

## 2. Phased milestones

### Phase A — Foundations (unblocks all)
1. `01` migrations `006–012` applied.
2. `02` real `/generate` in all axes + axis-10 reconciliation.
3. `05` dependency engine + §5.5 unit test.

**Exit:** an axis produces a real structured proposal; `affected_axes()` matches
the doc's worked example.

### Phase B — Flows (demo core)
4. `03` creation loop + plan document + PDF export.
5. `04` diagnosis + PDF upload/extraction + Debate + history compare.
6. `08` project selector + per-project state.

**Exit:** create a project from an idea end-to-end, export PDF; diagnose an
existing one with an uploaded PDF and debate a score; switch between projects.

### Phase C — Liveness (the wow)
7. `06` four sources + Event Feed + DiffView.
8. `07` progress-aware roadmap + score re-prioritisation + KB versioning.

**Exit:** a daemon event card → Act → axes re-run → event logged with diff;
checking off a horizon generates next actions; a score drop re-prioritises.

### Phase D — Polish
9. "What's new?" voice/chat summary, celebration UX, provenance panel, filters,
   i18n sweep, empty/error states.

---

## 3. Hackathon demo cut-line

If time is short, ship **Phase A + B + two Phase-C highlights**:
- ✅ Creation flow with real generation + PDF export (`03`).
- ✅ Diagnosis with PDF upload + Debate (`04`).
- ✅ Multi-project selector (`08`).
- ✅ One daemon Event Card with Act/Manual/Ignore (`06 §5`) — the liveness story.
- ✅ Progress-aware roadmap: check an action → new action appears (`07 §3`).

Defer: tool-signal interpretation breadth (`06 §3`), KB anonymised promotion,
history-compare polish, "What's new?" voice. They are narratively nice but not
load-bearing for the pitch.

---

## 4. Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **BM↔Operations dependency cycle** (§5.5 table) | Re-run never terminates | Explicit SCC handling in `05 §3`; unit test |
| **Axis-10 mismatch** (`gtm` vs `roadmap`/`operations`) | Inconsistent fan-out | Reconcile in `02 §4` *first*, in Phase A |
| **Local LLM JSON reliability** for `/generate` | Broken proposals | Reuse `_parse_llm_json` salvage; strict schema + retry; low temp |
| **Single-project store leaks state on switch** | Wrong data shown | Explicit `setActiveProject` reset (`08 §2`) |
| **Auto re-runs overwrite user work** | Trust loss | Creation re-runs always produce *proposals to review* (`05 §4`); only daemon/tool "Act" auto-applies, always logged |
| **PDF extraction on scanned decks** | No text | Accept text PDFs only for demo; warn; OCR later |
| **KB versioning scope creep** | Time sink | Catalogue + monotonic version is enough; defer anonymised global promotion |
| **SSE event volume** during fan-out | UI jitter | Batch progress; one summary `event` per scheduler run, not per axis |
| **Migrations not applied** (recurring footgun) | Endpoints 500 | Add a `scripts/migrate.sh` run-all; document in README |
| **Cargo/Tauri offline build** | Frontend won't ship | Keep client-side PDF + browser File API; no new native plugins (consistent with prior decisions) |

---

## 5. Definition of done (per workstream)

- Migrations applied + idempotent.
- New endpoints covered by at least a smoke test / curl in `scripts/`.
- Dependency engine has the §5.5 unit test green.
- Every new UI string present in fr/en/ar at parity.
- `cargo check` green offline (no new native plugins).
- Each `events`-producing path writes a row with a renderable `diff`.
- README "What it does" updated to describe both modes + liveness.

---

## 6. Open questions for the team

1. Keep `go-to-market-service` container running but unrouted, or remove it now?
   (Recommended: keep, retire later — `02 §4`.)
2. Client-side PDF (jspdf/react-pdf) acceptable, or is a server route wanted?
   (Recommended: client-side — `03 §6`.)
3. Should tool-signal "Act" auto-apply structured patches without review, or
   always queue proposals? (Doc implies auto-apply for structured tool data;
   confirm for the demo.)
4. Anonymised upload → global KB promotion: in or out for the hackathon?
   (Recommended: out.)
