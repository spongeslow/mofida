# Moufida Desktop UI — Complete Analysis

> **How to read this document.** Part I (sections A–E) is the strategic layer: what the
> product feels like from an entrepreneur's chair, what is genuinely good, the sharpest
> criticisms, the entertainment/character direction, and a fix-first priority order.
> Part II (sections 1–29) is the detailed, code-verified feature-by-feature inventory.
> Strategy was added on top of the inventory after a full pass over the frontend source;
> where the inventory and code disagreed, corrections are noted inline (see §10, §21).

---

# PART I — STRATEGIC ANALYSIS (entrepreneur's perspective)

## A. The core problem: a powerful engine behind a flat, silent dashboard

After walking the whole app as an entrepreneur, the single biggest gap is **not** missing
features — it's that **Moufida feels thinner and more impersonal than she actually is.**
The backend can debate a score with me, ingest my business plan, compare two diagnostics,
project pivot scenarios, simulate investors and customers, and watch the market 24/7. But
the UI surfaces almost none of that emotionally, and the character who is supposed to be my
"co-founder" is mostly a decorative sprite that reacts to nothing.

Three structural problems cause most of the pain:

1. **The dashboard is a wall of cards.** Twelve cards stack vertically with no hierarchy,
   no "what should I look at first," and deep interactive tools (Personas, Pitch) wedged in
   as cards next to at-a-glance health widgets. A first-time founder scrolls a long page and
   doesn't know where their startup actually stands or what to do next.

2. **The best character asset is hidden; the weak one fronts the journey.** The expressive
   SVG Moufida (14 states, costumes, blinking, sparkles, mouth-sync, a whole CSS keyframe
   system) appears **only on dashboard cards**. Every emotionally important moment — landing,
   intake, the creation flow, chat, the desktop pet — uses the **pixel canvas**, which is far
   less expressive and whose "states" are largely cosmetic (see §10/§21 corrections). The one
   moment that should feel triumphant — finishing the full plan — renders the pixel character
   in `speaking` state, which looks identical to idle.

3. **A lot of real power has zero UI**, so the product feels like a scorecard rather than an
   advisor: score debate, document upload, diagnostic compare, the 65+ knowledge base, saved
   scenarios, and watch-targets all exist in the backend and are invisible (see §17).

The fix is less "build more backend" and more "**make what exists visible, legible, reactive,
and alive.**"

---

## B. What is genuinely well-built (don't break these)

A fair critique has to start with credit — several things are above hackathon bar:

- **The SVG character system** (`MoufidaCharacter.tsx` + `styles.ts`) is excellent: 14 states
  driven by clean CSS classes, real keyframe animations (idle float, listen tilt, think
  bubble pulse, speak mouth-flap, alert jump, celebrate spin + sparkles, sleep ZZZs), eye
  blink groups, and even costume overlays (skeptic briefcase, presenting pointer). This is the
  asset to build the whole personality around — it is currently underused.
- **The design system is coherent.** A single warm-autumn palette, two well-paired fonts,
  consistent `card`/`btn`/`inputStyle` tokens, a 5-tier `scoreColor` grammar, and a real
  animation utility set (`mf-anim-card`, `mf-anim-row`, shimmer skeletons, toast-in, view
  transitions, button press). The bones for a polished, animated UI are already here.
- **Sector-adaptive theming works.** `setAccent()` maps the project sector to `--mf-accent`
  and a textured background variable — the infrastructure for "the app dresses itself for my
  industry" exists; it's just barely used (see §C).
- **The creation flow's skeleton is right**: stepper, per-axis review with approve/edit/retry,
  assumptions/needs-input callouts, progress bar, a finalize step, and a printable plan view.
  The structure is sound; what's missing is narrative, reaction, and explanation.
- **Real-time plumbing is real.** 12+ SSE event types are wired to the store. The data is
  flowing; it just isn't dramatized in the UI (no live progress, no connection indicator).

---

## C. Sharpest criticisms of what's currently implemented

These are critiques of existing code, not missing features:

1. **Two character systems, and the worse one is on the critical path.** Maintaining both a
   pixel canvas and an SVG character doubles the work and guarantees inconsistency. The pixel
   version is the one users meet first and most often, yet it's the least expressive.
   **Resolved direction (see §D decision):** consolidate on the **pixel** character everywhere,
   retire the SVG, and invest in the pixel renderer to bring it up to (and past) the SVG's
   expressiveness — see §D5 for the per-state port spec.

2. **The pixel character's "states" are partly fictional.** `drawChar()` only renders distinct
   visuals for `thinking`, `listening`, `sleeping`, and `startled` (as small bubbles), plus a
   walk-leg toggle and idle wave. `speaking`, `alert`, `celebrating`, `processing`, `walk`, and
   `idle` produce **no body change** — the body sprite is static. Calling
   `PixelMoufida state="celebrating"` is currently a no-op visually. The §21 claim of "8 states"
   is generous; it's really ~4 bubble overlays on one static pose.

3. **The dashboard has no information architecture.** Everything is a sibling card in one
   scroll. There's no "your startup at a glance" hero, no separation of *health* (scores,
   blockers) from *tools* (personas, pitch, scenarios) from *intel* (competitors,
   opportunities, events). Founders can't triage.

4. **The character is decorative, not communicative.** Across the whole app, Moufida never
   *says anything in her own voice* outside the chat panel. She floats and blinks but doesn't
   narrate the creation flow, doesn't congratulate an approval, doesn't warn when a score
   drops. She's a mascot, not an advisor. This is the single biggest missed opportunity for
   "meaningful and entertaining."

5. **Raw data leaks to the user.** `JSON.stringify()` fallbacks in the plan renderer and the
   HUD ReviewCard `<pre>` block expose raw JSON; score tiers rely on color alone; justification
   text is unformatted. These small leaks make a sophisticated product feel unfinished.

6. **State is fragile.** Creation-flow position, HUD chat history, scenario drafts, and intake
   answers all live in component/Zustand memory and vanish on refresh — even though the
   backend has tables for several of them. A founder who closes the app mid-plan loses their
   place.

7. **Failures are silent.** Failed diagnostic axes return `null` and simply disappear; SSE
   drops show stale data with no indicator; web search returns `[]` on timeout with no signal.
   The app never admits when something went wrong, which erodes trust more than an honest error.

---

## D. Entertainment & character direction (the "appealing, alive, fun" layer)

This is the heart of the request: make Moufida a companion an entrepreneur *wants* to open.
Concrete, code-grounded direction:

> ### ★ DECISION (locked): one character system — the **pixel** Moufida
>
> The app standardizes on the **pixel-art character** (`PixelMoufida` / `pixelArt/moufida.ts`)
> **everywhere**. The SVG character (`MoufidaCharacter.tsx`, the "old design") is **retired** —
> it should no longer be rendered anywhere, and is eventually deleted.
>
> This means the work is **not** "promote the SVG"; it is the opposite — **invest in the pixel
> character so it carries the full emotional range the SVG had.** The pixel sprite is currently
> the least expressive renderer (per §10/§21 it only draws bubbles for 4 states on a static
> body), so making it the *only* character is a deliberate trade: we accept a single, charming,
> retro art direction and then do the work to make it genuinely emote.
>
> **Scope of this fix (two parts):**
>
> **Part 1 — Swap every render site to the pixel character.** Replace all 5 SVG usages with
> `PixelMoufida`. The SVG `size` prop (px width) maps to the pixel `cssScale` prop via
> `cssScale ≈ size / 92` (the pixel canvas is natively 92px wide):
>
> | File | Current (SVG) | Replace with (pixel) |
> |---|---|---|
> | `companion/index.tsx:59` | `state={charState} size={112}` | `state={charState} cssScale≈1.2` |
> | `pitch/PitchSimulator.tsx:150` | `state={charState} size={92}` | `state={charState} cssScale≈1.0` |
> | `pitch/PitchSimulator.tsx:95` | `state="skeptic" size={56}` | `state="skeptic" cssScale≈0.6` |
> | `persona/PersonaGallery.tsx:67` | `state="pointing_left" size={56}` | `state="pointing_left" cssScale≈0.6` |
> | `scenario/ScenarioPlannerPanel.tsx:197` | `state={…} size={44}` | `state={…} cssScale≈0.48` |
> | `persona/PersonaChat.tsx:87` | `state={charState} size={40}` | `state={charState} cssScale≈0.45` |
>
> Keep the `CharacterState` string-union type (move it out of `MoufidaCharacter.tsx` into the
> pixel module, e.g. `pixelArt/moufida.ts` or `PixelMoufida.tsx`, so the SVG file can be deleted
> without breaking the typed state logic in `PersonaChat`, `PitchSimulator`, and
> `companion/index.tsx`). Then delete `MoufidaCharacter.tsx`.
>
> **Part 2 — Port the old design's 14 states into the pixel character and improve it.** This is
> the real value: give the pixel sprite real pose/overlay changes for every state the SVG had,
> so swapping renderers doesn't lose expressiveness. See §D5 (now the primary character plan)
> for the per-state spec.

### D1. One character, everywhere, reactive
- **The pixel character is the single persistent presence.** Put a small floating pixel Moufida
  (a "companion rail" or bottom-corner avatar) on every in-app view, not just dashboard cards.
  Drive her state from app/SSE events: diagnostic running → `thinking`/`processing`; score
  drop or critical alert → `worried`/`alert`; diagnostic complete or milestone → `celebrating`;
  pitch page → `skeptic`; personas page → `pointing_left`; parcours → `reading`; idle for a
  while → `sleeping`. The triggers are the same as before — but every one of these states must
  first be **implemented in the pixel renderer** (§D5), since most are currently no-ops there.
- **Wire the desktop pet to daemon/app state** (today it walks regardless). Critical alert →
  she stops and shows the alert pose; diagnostic done → she celebrates; daemon paused → she
  sleeps. The desktop companion is the product's most "alive" surface and currently reacts to
  almost nothing.

### D2. Give Moufida a voice in the flow (narration)
- **Narrate the creation flow.** Before each axis, show a speech bubble in Moufida's voice:
  "Let's nail your *Ideation* — this is where I check your idea is sharp enough to defend. Ready?"
  Each axis becomes a beat in a story instead of a silent JSON review. This also solves §1's
  "axes have no explanation" gap in a way that's *characterful* rather than a help tooltip.
- **React to my actions.** Approve → `celebrating` + sparkle + a one-line "Yes! That's a strong
  market read." Retry → `thinking` + "On it, let me try a different angle." Edit → `reading`.
  These are emotional rewards for progress — the cheapest possible dopamine and the biggest
  perceived-quality win.

### D3. A light gamification / progression layer
The product is literally a *maturity* journey — lean into it:
- **Maturity stage as a visible "level"** with a progress track to the next stage and a clear
  "here's what unlocks Growth" (ties to the MaturityCard gap in §22).
- **Milestone badges + celebrations:** first idea captured, all 9 axes approved, first
  diagnostic, first blocker resolved, score improvement, first pitch survived, plan exported.
  Each fires the `celebrating` animation + confetti + a badge that persists in Mon Parcours.
- **A streak / check-in mechanic** tied to the always-on daemon: "Moufida watched your market
  3 days running — here's what changed." Turns the 24/7 watcher into a reason to come back.
- **Score count-up animations** (gauges animate from previous → new value) and a satisfying
  roadmap-checkbox check, so progress *feels* like progress.

### D4. Decoration & atmosphere (cheap polish, big payoff)
- **Use the texture/ambient layer that already exists.** Apply `mf-textured` and a soft
  per-sector ambient gradient to content areas (only the landing page currently has decorative
  glows; everything else is flat sand). The CSS var plumbing is already in place.
- **Per-page accent + character costume**, matching the §20 vision but powered by the existing
  `--mf-accent` system: blue/skeptic for Pitch, purple/glasses for Scénarios, green/reading for
  Parcours, sector hue for Dashboard.
- **Micro-interactions:** extend `mf-press` to cards, hover-lift already exists — add gentle
  parallax on the landing glow, animate the stepper check when an axis completes, and animate
  alert arrival (slide + the character's alert jump).
- **Optional but high-impact for a desktop app:** subtle sound cues (a soft chime on
  approve/celebrate, a low tone on critical alert). Desktop context makes this appropriate.

### D5. Pixel-art character upgrade — PRIMARY character plan (per the §D decision)

Because the pixel character is now the *only* character, this is no longer optional polish — it
is the core of the fix. The goal: **re-implement, in pixel art, every expressive state the SVG
`MoufidaCharacter` had**, then push the pixel character further than the SVG ever went.

**Current pixel renderer (baseline to build on):** `pixelArt/moufida.ts` exposes a single static
`BODY` rect table, a 2-frame `getLegs()` walk toggle, a `BLINK` overlay, a `getWaveArm()` wave,
and `drawChar()` which adds small symbol overlays for only `thinking`, `listening`, `sleeping`,
`startled`. The palette `P` is one hardcoded object. Everything below extends this same model
(rect tables + overlays), so it's incremental, not a rewrite.

**State-by-state port (SVG → pixel).** Each needs a pixel pose table and/or overlay so the state
actually reads:

| State | SVG behavior (old design) | Pixel implementation to add |
|---|---|---|
| `idle` | gentle float + periodic blink/wave | already present — keep; add subtle 1px breathing bob |
| `walk` | (companion only) | already present (leg toggle); fine |
| `listening` | head tilt + ♫ | ♫ exists; add a slight head/ear lean pose |
| `thinking` / `processing` | think bubble + sway | bubble exists; add a hand-to-chin arm variant |
| `speaking` | mouth-flap open/close | add a 2-frame mouth table (closed smile ↔ open) toggled while speaking |
| `alert` | jump + scale + shake | add a vertical "jump" offset table + `!` overlay (extend existing `startled`) |
| `celebrating` | spin + 3 animated sparkles | add arms-up pose + on-canvas confetti/sparkle particles |
| `sleeping` | closed eyes + ZZZ | ZZZ exists; add closed-eye overlay (reuse BLINK-style) + slight slump |
| `skeptic` | frown + darkened dress + briefcase | frown mouth overlay + arms-crossed pose + briefcase accessory rects |
| `presenting` | pointer accessory + lean | extended arm pose + pointer/stick accessory rects |
| `pointing_left` | arm out to the side | left-arm-raised pose (mirror the existing wave-arm logic) |
| `worried` | frown + lowered + dim | frown overlay + lowered body offset + reduced highlight |
| `surprised` | pop up + scale | jump offset + wide-eye overlay + `!` |
| `reading` | book accessory + head down | head-down pose + book accessory rects (held in both hands) |

**Reusable pieces to add to `pixelArt/moufida.ts`:**
- A **mouth table** (smile / open / frown) layered like `BLINK`, selected by state — unlocks
  speaking, skeptic, worried.
- An **arm-pose set** (down / chin / crossed / pointing / raised) so poses read without redrawing
  the whole body.
- **Accessory rect tables** (briefcase, pointer, book, optional glasses) layered as overlays for
  costume states — the pixel analogue of the SVG costume groups.
- A **particle/overlay layer** for celebrate confetti and alert shake.

**Improvements beyond parity (make the pixel character better than the old one):**
- **Per-page / per-sector palette swaps.** Today `P` is one hardcoded object. Add alternate
  palettes (e.g. professional blue for Pitch, purple for Scénarios, green for Parcours) selected
  by page or by the existing `--mf-accent` sector hue — so Moufida visibly "dresses" for context.
- **Richer idle variety** so the most-seen character isn't repetitive: occasional stretch, look
  around, tap foot, or peek — randomized like the existing blink/wave timers.
- **Smoother animation**: more walk frames, eased bob, and a short transition when state changes
  rather than a hard cut.
- **Consistency**: `PixelMoufida` (React) and `companion.ts` (desktop pet) share
  `pixelArt/moufida.ts`, so every new state/pose lands in both the in-app character and the
  desktop pet at once — fixing the §9 "desktop pet reacts to nothing" gap for free.

---

## E. Fix-first priority order (impact × effort, entrepreneur value)

**Tier 1 — do these first (highest perceived value, mostly wiring existing pieces):**
0. **Character consolidation (foundation):** swap all SVG render sites to the pixel character and
   port the SVG's states into the pixel renderer (§D decision + §D5). This must come first —
   the reactive/narrative work below has nothing to show until the pixel states actually emote.
1. Make the character reactive & narrative in the creation flow (D2) and persistent across
   views driven by SSE (D1). Biggest "alive/meaningful" jump once the pixel states exist.
2. Live diagnostic progress panel with per-axis/wave status + SSE-driven score cards (§2).
3. Surface the highest-value invisible backends: **document upload**, **score debate**, and
   **diagnostic compare** — each is one button + a panel over an existing endpoint (§17).
4. Kill the raw-JSON leaks and add empty/error/loading states + an SSE connection indicator
   (§6, §28).

**Tier 2 — structural (bigger but high return):**
5. Restructure navigation: promote Personas, Pitch, and Scénarios to dedicated pages; make the
   dashboard a focused "health + next actions" hub (§18, §19).
6. Gamification/progression layer + milestone celebrations (D3).
7. Persist chat history, creation-flow position, and scenarios (§26).

**Tier 3 — depth & polish:**
8. Knowledge Base browser, watch-targets UI, evidence/source viewer, inline citations (§17, §23, §25).
9. Pixel-character improvements *beyond* state parity: per-page/per-sector palette swaps, idle
   variety, smoother transitions (§D5 "beyond parity"), plus ambient decoration and sound (D4).

---

# PART II — DETAILED FEATURE INVENTORY

## 1. New Project Creation (Axis Generation Flow)

### Current State

When an entrepreneur clicks "J'ai une idée!" and describes their startup idea, they enter a creation flow with a stepper sidebar showing 9 axis labels: Idéation, Marché, Produit, Marque & Innovation, Modèle Économique, Légal & Green, Opérations, Marketing, Commercial. Each axis generates a proposal sequentially. The user reviews structured JSON content (fields like `refined_idea`, `mvp_features`, `competitors`) rendered by per-axis view components. Citations appear as a separate link list at the bottom of the proposal card. The user can Approve, Edit (with constraints), or Retry.

### What's Missing

- Each axis in the stepper has no explanation. It's just a label. An entrepreneur needs to understand why "Idéation" matters before approving its output. Each axis should present a compelling description explaining what it analyzes and why it's critical for the startup's success.

- Evidence sources from the knowledge base and web search are shown as separate clickable links at the bottom rather than woven into the text naturally. For example, instead of showing "See APII study for more details," the text should say "Selon l'étude APII (2026), le marché tunisien du e-commerce artisanal est estimé à 120M TND." Sources should be inline.

- When the LLM returns unexpected fields, the fallback renderer calls `JSON.stringify()` — raw JSON becomes visible to the user. Every axis output should render as natural language text with bullet points, never as raw JSON.

- The character shows "thinking" during generation but doesn't react emotionally to approval (celebration) or retry (encouragement). Moufida should respond to each user action.

- There is no edit preview. When the user clicks Edit, they see a textarea but no diff showing what changed between the previous version and the regenerated one.

- If the app is closed mid-creation, the flow resets on reopen. Approved sections persist in the database but the creation flow starts from the beginning.

- Axes are in a fixed order. Users cannot prioritize or reorder which axes they want to review first.

---

## 2. Diagnostic Logic Flow

### Current State

The diagnostic runs in three dependency-ordered waves: Wave 0 runs ideation, market, and product in parallel. Wave 1 runs brand using Wave 0 outputs. Wave 2 runs business-model, legal, operations, marketing, and sales in parallel. After all waves complete, results are aggregated, persisted, and optional Concept Bottleneck Model and roadmap generation run. The frontend shows a single button "Lancer le diagnostic" that changes to "Diagnostic en cours..." with no further detail. When the API returns results, `applyDiagnosticResult()` populates the Zustand store and dashboard cards render the data. Scores also arrive individually via SSE events (`score_update`, `maturity_update`).

### What's Missing

- There is no visual progress indicator. The user doesn't know which of the 9 axes is being analyzed, whether it's in Wave 0, 1, or 2, or whether post-processing (CBM, roadmap) is happening. A progress panel showing each axis with a spinner, and waves completing with checkmarks, would provide critical feedback.

- Axes that finish during Wave 0 could update in real-time via SSE, but there's no visible card updating live as scores arrive.

- There is no estimated time remaining based on previous diagnostic durations.

- There is no cancel/abort button. Once started, the user must wait for the full diagnostic to complete.

- There is no explanation of quick vs. full diagnostic. The buttons "Lancer le diagnostic" and "Diagnostic rapide" exist but the user doesn't know what's skipped in quick mode (CBM layer and roadmap generation).

---

## 3. Score Display — Gauges and Breakdown

### Current State

Five composite score gauges (market, commercial_offer, innovation, scalability, green) each show a number out of 5, a progress bar, and an expandable section with a breakdown table (sub-dimension, weight, normalized value, tier) and a plain-language justification. Each score has its own accent color. A 5-tier color grammar maps scores to green/yellow/amber/red.

### What's Missing

- There is no debate/challenge button. Despite a complete backend endpoint, API function, and 6 locale keys, there is no "Discuter ce score" button on any gauge. An entrepreneur who disagrees with a score cannot argue their case.

- Only the current score is shown. Previous scores with deltas (↑ +0.3, ↓ -0.5) are not displayed. Users must go to Mon Parcours to see history.

- No benchmark comparison exists. The entrepreneur can't see "Your score vs. average startup at your stage" or "vs. competitors in your sector."

- Low-scoring sub-dimensions don't link to their corresponding recommendation in the RecommendationsCard.

- The justification text, when present, is plain text with no formatting. It could use bullet points or structured sections for readability.

---

## 4. Concept Breakdown (Concept Bottleneck Layer)

### Current State

Displays per-axis decomposition into micro-concepts scored 0-1, with a bottleneck concept highlighted. The bottleneck shows: current value, target (0.80), and projected score lift. Only appears after a full (non-quick) diagnostic.

### What's Missing

- If the CBM was skipped (quick diagnostic), the entire section is hidden with no explanation. A note like "Run a full diagnostic to see the concept breakdown" would help.

- The labels for concepts come from the API but some use raw ID strings with underscores instead of human-readable names when the `labels` mapping is incomplete.

- There's no action button to "Improve this concept" that could link to a relevant recommendation or roadmap action.

---

## 5. HUD — Chat Panel

### Current State

A chat panel in the HUD view lets users type or use voice (STT via Whisper, TTS via Piper/Kokoro) to converse with Moufida. Messages appear as chat bubbles. The PixelMoufida character shows listening/thinking/speaking states. Voice control can be triggered via Ctrl+Shift+V or a microphone button.

### What's Missing

- Messages are stored only in memory. Navigating away from the HUD view or refreshing the page clears the entire conversation. There is no database table for chat history.

- The LLM endpoint receives each message independently with no conversation history. The chat has no memory of previous turns within a session.

- LLM replies may contain markdown (bold, lists, code) but are rendered as plain text.

- If the LLM cites a source or references evidence, there is no EvidenceTrace component in the chat (unlike the Pitch Simulator which shows traces for every investor question).

- There are no suggested follow-up questions shown after each reply, a common UX pattern in conversational interfaces.

- Voice chat has no way to interrupt or cancel once triggered. The user must wait for speech recognition and response to complete.

---

## 6. Review Card (HUD)

### Current State

Displays review notifications when an axis re-analysis is ready. Shows the output and approve/edit/retry buttons.

### What's Missing

- The output is rendered with `JSON.stringify()` inside a `<pre>` block. Raw JSON is visible to the user. This should render as structured human-readable content like the creation flow does.

- There is no visual indicator on the sidebar showing that a review is pending (e.g., a badge count on the HUD nav item).

---

## 7. Alert Feed

### Current State

Shows SSE-pushed alerts with severity colors (critical/warning/info), title, body, timestamp, and dismiss button.

### What's Missing

- Multiple similar alerts are not grouped or collapsed. If the same event fires repeatedly, the list grows unbounded.

- Critical alerts have no sound or desktop notification. In a desktop app, a critical blocker being detected should trigger some form of interruption.

- There's no "mark all read" action.

---

## 8. Mon Parcours — History and Growth

### Current State

Contains a ScoreChart (Recharts line chart of score history), a list of completed actions, and a list of past diagnostic history entries.

### What's Missing

- The compare feature has no UI. `compareHistory()` API exists, 4 locale keys exist (`compare_title`, `compare_score_deltas`, `compare_resolved`, `compare_new`), but there is no "Compare two diagnostics" button. Users cannot see side-by-side progress.

- No delta badges appear next to current scores compared to the previous diagnostic. Users must look at the chart to infer change.

- No blocker evolution summary exists. "Previously you had 3 critical blockers. Now you have 1" would be encouraging.

- No score projection or trend line shows where the startup is heading at the current rate.

- There is no way to export the chart as an image or share progress with a co-founder or mentor.

---

## 9. Companion Window (Desktop Pet)

### Current State

A separate Tauri window that roams the bottom-right edge of the screen. Canvas-rendered pixel character walks left and right, blinks, waves when idle. Clicking shows the main window. Double-clicking shows the main window and triggers a quick diagnostic.

### What's Missing

- The desktop companion doesn't react to daemon events or app state. The in-app SVG companion shows an alert state when critical alerts arrive, but the desktop pet keeps walking regardless.

- There is no idle animation variety beyond walk/blink/wave. The character doesn't sit, stretch, play with items, or otherwise express personality.

- The roaming zone is fixed at 200px from the right edge. Users cannot reposition the companion or pin it to a different screen location.

- There is no onboarding or introduction. New users see a pixel character roaming the screen with no explanation of who she is or what she does.

- No customization is available. Users cannot change Moufida's appearance from the companion window.

---

## 10. Character System — Moufida

### Current State

Two rendering modes exist:

- **SVG character** (`MoufidaCharacter.tsx`): 14 states (idle, listening, thinking, processing,
  speaking, alert, celebrating, sleeping, skeptic, presenting, pointing_left, worried, surprised,
  reading), each backed by a real CSS keyframe animation in `styles.ts`, plus eye-blink groups,
  mouth-sync, a think bubble, sleep ZZZs, celebrate sparkles, and two costume overlays (skeptic
  briefcase, presenting pointer). This is the genuinely expressive asset. **It is used only on
  dashboard cards, personas, pitch, and scenario.**
- **Pixel canvas character** (`PixelMoufida.tsx` + `pixelArt/moufida.ts`): used on landing,
  intake, creation flow, chat header, and the desktop companion — i.e. the entire first-run
  journey.

**Code-verified correction (important):** the pixel character is far less stateful than
previously documented. `drawChar()` only produces distinct visuals for **four** states —
`thinking`, `listening`, `sleeping`, `startled` — and those are small *bubble/symbol overlays*,
not pose changes. There is a 2-frame walk-leg toggle, a periodic blink, and an idle wave arm.
The body sprite (`BODY`) is otherwise **static**: `speaking`, `alert`, `celebrating`,
`processing`, `walk`, and `idle` render the same body with no animation. So the most-seen
character on the most important screens barely emotes. The palette `P` is a single hardcoded
object, so there is no theming hook at all on the pixel side.

The net effect: **the rich character is hidden on secondary surfaces while the static one
fronts the whole journey.**

**Locked direction (see Part I §D decision):** the app standardizes on the **pixel** character
everywhere and **retires the SVG** (the "old design"). The fix is therefore to (1) swap all SVG
render sites to `PixelMoufida`, and (2) port the SVG's 14 states into the pixel renderer and
improve it so expressiveness is gained, not lost — full per-state spec in §D5.

### What's Missing

- There is only one color theme. The character always uses the warm autumn palette (orange dress, brown hair). There are no alternate costumes, dress colors, or themes tied to different pages.

- The pixel and SVG versions have inconsistent state support. The pixel version lacks: skeptic, presenting, pointing_left, worried, surprised, reading.

- No per-page theme system exists. The character could wear different colors or accessories depending on the current view (e.g., professional blue for pitch, warm orange for personas, green for parcours, purple for scenarios).

- No progressive celebration animations exist for milestones (first axis approved, diagnostic complete, score improvement). Currently only the SVG has a "celebrating" state but it's used sparingly.

- The character doesn't show encouragement if the user hasn't interacted for a while.

---

## 11. Dashboard — Overall Layout

### Current State

The dashboard is a vertically scrolling page containing: MaturityCard, ScoreGauge, ConceptBreakdown, BlockerList, RecommendationsCard, WhatsNew, OpportunityRadar, CompetitorBoard, PersonaGallery, PitchSimulator, RoadmapTimeline, EventFeed. Personas and Pitch are embedded as cards taking up significant vertical space with inline chat/session overlays.

### What's Missing

- PersonaGallery and PitchSimulator should not be dashboard cards. They are deep interactive features that deserve dedicated pages. The dashboard should be focused on at-a-glance health: maturity, scores, blockers, recommendations, roadmap.

- There is no document upload button. Despite a complete backend endpoint, users cannot upload their business plan, market study, or financial model to enrich analysis.

- There is no score debate button. Despite complete backend, users cannot challenge scores they disagree with.

- The diagnostic compare button is missing from the dashboard header. Users should be able to compare the current scores with the previous diagnostic from the dashboard directly.

- No SSE connection status indicator shows whether real-time updates are active.

---

## 12. Tool Integrations — Settings Page

### Current State

Tools are grouped by domain (communication, documentation, finance, marketing, development). Each tool card shows: icon, label, domain, direction badge, status dot, enable/disable toggle, and expandable config form with test/save/sync buttons. Composio-managed tools use OAuth with polling for connection status.

### What's Missing

- There is no plain-language explanation of what each tool does when connected. The label "Slack" doesn't explain "When connected, Moufida can detect team communication patterns relevant to your startup's operations."

- No tool signal history exists. When a tool syncs and triggers an axis re-analysis, there is no log of what data was pulled or which axes were re-evaluated.

- Sync progress shows only text "Syncing..." with no progress bar or time estimate.

- For Composio tools, showing the webhook URL for manual setup would help with debugging connection issues.

- No privacy detail per tool explains exactly what data each integration sends or receives.

- The `getToolState()` API exists but is never used. No component drills into a single tool by slug.

---

## 13. SSE / Real-Time Events

### Current State

An EventSource consumer handles 12 event types and dispatches them to Zustand store actions. Events include: score_update, alert, roadmap_update, review_ready, maturity_update, event_new, kb_updated, horizon_complete, daemon_status, competitor_update, opportunity_new, concept_update, watch_targets_updated.

### What's Missing

- No connection status indicator. The user doesn't know if the real-time connection to the backend is alive or dead.

- No reconnection notification. If the SSE connection drops and reconnects, there is no toast or visual cue.

- No event rate limiting. Rapid fire events (e.g., batch competitor updates during initial sync) could cause excessive re-renders.

- The `review_ready` event fires review notifications but there's no badge count on the HUD sidebar nav item to indicate pending reviews.

---

## 14. Event Feed

### Current State

Chronological filterable event list with status filters (all/new/acted/ignored) and source icon filters (manual/chat/tool/daemon). Each event card shows: source icon, summary, axes affected, severity, timestamp, suggestion, expandable diff, and action buttons (Act/Manual/Ignore).

### What's Missing

- The `getEventDiff()` API function exists but is never called. The diff is read directly from the event list response, which may not contain the full detailed diff.

- There is no bulk action support. Users cannot select multiple events and Act on all of them at once.

- Events are not grouped by source or type. A burst of similar events from the daemon appears as separate cards.

- No "mark as read" visual state exists beyond the status-based resolved/unresolved opacity. Events that have been viewed but not acted on look the same as unviewed ones.

---

## 15. Intake Wizard

### Current State

Adaptive branching questionnaire with stateless client-side answer accumulation. Shows one question at a time with progress bar, PixelMoufida character, and input types: choice grid, boolean buttons, text/number inputs.

### What's Missing

- There is no back button. Users cannot go back to change a previous answer once they've moved to the next question.

- No answer review screen exists. After all questions, the wizard immediately patches the profile and proceeds. Users should see a "Review your answers" step before finalizing.

- Individual questions cannot be skipped. The only skip option bypasses the entire remaining questionnaire.

- The progress bar says "Question 3" but not "3 of ~9" (estimated total is hardcoded). The actual question count varies by branch.

- The character doesn't react to answers. Moufida could acknowledge the user's sector or stage with a brief contextual response.

---

## 16. Scenario Planner

### Current State

Slide-in modal panel from the dashboard. Users create up to 3 scenarios with key/value parameter overrides, project their effect on all 9 axes with confidence and reasoning, compare side-by-side in a table, and adopt one scenario (patches profile + re-runs diagnostic).

### What's Missing

- The scenario planner is hidden behind a small "What-if" button in the dashboard toolbar. Many users will never discover it. It should be a dedicated page or at minimum a sidebar entry.

- There is no way to view a list of previously saved scenarios. Each session starts fresh. The backend has `GET /scenarios` but no API wrapper or UI exists.

- Saved scenarios cannot be compared against each other historically. Only the current session's projections are shown.

- The character shows presenting/idle poses but doesn't react to the projected delta or help the user interpret the results.

---

## 17. Features With No UI At All

These features exist in the backend, database, or API layer but have zero frontend representation:

- **Score Debate**: `POST /axis/{axis}/debate` endpoint and `debateAxis()` API function exist. 6 locale keys exist. Zero UI. An entrepreneur cannot argue with Moufida about a score they disagree with.

- **Document Upload**: `POST /documents` endpoint and `uploadDocument()` API function exist. PDF text extraction via PyPDF is implemented in the backend. Zero UI. Users cannot upload their business plan, pitch deck, or market study.

- **Diagnostic Compare**: `GET /history/compare` endpoint and `compareHistory()` API function exist. 4 locale keys and a `CompareResult` TypeScript type exist. Zero UI. Users cannot see side-by-side progress between two diagnostic runs.

- **Knowledge Base Entry Management**: `POST /kb` endpoint and `addKbEntry()` API function exist. Zero UI. Users cannot add their own knowledge sources or see what Moufida already knows. The 65+ existing KB resources are invisible.

- **Event Diff Detail**: `GET /event/{id}/diff` endpoint and `getEventDiff()` API function exist but are never called. The EventFeed reads diff from the list response instead.

- **Watch Targets Management**: `GET /watch-targets` and `POST /watch-targets/refresh` endpoints exist. A `project_watch_targets` database table exists. No API wrapper and no UI. Users cannot see or manage what the daemon is watching for them.

- **Telemetry in Desktop App**: `api_requests`, `llm_calls`, `daemon_activities` database tables exist (migration 020). These are exposed only in the separate Admin SPA. The desktop app has no visibility into LLM usage, API health, or daemon activity.

---

## 18. Features in Wrong Places

These features work but are located where they don't belong:

- **Customer Personas** (PersonaGallery, PersonaChat, CloseStrategyCard): Embedded as a dashboard card with inline chat. Persona simulation is a deep interactive feature requiring focus. It should be a dedicated page with its own sidebar link and full-screen chat experience.

- **Investor Pitch Simulator** (PitchSimulator, PitchReadinessReport): Embedded as a dashboard card with a full-screen overlay. Investor preparation is a high-stakes activity deserving a dedicated page with session history, profile persistence, and side-by-side readiness comparison.

- **Scenario Planner** (ScenarioPlannerPanel): Hidden behind a small text button in the dashboard toolbar. It's a sophisticated what-if analysis tool that most users will never discover. It should be a dedicated page or at least a sidebar entry.

---

## 19. Navigation Restructure Summary

The sidebar currently shows: Dashboard, HUD, Mon Parcours, Settings.

It should show:
- Dashboard (diagnostic hub with maturity, scores, blockers, roadmap, competitors, opportunities, events)
- Assistant (HUD: chat, alerts, reviews)
- Mon Parcours (history, chart, comparison)
- Personas Client (dedicated customer persona page)
- Pitch Investisseur (dedicated investor pitch page)
- Scénarios (dedicated what-if analysis, replacing the hidden modal)
- Intégrations (existing settings/tools page)
- Base de Connaissances (new: browse what Moufida knows)

---

## 20. Character Theme Per Page

The character currently uses one warm-autumn color scheme everywhere. It should adapt per page:

- Landing: Default warm autumn, pixel art, name badge
- Dashboard: Sector-based accent color, floating companion in watching/idle state
- Personas Client: Warm orange theme, pointing_left pose, thought bubble
- Pitch Investisseur: Cool blue/professional theme, skeptic pose, briefcase accessory
- Scénarios: Purple theme, thinking pose, glasses/pointer accessory
- Mon Parcours: Green theme, reading pose, scroll/book accessory
- Settings/Integrations: Neutral gray, idle pose, tool icons

---

## 21. Character State Inconsistencies

The SVG character (`MoufidaCharacter.tsx`) supports 14 fully-animated states: idle, listening, thinking, processing, speaking, alert, celebrating, sleeping, skeptic, presenting, pointing_left, worried, surprised, reading.

The pixel character (`PixelMoufida.tsx`) *accepts* a `state` string but, per the code, only
renders distinct visuals for **4** of them — and only as small overlays, not poses:
`thinking` (thought bubble), `listening` (♫), `sleeping` (ZZZ), `startled` (!). Everything else
(`idle`, `walk`, `speaking`, `alert`, `celebrating`, `processing`) falls through to the same
**static body** plus the shared walk-leg toggle / blink / idle-wave. So the practical gap is not
"8 vs 14 states" — it's that the pixel character has **no pose/emotion system at all**, just a
static sprite with a few decorative bubbles.

Missing from the pixel version vs. SVG: every real emotional pose — skeptic, presenting,
pointing_left, worried, surprised, reading, processing, plus any visible difference for speaking,
alert, and celebrating.

The desktop companion (`companion.ts`) shares `pixelArt/moufida.ts` drawing functions and is
even more limited, and (per §9) does not react to daemon/app events at all.

**Locked direction (see Part I §D decision):** standardize on the **pixel** character everywhere
and retire the SVG. Instead of reaching parity by keeping both, the SVG's full state set is
**ported into the pixel renderer** (real pose tables + overlays + accessories) and improved
beyond it (per-page palettes, idle variety, smoother animation). Full per-state port spec in
§D5. The 5 SVG render sites to convert are listed in the §D decision table.

---

## 22. Dashboard Card Detail Gaps

### MaturityCard
- Shows stage badge, confidence percentage, evidence bullets, perception gap warning.
- Missing: stage progression visualization showing what's required to advance to the next stage, confidence explanation.

### BlockerList
- Shows blockers sorted by severity with axis labels.
- Missing: "link to roadmap" action per blocker, resolution suggestion.

### RecommendationsCard
- Shows priority-highlighted actions with score name.
- Missing: dismiss action per recommendation, link to sub-dimension in ScoreGauge.

### RoadmapTimeline
- Shows 3-horizon columns, checkboxes, advance/regenerate buttons, celebration banner, stale warning, score-delta warning, provenance panel.
- Missing: drag reorder, estimated effort per action, assignee, dependency visualization between actions.

### CompetitorBoard
- Shows comparison table with positioning/pricing/funding, SWOT cards per competitor.
- Missing: user's own pricing row (shows "—"), snapshot history, manual competitor add, "report competitor" button.

### OpportunityRadar
- Shows funding/grant cards sorted by deadline, urgency coloring, match score, dismiss.
- Missing: calendar view, "mark as applied" action, applied filter, notification toast on new opportunities.

### WhatsNew
- Shows LLM digest summary, events list, refresh button.
- Missing: auto-refresh on SSE event_new, mark-as-read for summary events.

### EventFeed
- Shows filterable event list, action buttons, expandable diff, suggestion display.
- Missing: getEventDiff API usage, bulk actions, event grouping, viewed/unviewed state.

---

## 23. Knowledge Base — Resources and Taxonomy

### Current State

65+ hand-crafted resource JSON files exist in `backend/rag/knowledge-base/resources/`. Each contains a full article body in French with metadata (title, summary, type, stage, sector, source, URL). A `taxonomy.json` defines a coverage grid: 6 startup stages (idea, validation, launch, growth, maturity, pivot) × 5 resource types (methodology, regulation, funding, case_study, best_practice) × 4 sectors (general, tech, green, manufacturing). The `generate_kb.py` script creates these resources with hardcoded bodies.

### What's Missing

- No web scraping pipeline exists. All 65+ resources were hand-written. There is no script that crawls the URLs listed in the resources to extract and validate content. The URLs embedded in resource files may be dead or incorrect.

- No URL validation or health checking is performed. Resources reference URLs that could be 404, domain-squatted, or expired.

- The taxonomy target is 80-100 resources to reach minimum viable coverage. Currently at ~65, the remaining gap has no clear path to close programmatically.

- There is no UI to browse the knowledge base. A sidebar entry "Base de Connaissances" could show the taxonomy coverage, let users filter by stage/type/sector, and view individual resource content inline.

- There is no way for users to add their own knowledge entries, despite a complete backend endpoint and API function.

- No confidence or freshness indicator exists per resource. Users don't know whether a resource was created by Moufida's team, web-scraped last week, or is auto-generated.

---

## 24. Web Search — SearXNG Integration

### Current State

A self-hosted SearXNG instance runs at `http://searxng:8080`. The `websearch.py` module sends POST requests with a 12-second timeout. Results are cached in-process for 15 minutes. On failure (timeout, connection error, empty response), the module returns an empty list best-effort — no error is raised.

### What's Missing

- No health-check endpoint or health indicator. If SearXNG goes down, web search silently returns empty results. Users and the daemon have no way to know.

- The 12-second timeout is aggressive. Many SearXNG instances with multiple search backends take 15-20 seconds to return results during peak load. Timeouts cause silent empty results.

- No fallback search provider exists. If SearXNG is unreachable, there is no graceful degradation to another search API (even a public one).

- There is no UI to see search queries or results. Users cannot verify what web sources Moufida consulted during creation or diagnostic.

- The in-process cache means each backend process maintains its own cache. With multiple workers (common in production), cache hit rates drop significantly.

- No rate limiting or queue exists. If multiple axes request web searches simultaneously, SearXNG gets unbounded concurrent requests.

---

## 25. Evidence Assembly — RAG + Web Results

### Current State

The `evidence.py` module in the orchestrator assembles per-axis evidence before LLM call during creation mode. Each axis has a mapping (`AXIS_EVIDENCE`) specifying which KB collection and web search topic to query. Results are formatted as a text block prepended to the LLM prompt as context.

### What's Missing

- The evidence text is raw interpolated content. It has no structure — source attribution, confidence, or relevance score. The LLM sees a blob of text from KB + web and must figure out attribution on its own.

- No citation metadata survives through to the LLM output. The LLM receives evidence with source URLs but the generated proposal may not cite them properly. The frontend cannot display inline citations because the LLM output doesn't reference them.

- Evidence is fetched synchronously before each axis call. For axes that could run faster, the evidence assembly time adds a fixed overhead (often 2-5 seconds per axis).

- There is no evidence quality check. If the KB returns no documents and web search times out, the evidence block is empty. The LLM receives no context and may hallucinate.

- No user-facing evidence view exists. Users cannot see what documents and web pages Moufida consulted before generating each axis proposal.

---

## 26. Storage and Persistence Gaps

### Database

- The `chat_messages` table exists in migration 020 but is never populated by the frontend or the orchestrator. Chat messages live only in `zustand` memory and disappear on page refresh.
- The `scenarios` table stores scenarios but the frontend only uses in-memory scenarios. No UI lists, loads, or manages saved scenarios.
- Migration 020 adds `api_requests`, `llm_calls`, `daemon_activities` tables intended for telemetry. These are collected only in the admin SPA, not in the desktop app.
- The `project_watch_targets` table exists and the backend serves endpoints to read and refresh watch targets. No frontend UI exists.

### Frontend State

- The Zustand store resets to initial state on page refresh (with `persist` middleware on some keys). Diagnostic results are re-fetched from the API on mount, but HUD chat messages, scenario drafts, and intake wizard answers are lost.
- SSE connection state is not persisted and not exposed to the user.
- Auth tokens are stored in localStorage with no refresh mechanism.

---

## 27. Localization Gaps

28 locale keys exist in `fr.json` (and presumably `en.json`, `ar.json`) that are never referenced by any component:

- `debate_title`, `debate_success`, `debate_error`, `debate_placeholder`, `debate_submit`, `debate_closed` — for the score debate feature
- `compare_title`, `compare_score_deltas`, `compare_resolved`, `compare_new` — for the diagnostic compare feature
- `daemon_focused`, `daemon_idle` — for daemon status display
- `competitor_change`, `competitor_new`, `competitor_dropped` — for competitor monitoring alerts
- Various others related to tools, events, and settings that appear unused

These keys are properly translated but unreachable from any component tree.

---

## 28. Error Handling and Empty States

- Many dashboard cards don't handle the loading/fetching state. They show previous data or nothing while a re-fetch is in progress.
- No cards show an explicit empty state with a CTA. If a startup has no recommendations yet, the RecommendationsCard shows nothing or a blank area.
- SSE connection errors are silent. If the backend goes down, the user sees stale data with no indicator of connection loss.
- API error toasts use a generic format with the raw error message. Server errors in French or English show technical details not useful to an entrepreneur.
- The diagnostic runner never raises on axis failure — failed axes return `null`. The frontend silently hides failed axes from the dashboard, leaving users unaware that an axis was skipped.

---

## 29. Accessibility and UX Concerns

- The sidebar navigation has no active-state indicator beyond text color. Users don't visually know which page they're on without looking at the header title.
- All dashboard cards use hover-based expand/collapse. On the desktop app row-by-row card layout, this may feel inconsistent — some cards expand, others open overlays or modals.
- Score gauges use color alone to convey tier status (green/yellow/amber/red). No text label like "Healthy" or "Warning" is shown for colorblind users.
- The HUD chat input has no placeholder text hinting at what users can ask.
- There is no keyboard shortcut reference or help menu.
- The landing page introduces Moufida but contains no "Try it" or "Start without signing up" option beyond the main CTA.
