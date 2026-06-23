# 08 — Multi-Project & Frontend Surface

> Implements new-logic.md §4 plus the consolidated frontend component inventory
> for every workstream. Backend already supports many `profiles` rows and
> `GET /projects`; the work is UI + per-project state isolation.

---

## 1. Project selector (§4.1)

- `GET /projects?limit=20` already returns recent projects with latest maturity
  stage. Add `mode` (creation/diagnosis, from `01 §1`) and `name` to the payload.
- New `ProjectSelector.tsx` in the dashboard header: dropdown/tab bar listing
  projects with mode + maturity badge + `[+ New Project]`.
- Selecting a project sets the active `projectId` in `store.ts`; all dashboard
  panels key off it.

---

## 2. Per-project state isolation (§4.2)

`store.ts` currently holds one project's state. Refactor to key state by
`projectId` (or fully reset on switch). Each project independently carries:

| State | Source |
|-------|--------|
| Scores | diagnostic runs (diagnosis) / plan baseline (creation) |
| Roadmap | `roadmap_versions` live row |
| Plan sections | live `plan_sections` (creation only) |
| Events | `events` feed |
| History | `diagnostic_history` / plan version timeline |

Switching projects must **not** leak state (a real bug risk with the current
single-project store). Add an explicit `setActiveProject(id)` that clears
derived caches and refetches.

---

## 3. Cross-project operations (§4.3)

- **Create** — "Got any idea?" (creation) or "Diagnose existing" (diagnosis).
- **Import** — JSON import exists (`RecentProjectsPicker` File API). Extend to
  accept a plan JSON → `POST /project/new` + restore `plan_sections`.
- **Delete** — `DELETE /project/{id}` (cascades via FK `ON DELETE CASCADE`);
  confirm dialog. Add the endpoint to `state_router`.
- **Switch** — §1, without state loss.

---

## 4. Landing page changes (§9 mapping)

- "New Project" → **"Got any idea?"** textarea (`03 §1`).
- "Diagnose existing" → intake + PDF upload (`04`).
- Recent-projects picker stays; route selection through `ProjectSelector`.

---

## 5. Component inventory (new / changed)

| Component | File | Workstream |
|-----------|------|-----------|
| Landing "Got any idea?" | `App.tsx` / landing | `03` |
| `CreationFlow` (real loop) | `intake/CreationFlow.tsx` (rework) | `03` |
| `PlanSectionView` (axis renderer) | new, shared | `03` |
| `PlanDocument` (living doc + inline edit) | new | `03`,`06` |
| PDF export button | new util | `03` |
| IntakeWizard + file step | `intake/IntakeWizard.tsx` | `04` |
| Debate chat modal | new (reuse `ChatPanel`) | `04` |
| History compare | `mon-parcours/*` (extend) | `04` |
| `ProjectSelector` | new | `08` |
| `EventFeed` + filters | new | `06` |
| `DiffView` (field-level) | new, shared | `06`,`04` |
| Event Card (Act/Manual/Ignore) | extend `hud/AlertFeed.tsx` | `06` |
| Chat-driven updates | `hud/ChatPanel.tsx` (extend) | `06` |
| "What's new?" surface | `ChatPanel` + voice | `06` |
| Roadmap progress/regen/reprioritise | `dashboard/RoadmapTimeline.tsx` (extend) | `07` |
| KB provenance ("based on sources") | new small panel | `07` |

---

## 6. State/store changes (`store.ts`, `api.ts`, `types.ts`)

- `api.ts`: add the ~20 new endpoints (creation, debate, events, rerun, roadmap
  advance/regenerate, documents, kb, delete). Keep the existing `/api/v1` base.
- `types.ts`: `PlanSection`, `EventRecord`, `ToolSignal`, `KbSource`,
  `RoadmapAction` (+`axis_slug`,`horizon`), `Project` (+`mode`).
- `store.ts`: `activeProjectId`, per-project slices, SSE-driven event/feed
  updates, review queue for pending re-run proposals.

---

## 7. Theming / consistency

- All new components use the Warm Autumn theme + Playfair/Jakarta fonts already
  in `theme.ts`/`styles.ts`. Companion reactions (celebration on completion)
  reuse the `emitTo("companion", ...)` channel.
- Every string in `locales/{fr,en,ar}.json` at parity; RTL already handled.

---

## 8. Checklist

- [ ] `ProjectSelector` + `GET /projects` (add `mode`,`name`)
- [ ] `store.ts` keyed by active project; no state leak on switch
- [ ] `DELETE /project/{id}` + confirm dialog
- [ ] Plan-JSON import/export round-trip
- [ ] Wire all new components into routing (`App.tsx`)
- [ ] `api.ts`/`types.ts` additions; SSE-driven feed
- [ ] i18n parity across fr/en/ar for every new key
