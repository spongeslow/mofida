
# Moufida UI — Implementation Plan

This plan turns `docs/ui-analysis.md` into an ordered, checkable execution roadmap. It follows
the §E "fix-first" priority order. Each phase is independently shippable and verifiable
(`cd frontend && npm run build` must pass after each step).

Legend: `[ ]` todo · `[~]` in progress · `[x]` done.

---

## Phase 1 — Character consolidation (FOUNDATION)

> Locked decision (analysis §D): one character system — the **pixel** Moufida — everywhere.
> Retire the SVG (`MoufidaCharacter.tsx`, the "old design") and port its full expressive range
> into the pixel renderer, then push it further.

### Step 1.1 — Swap all render sites to the pixel character ✅ DONE
- [x] Move the `CharacterState` string-union type out of `MoufidaCharacter.tsx` into the pixel
      module (`pixelArt/moufida.ts`) so typed state logic survives the SVG's deletion.
- [x] Replace the 5 SVG render sites with `PixelMoufida` (`cssScale ≈ size / 92`):
  - [x] `components/companion/index.tsx` — `size={112}` → `cssScale={1.2}`
  - [x] `components/pitch/PitchSimulator.tsx` — `size={92}` → `cssScale={1.0}`, `size={56}` → `cssScale={0.6}`
  - [x] `components/persona/PersonaGallery.tsx` — `size={56}` → `cssScale={0.6}`
  - [x] `components/persona/PersonaChat.tsx` — `size={40}` → `cssScale={0.45}`
  - [x] `components/scenario/ScenarioPlannerPanel.tsx` — `size={44}` → `cssScale={0.48}`
- [x] Delete `components/companion/MoufidaCharacter.tsx`.
- [x] `tsc --noEmit` passes; no remaining `MoufidaCharacter` imports.

### Step 1.2 — Port the SVG's states into the pixel renderer ✅ DONE
Extended `pixelArt/moufida.ts` (`drawChar` + new rect/overlay helpers). Shared by both the in-app
`PixelMoufida` and the desktop pet (`companion.ts`), so every pose lands in both at once.
- [x] **Mouth layer** (`getMouth`): `smile` (default) / `open` (speaking flap) / `o` (surprised) / `frown` (skeptic, worried).
- [x] **Arm-pose set** (`getArmClear` + `getArmPose`): chin (thinking/processing), crossed (skeptic), pointing-left, raised-both (celebrate), right-up (presenting), forward (reading).
- [x] **Accessory overlays** (`getAccessory`): briefcase (skeptic), pointer (presenting), book (reading).
- [x] **Particle/overlay layer**: confetti (`drawParticles`, celebrate), `!` bubble (alert/surprised/startled), sweat drop (worried).
- [x] **Body offsets** (`bodyOffset`): hop (alert/celebrate/surprised), slump (worried/sleeping).
- [x] Closed-eyes overlay when `sleeping` (not just blink).
- [x] All 15 states route through real visuals; speaking flap & confetti are time-driven (no signature change).
- [x] `tsc --noEmit` passes. _(Pending: visual confirmation of a few states in the running app.)_

### Step 1.3 — Pixel character improvements beyond parity ✅ DONE
- [x] Per-page palette swaps: `PaletteName` + `THEME_OVERRIDES` + `paletteFor()` in `moufida.ts`;
      `PixelMoufida` gains a `theme` prop; pitch→blue, scenarios→purple, parcours→green.
- [x] Idle variety: randomized wave cadence (3–8 s) in `PixelMoufida`.
- [~] Smooth transitions: time-driven anims smooth most states (hard cut on instant state change remains).

---

## Phase 2 — Make the character reactive & narrative ✅ DONE

### Step 2.1 — Persistent reactive companion across views ✅ DONE
- [x] `MoufidaCompanion` (was unmounted) now rendered globally in `App.tsx` for all main views.
- [x] Store gains `companionPulse` + `pulseCompanion()`; SSE consumer pulses on critical alert
      (alert), review_ready (surprised), horizon_complete (celebrating); dashboard pulses
      thinking→celebrating/worried around the diagnostic; sleeps when daemon paused.

### Step 2.2 — Narrate the creation flow ✅ DONE
- [x] Per-axis narration speech bubble (fr/en/ar) explaining why each axis matters (analysis §1).
- [x] Completion now plays `celebrating` (was `speaking`, a no-op).
- [~] Per-action approve/retry/edit reactions: completion celebrate done; in-card approve/retry
      micro-reaction left light (flow advances immediately to next axis).

### Step 2.3 — Wire the desktop pet to events ✅ DONE
- [x] `App.tsx` forwards `companionPulse` to the `companion` window then restores base state;
      `companion.ts` state type widened to the full `CharacterState`.

---

## Phase 3 — Diagnostic progress + surface invisible backends

### Step 3.1 — Live diagnostic progress (analysis §2) ~ PARTIAL
- [~] Companion reacts (thinking→celebrating) + score gauges animate live as `score_update`
      SSE events land. Full per-axis/wave progress panel + cancel/abort still TODO (needs
      backend per-axis progress events).

### Step 3.2 — Surface high-value invisible backends (analysis §17) ✅ DONE
- [x] **Document upload** — 📎 button + status in the dashboard header over `uploadDocument()`.
- [x] **Score debate** — 💬 "Débattre du score" inline chat on every gauge over `debateAxis()`;
      applies `new_score` live and locks when the backend locks.
- [x] **Diagnostic compare** — `CompareDiagnostics` card in Mon Parcours over `compareHistory()`
      (per-score deltas + resolved/new blockers).

### Step 3.3 — Kill raw-data leaks & add states (analysis §6, §28) ~ MOSTLY DONE
- [x] HUD ReviewCard now renders via `PlanSectionView` (no more raw `JSON.stringify` `<pre>`).
- [x] SSE connection indicator in the sidebar (`sseConnected` store + `SSEIndicator`).
- [~] Broad per-card empty/loading states + surfacing failed axes still TODO.

---

## Phase 4 — Navigation restructure (analysis §18, §19) ✅ DONE
- [x] `View` type + sidebar gain dedicated **Personas / Pitch / Scénarios** pages (new icons);
      rendered in `App.tsx` with per-page companion themes.
- [x] Dashboard refocused: Personas/Pitch cards and the scenario modal removed; What-if now
      navigates to the Scénarios page.
- [x] Active-state nav indicator already present (`mf-nav-item.active` + accent dot).
- [ ] Base de Connaissances entry — deferred to Phase 7 (KB browser).

## Phase 5 — Gamification / progression (analysis §D3) ✅ MOSTLY DONE
- [x] Score count-up animations (`useCountUp` in ScoreGauge) + diagnostic-complete celebrate.
- [x] Maturity stage as a visible "level" ladder + next-stage label (`StageLadder` in MaturityCard).
- [x] Milestone badges (`AchievementsCard` in Mon Parcours): 6 milestones derived from live state,
      persisted per project, celebrate pulse on first unlock.
- [ ] Streak / daily check-in tied to the daemon — deferred.

## Phase 6 — Persistence (analysis §26) ✅ DONE
- [x] HUD chat history persisted per project in localStorage (survives navigation/refresh).
- [x] Creation-flow position (`currentIdx` + approved sections) persisted; cleared on completion.
- [x] Scenario drafts persisted per project (`ScenarioPlannerPanel`).

## Phase 7 — Depth & polish ✅ DONE
- [x] Ambient texture applied to all in-app views (`mf-textured` on the content shell).
- [x] Per-page character costume palettes (Phase 1.3) + per-view companion theme.
- [x] Watch-targets UI (`WatchTargetsCard` in HUD) over new `getWatchTargets`/`refreshWatchTargets`.
- [x] "Add knowledge" UI (`KbAddCard` in HUD) over `addKbEntry()`.
- [x] **Knowledge Base browser** — new backend `GET /resources` (RAG, disk-backed) +
      orchestrator proxy `GET /api/v1/kb/resources` + dedicated **Base de Connaissances** page
      (`KnowledgeBase.tsx`) with stage/type/sector filters and inline reading.
- [x] **Inline citations** (§25): backend `format_evidence_block` now numbers sources `[n]`
      (aligned with `build_citations`) and instructs inline citing; `PlanSectionView` renders
      `[n]` markers as clickable superscript links (graceful no-op when absent).
- [x] Sound cues (`sfx.ts`): synthesized chimes on celebrate / alert / surprised pulses,
      gated by companion visibility.

---

## Status: all phases implemented
Remaining nice-to-haves (not blocking, noted for later): streak/daily check-in (Phase 5),
full per-axis/wave live diagnostic progress panel + cancel (Phase 3.1), broad per-card
empty/loading states (Phase 3.3). Everything else in the plan is done and typechecks clean.

---

## Working agreement
- One step at a time; `npm run build` green before moving on.
- Match existing code style (inline styles, theme tokens, i18n `useT`).
- Update this file's checkboxes as steps complete.
