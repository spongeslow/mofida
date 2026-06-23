# 03 — Creation Flow ("Got any idea?")

> Implements new-logic.md §2. Replaces the faked creation path with a real
> step-by-step generation loop, the interactive plan document, and PDF export.
> Depends on `02-axis-dual-mode.md` (generate endpoints) and `01` (`plan_sections`).

---

## 1. Entry point (§2.1)

Landing page (`App.tsx` + landing component): replace the "New Project" button
with **"Got any idea?"** → opens a textarea → "Let's build it".

- On submit: `POST /project/new` (existing) with `{name, language}`, then
  `PATCH /project/{id}/profile` storing the raw idea (e.g.
  `profile.raw_idea`). State stays `NEW` (= creation mode).
- Route into `CreationFlow.tsx` with the new project id.

i18n keys: `creation.gotIdea`, `creation.ideaPlaceholder`, `creation.build`.

---

## 2. Backend endpoints (orchestrator)

New `creation_router.py` (mounted under `/api/v1`), using
`generation/runner.py` from `02 §6`:

| Method & path | Body | Returns |
|---------------|------|---------|
| `POST /project/{id}/generate/{axis}` | `{constraints?}` | proposal `{content, summary, assumptions, needs_input}` (not persisted) |
| `POST /project/{id}/generate/{axis}/approve` | `{content}` | persists live `plan_sections` row; `{version}` |
| `POST /project/{id}/generate/{axis}/retry` | — | fresh proposal (constraints=null) |
| `GET  /project/{id}/plan` | — | all live `plan_sections` (the assembled plan) |
| `POST /project/{id}/finalize` | — | runs roadmap (axis 10), sets `plan_complete=true` |

The "Edit" action is just `POST .../generate/{axis}` with `constraints` =
edited text, so no separate endpoint. Progress streams over existing SSE.

**Sequencing rule:** axis N's generate call loads all *approved* upstream
sections as `upstream` context (`02 §2`). The loop walks the dependency order
(`05`) for the nine axes, then roadmap last.

---

## 3. Per-axis card UI (§2.2)

`CreationFlow.tsx` becomes a real loop (it currently builds cards from
diagnostic output — rework it):

- **Stepper sidebar** — nine axes + roadmap, each `pending | current | done`,
  with "4 / 9 axes complete" counter.
- **Proposal card** for the current axis renders `content` via an axis-aware
  renderer (`PlanSectionView`, shared with the document view §5):
  - **Approve** → call approve endpoint, advance stepper to next axis, auto-fire
    its `generate`.
  - **Edit** → inline textarea (and/or structured fields) → submit as
    `constraints` → show the re-generated proposal.
  - **Retry** → call retry endpoint.
- Show `assumptions` and any `needs_input` prompts inline so the founder can
  answer before approving.

Reuse `ReviewCard.tsx` patterns but the actions now hit real endpoints.

---

## 4. Completion screen (§2.3)

After Sales is approved, `POST /finalize`:
1. Orchestrator generates the **Roadmap** (RAG, `07`) from all approved sections,
   persists it as `plan_sections[axis='roadmap']` and a `roadmap_versions` row.
2. Frontend shows the completion screen:
   - Assembled plan in the interactive document view (§5).
   - **Export as PDF** (§6).
   - **View Dashboard** → transition to the (now multi-project) dashboard `08`.

---

## 5. Interactive plan document (§2.4)

`PlanDocument.tsx` — collapsible, one section per axis:
- Axis label + `summary` + key decisions + rendered `content`.
- **Inline "Edit" per section** → triggers the dependency engine path
  (Source A in `06-continuous-updates.md §2`): edit → re-generate affected
  downstream axes → review their proposals → log an `event`.
- This is the "living plan" surface; it is reachable from the dashboard at any
  time, not just at completion.

`PlanSectionView` (renderer) is shared between the creation card and this
document so the axis `content` shapes render identically.

---

## 6. PDF export (§2.3, gap G14)

- **Approach:** client-side render of the assembled plan to PDF to stay 100%
  local and avoid a backend headless-browser dependency. Use a lightweight lib
  already friendly to Vite (e.g. `jspdf` + `html2canvas`, or `react-pdf`/
  `@react-pdf/renderer`). Pick one in `08`'s dependency review.
- Render the `PlanDocument` sections + scores/roadmap into a branded template
  (Warm Autumn theme, Playfair/Jakarta fonts).
- Button on completion screen and on the plan document.
- **Alternative** if a server-side route is preferred later: orchestrator
  endpoint that templates HTML → PDF; not needed for the demo.

---

## 7. Checklist

- [ ] Landing: "Got any idea?" textarea → create project + store `raw_idea`
- [ ] `creation_router.py` (generate / approve / retry / plan / finalize)
- [ ] Rework `CreationFlow.tsx` into a real loop against those endpoints
- [ ] `PlanSectionView` axis-aware renderer (shared)
- [ ] `PlanDocument.tsx` collapsible living document with inline edit
- [ ] `POST /finalize` runs roadmap + sets `plan_complete`
- [ ] PDF export (client-side) on completion + document
- [ ] i18n keys (fr/en/ar parity); SSE progress wired
- [ ] Remove/retire the faked-creation code path
