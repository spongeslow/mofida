# Moufida — Desktop App User Manual

This manual walks through **every screen and control** of the Moufida desktop app,
and — for each one — explains *what happens in the background* in plain language.
It also explains the **2D character** (the little companion) and how it is wired
to the always-on **Go daemon**.

> New here? See the [README](README.md) for installation and how to start the
> backend + app. In short: `docker compose up --build` (backend), then
> `cd frontend && npm run tauri dev` (the desktop app). The app talks to the
> orchestrator at `localhost:8001` over HTTP and a live **SSE** event stream.

---

## 0. The big picture (read this first)

Moufida has **two windows**, **one background brain**, and **one optional admin
panel**:

- **The main window** — the dashboard/chat/settings app you interact with.
- **The companion window** — a small, frameless 2D character ("Moufida") that
  roams along the bottom of your screen. It is the *face* of the system.
- **The Go daemon** — a 24/7 background process (inside Docker) that keeps
  watching the world for your project even when the app is closed.
- **The admin / observability panel** — a separate, read-only web page
  (`localhost:3002`) for watching the system's internals live (see §16).

Everything you see in the UI is backed by the **orchestrator** (a FastAPI
service). When something changes in the background, the orchestrator pushes a
live **event** down an SSE stream and the UI updates itself without a refresh.

Three ideas recur throughout this manual:

- **Project** — one startup. You can have many; one is "open" in the app, and
  (separately) one is "focused" by the daemon.
- **Event** — an interpreted change from any of four sources (you, chat, a
  connected tool, or the daemon). Events appear in the **Event Feed** with a
  diff and an Apply / Handle / Ignore choice.
- **Axis** — one of the nine analysis areas (ideation, market, product, brand,
  business-model, legal, operations, marketing, sales). Scores and plan sections
  are produced per axis; when one changes, only the *dependent* axes re-run.

---

## 1. The landing page

When no project is open, you see the hero screen: the **2D character**, the
"Moufida" title, a tagline, and two main actions.

### Button 1 — "Got an idea?" (creation mode)

- **What you see:** clicking it reveals a text box asking you to describe your
  idea. Type it, then press **Build →** (or `Ctrl/Cmd + Enter`).
- **What happens in the background:**
  - A new project is created (`POST /api/v1/project/new`) in **creation state**.
  - Your raw idea is saved into the project profile
    (`PATCH /api/v1/project/{id}/profile` with `{ raw_idea }`).
  - The app switches to the **Creation flow** (see §4).

### Button 2 — "📁 Mes Projets" (the secondary button)

- **What you see:** it opens the **Projects** page (your portfolio).
- **What happens in the background:** the app fetches your project list
  (`GET /api/v1/projects`) and your daemon's current focus
  (`GET /api/v1/daemon/control`) so it can mark which project is being watched.
- This same page is now reachable **any time** from the sidebar (📁 Mes Projets),
  not only from the landing screen — so you can switch projects without leaving.

### Bottom hint

- A line reminding you that you can summon Moufida by voice ("Hey Moufida").
  This is handled by the local wake-word listener (no audio leaves your machine).

---

## 2. The Projects page (your portfolio)

A list of your projects with explicit actions, reachable from the sidebar (📁
**Mes Projets**) at any time — or from the landing screen before any project is open.

- **Open** — the project becomes the open project and you go **straight to its
  Dashboard** (no forced questionnaire). Switching to a different project here
  re-points the whole app — scores, live SSE stream, and the companion all
  re-bind — with **no page refresh**.
- **⚡ Diagnose** — opens the project *and* immediately runs a fresh full
  diagnostic.
- **✎ Update profile** — the only place that now routes you through the
  **adaptive intake** (§3, *update* mode) before returning to the Dashboard.
- **＋ New project** — returns to the landing "Got an idea?" entry to start fresh.
- **Mode & stage badges:** each card shows whether the project is in *creation*
  or *diagnosis* mode and its latest maturity stage (if any).
- **👁 Focus button — this is how you point the daemon at a project:**
  - Clicking it calls `POST /api/v1/daemon/control { focus_project_id }`.
  - The background daemon then **hot-swaps** its watchers onto that project
    (no restart) and starts monitoring competitors, funding deadlines, legal
    changes, trends, etc. *for that specific project*.
  - Click again to **unfocus** (the daemon parks itself). The currently-watched
    project is highlighted with a filled icon/badge.
  - This replaces the old "set a project ID in a config file" approach entirely.
- **📂 Import project:** load a project from a JSON file. The app creates a
  project and merges the file's profile into it.
- **🗑 Delete:** permanently removes the project (`DELETE /api/v1/project/{id}`),
  cascading its plan sections, events, scores, and history. You're asked to
  confirm first.

---

## 3. The adaptive intake (questionnaire)

Reached via **✎ Update profile** on the Projects page (and at the start of
creation when needed). Opening a project no longer forces this — it's an explicit
choice when you want to refresh the project's context.

- **What you see:** one question at a time — multiple-choice, yes/no, number, or
  free text — that **adapts** based on your previous answers and sector.
- **What happens in the background:**
  - The questionnaire is **stateless on the server**: the app sends the full
    answers map each step (`POST /api/v1/intake/answer`) and gets the next
    question or a completion signal back.
  - On completion, the collected answers are merged into your project profile.
  - You're then taken to the **Dashboard** (existing project) or the **Creation
    flow** (new idea).

---

## 4. The Creation flow (build a plan from an idea)

A guided, **nine-step** generator. A stepper at the top shows progress through
the axes: ideation → market → product → brand → business-model → legal →
operations → marketing → sales.

For each axis you get a generated **proposal** and three choices:

- **Approve** — accept the section.
  - Background: `POST /api/v1/project/{id}/generate/{axis}/approve` persists the
    section, then the next axis is generated automatically.
- **Edit with constraints** — type guidance and regenerate.
  - Background: re-calls `generate` with your constraints so the new draft
    respects them.
- **Retry** — regenerate the same axis from scratch.

Before each axis, **Moufida narrates** (in a speech bubble) what that axis checks
and why it matters, so the plan reads like a guided conversation rather than a
silent form. Every proposal is **grounded**: the generator pulls evidence from
the local knowledge base (per-axis RAG collections) plus free live web search,
and shows **citations** for what it used (referenced inline as `[n]` where the
text cites a source).

If you close the app mid-plan, the flow **resumes where you left off** on reopen
(approved sections persist server-side; your position is restored locally). When
the ninth axis is approved, Moufida **celebrates** on the completion screen.

- **Finishing:** after the ninth axis is approved, the app calls
  `POST /api/v1/project/{id}/finalize`, which assembles a **roadmap** from real
  Tunisian support programmes. You land on a completion screen with the full
  **plan document** and a **PDF export**.

---

## 5. The main layout: sidebar + content

Once a project is open, the window is a left **sidebar** + a main **content area**.

### Sidebar (top → bottom)

- **Navigation** (hidden during intake/creation): **Mes Projets**, **Dashboard**,
  **Chat (HUD)**, **Personas**, **Pitch**, **Scénarios**, **Base de Connaissances**,
  **History (Mon Parcours)**, **Settings**. (Personas / Pitch / Scénarios are now
  dedicated pages — see §15 — not dashboard cards.)
- **Daemon status control** *(this is the character switch — see §9):*
  - A colored dot + label: **Watching** (green), **Paused** (amber), or
    **Offline** (grey, no heartbeat in ~90s).
  - A **⏸ / ▶ button** to pause or resume the daemon's work.
  - It's **disabled until you've focused a project** (the 👁 button in §2),
    because there's nothing to watch otherwise.
  - Background: pressing it calls `POST /api/v1/daemon/control { paused }`; the
    daemon picks the flag up on its next heartbeat and stops/starts doing work.
- **Voice state indicator:** shows *Listening / Speaking / …* when voice is active.
- **Real-time indicator:** a small dot + label (*Temps réel actif* / *Hors ligne*)
  showing whether the live SSE connection to the backend is up.
- **Language selector:** FR / EN / AR (Arabic flips the whole UI to right-to-left).

### Keyboard shortcuts (global)

- `Ctrl/Cmd + Shift + M` — show/hide the main window.
- `Ctrl/Cmd + Shift + D` — run a diagnostic.
- `Ctrl/Cmd + Shift + V` — start voice.

---

## 6. The Dashboard

The home screen for an open project. It auto-runs a diagnostic the first time if
none exists yet.

- **Run diagnostic / Quick diagnostic buttons:**
  - Background: `POST /api/v1/project/{id}/run-diagnostic` fans the profile out
    across the nine axes in three dependency-ordered waves, computes the five
    composite scores, detects anomalies, and **streams results live** over SSE as
    each wave finishes. "Quick" is a lighter pass.
- **📎 Upload document button** *(dashboard header):* attach a PDF or text/
  markdown file (business plan, market study…). Its text is extracted and added
  to the project knowledge base (`POST /documents`) to enrich analysis.
- **Maturity card:** your stage (Ideation → … → Growth) shown on a **stage
  "level" ladder** (with the next stage to reach), plus evidence and the gap
  between self-assessed and computed stage.
- **Score gauges:** the five composite scores (Market, Commercial Offer,
  Innovation, Scalability, Green). The number **animates (counts up)** on update;
  each gauge expands to its sub-dimensions, weights, evidence tiers, and a
  plain-language justification — and has a **💬 Débattre du score** button that
  opens an inline chat to argue the score (`POST /axis/{axis}/debate`); if your
  case lands, the score updates live.
- **Concept breakdown** *(interpretability — see §15):* below the gauges, each of
  the nine axes can be expanded to show its score broken into named
  micro-concepts (e.g. *market* → TAM evidence, ICP specificity, WTP signal…).
  Moufida marks the **bottleneck** — the single concept holding the axis back —
  and tells you the projected score if you fixed it. A "calibrated / prior" chip
  shows whether the weights were learned from your own history yet.
- **"What If?" button** *(top of the dashboard):* opens the **Scénarios** page
  (the Scenario Planner — see §15).
- **Blockers:** ranked critical / warning / info issues.
- **Recommendations:** prioritized actions tied to the weakest sub-dimensions.
- **"What's new?":** a one-paragraph LLM digest of recent activity
  (`GET /api/v1/project/{id}/whats-new`). This is where daemon and tool activity
  gets summarized for you.
- **Opportunity Radar** *(fed by the daemon — see §10):* funding/grant cards
  sorted by deadline, colored red when an apply-by date is within 14 days, each
  with a match score, an **Apply** link, and a **Dismiss** button.
- **Competitor Board** *(fed by the daemon — see §10):* a "You vs each
  competitor" table (positioning, pricing, funding) plus a SWOT card per
  competitor. It refreshes itself whenever the daemon reports a competitor change.
- *(Customer Personas and the Pitch Simulator are no longer dashboard cards —
  they're now their own sidebar pages, **Personas** and **Pitch**. See §15.)*
- **Roadmap timeline:** three horizons (immediate / short-term / medium-term).
  Checking off all actions in the active horizon generates the next one. A
  **stale** banner appears when underlying data changed; you can **Regenerate**
  and inspect **provenance** (which KB version and trigger produced it).
- **Event Feed:** the running log of changes (see §8).

Every claim in the four analytical features above (concept bottleneck, scenario
reasoning, persona replies, investor questions) ships with an **Evidence trace** —
a small expandable "Sources" line showing exactly which axis field, KB document,
competitor snapshot, or signal it came from. Nothing is an unverifiable guess.

---

## 7. The Chat (HUD)

Reached via **Chat** in the sidebar.

- **Review card:** surfaces any axis proposals waiting for your review.
- **Chat panel:** a **grounded** assistant — it answers from *your* diagnostic
  results and scores, not generic advice.
  - **Update intent detection:** if you state a change ("we pivoted to B2B", "we
    hired a CTO"), Moufida recognizes it, logs an **event**, and proposes which
    axes to re-run — instead of just chatting. You stay in control via the Event
    Feed.
  - Voice in/out is available here (speech-to-text and text-to-speech run
    locally). Chat history is **persisted per project** (survives navigation/refresh).
- **Alert feed:** live alerts pushed from the background.
- **👁 Watch targets:** what the daemon monitors for this project (news feeds,
  legal sources, keywords, competitors), with a **Refresh** button
  (`GET`/`POST /project/{id}/watch-targets`).
- **📚 Add knowledge:** paste a note or link for Moufida to learn (`POST /kb`);
  it enriches RAG and bumps the project's knowledge-base version.

---

## 8. The Event Feed & the four update sources

Moufida treats every change as an **event** so nothing happens silently.

Events come from **four sources**, each shown with an icon:

- **✎ Manual** — you edited a plan section in the UI.
- **💬 Chat** — you described a change in conversation.
- **📡 Tool** — a connected integration (Notion/Slack/Sheets/GitHub/Analytics)
  reported a change.
- **🛰️ Daemon** — the background watcher detected a market/legal/trend/competitor
  signal.

For each event card you can:

- **⚡ Apply** — accept and auto-re-run the affected downstream axes as proposals.
- **✎ Handle myself** — mark it; you'll deal with it manually.
- **✕ Ignore** — dismiss it.

Every card carries a **field-level diff** (what changed, before → after). Under
the hood, a **dependency engine** computes the *transitive* set of axes to re-run
from whatever changed — so a change to "business-model" correctly cascades to
operations, legal, marketing, sales, and the roadmap, but nothing unrelated.

You can filter the feed by **status** (new/acted/ignored) and **source**.

---

## 9. The 2D character and how it relates to the Go daemon

This is the part that ties the visible app to the invisible background work.

### What the character is

- **One character, everywhere — the pixel-art Moufida.** There is a single
  renderer now (the older SVG character was retired), so she looks consistent on
  the landing screen, in the creation flow, on every page, and as the desktop pet.
- A small, frameless **desktop companion window** with the pixel character that
  walks/roams along the bottom of your screen — the always-visible "face" of Moufida.
- An **in-app floating companion** also appears bottom-right of the main window
  on every page, reacting to what's happening (see below).
- You can **show/hide** the companion from **Settings → Preferences** (the toggle
  also gates the in-app companion and its sound cues).

### What the character does

- **Click it** → brings the main window to the front.
- **Double-click it** → runs a quick diagnostic on the open project.
- It has a **full expression system**: idle/walk, *listening / thinking /
  speaking* during voice, plus **celebrating** (with confetti), **alert**,
  **worried** (sweat drop), **surprised**, **sleeping** (z z z), and role poses
  **skeptic** (briefcase), **presenting** (pointer) and **pointing/reading**
  (book) — each with mouth, arm and accessory changes.
- It is **reactive**: a running diagnostic makes her *think*; a completed
  diagnostic or unlocked milestone makes her *celebrate*; a score drop or error
  makes her *worried*; a critical alert makes her *alert*; a paused daemon makes
  her *sleep*. Subtle Web-Audio **chimes** accompany celebrate / alert / surprised.
- **Per-page costume:** she changes palette by context — professional **blue** on
  the Pitch page, **purple** on Scénarios, **green** on Mon Parcours.

### How it's wired to the Go daemon (the key relationship)

The character is the **switch and status light for the 24/7 daemon**:

- The daemon continuously sends a **heartbeat** to the orchestrator. The
  orchestrator broadcasts a `daemon_status` event (paused? alive? which project?)
  over SSE to the app.
- The sidebar **daemon status control** (§5) reflects that status and lets you
  **pause/resume** the daemon.
- **When you pause the daemon** (watching off), the orchestrator records it and
  broadcasts the new status → the app tells the companion window to **fall
  asleep** (the character literally sleeps, with "z z z").
- **When the daemon is watching** (alive and not paused), the character is awake
  and roaming.
- So, in plain terms: **an awake, roaming character = Moufida is actively
  watching your focused project in the background. A sleeping character =
  watching is paused.** "Offline" (grey) means the daemon process isn't
  heartbeating at all (e.g. backend not running).

### Which project the daemon watches

- The daemon watches the **focused** project — the one you picked with the **👁
  Focus** button in the project list (§2). This is independent of which project
  is merely "open" in the app.
- Changing focus makes the daemon **hot-swap** its watchers onto the new project
  at runtime (no restart). Before the new watchers start, the orchestrator
  re-derives that project's **watch targets** (see §10) so monitoring is tailored
  to it.

---

## 10. What the daemon actually does in the background

Once a project is focused and watching is on, the daemon runs several
**adaptive watchers**. "Adaptive" means their targets are derived from *your*
project's sector and profile — an agri-food project watches agri-food sources, a
fintech project watches different ones.

- **Competitor watcher** → **Competitor Board.**
  - Detects when a tracked competitor's page changes or they're mentioned in
    sector news. It sends the page text to the orchestrator, which uses the local
    LLM to extract **pricing, positioning, funding**, computes a **diff** vs the
    last snapshot, and regenerates a **SWOT**. The board then refreshes live
    (via a `competitor_update` event).
- **Grant / deadline radar** → **Opportunity Radar.**
  - Scans curated Tunisian/EU funding sources, and for each candidate the
    orchestrator LLM-scores how well it fits your project and extracts the
    **apply-by date**. Good matches appear as cards (via an `opportunity_new`
    event), sorted by deadline.
- **Legal, trend, milestone, budget watchers** → **Event Feed / "What's new?".**
  - Detect regulatory updates, market trend shifts, milestone/budget signals.
    Each is persisted as a **daemon event** so it survives and feeds the digest.
- **Adaptive watch-targets (the "smart" layer).**
  - Each project gets a deterministic, sector-based set of sources as a floor,
    plus an **LLM-derived, cached** set of niche-specific feeds/regulators/
    keywords/competitors. This is recomputed when you focus the project or when
    its profile changes — and cached so it doesn't re-run the LLM every cycle.
- **Knowledge-base staleness checker** (always on, project-independent).
- **Composio poll** (always on) — see §11.

**Pause semantics:** pausing stops the *work*, not the process. Heartbeats keep
flowing, so the UI can tell "paused" apart from "offline", and the character
sleeps rather than disappearing.

---

## 11. Settings & tool integrations

Reached via **Settings** in the sidebar.

### Preferences

- **Show companion** — show/hide the 2D character window.

### Tool integrations

Integrations are grouped by domain. There are **two kinds**, and they can coexist:

**A) Manual-token tools** (Slack, Notion, Google Sheets, GitHub, Google
Analytics):

- Expand the card, paste the required credentials, **Test** the connection,
  **Save**, and (for outgoing tools) **Sync now**.
- These are **one-directional** (Moufida pushes summaries out).

**B) Composio tools** (Notion / Slack / Google Sheets / GitHub, each labeled
"(Composio)") — **no credentials to paste**:

- **Connect button:**
  - Background: `POST /api/v1/tools/{slug}/connect` asks Composio (a managed
    OAuth broker) to start a connection and returns a hosted **OAuth URL**.
  - The app opens that URL in your browser; you authorize there.
  - The app then **polls** `GET /api/v1/tools/{slug}/connection` until the
    connection is active, then shows a **Connected** badge.
- **Connected = bidirectional:**
  - **Outbound:** diagnostic summaries/alerts are pushed out through Composio
    actions.
  - **Inbound:** a change on the other side (e.g. a Notion page edited, a Slack
    message, a new Sheet row) becomes a **trigger** → lands as a `tool_signals`
    record → is routed to the affected axes → appears in the **Event Feed** with
    a diff, exactly like any other update. This is the "a change in Notion flows
    back into Moufida" loop.
- **Disconnect** turns the tool off locally.

**How inbound reaches a desktop behind a router:** a desktop usually can't
receive webhooks. So the Go daemon **polls** the orchestrator every ~5 minutes
(`POST /api/v1/integrations/poll`); the orchestrator pulls any new Composio
trigger events and ingests them. Your Composio API key stays server-side and is
never exposed to the desktop.

### The one local-first exception

Everything in Moufida runs **on your machine** — the LLM, scoring, RAG, voice.
The **only** deliberate exception is the Composio integration edge: the OAuth
popup and trigger broker are hosted by Composio (the managed "middle party" the
product brief asked for). Leave `COMPOSIO_API_KEY` empty and Composio tools
simply report *unavailable*; the manual-token tools and the entire local
pipeline keep working.

---

## 12. History (Mon Parcours)

Reached via **History** in the sidebar.

- **🏆 Achievements:** milestone badges (first diagnostic, strong axis, all axes
  healthy, no blockers, advanced stage, roadmap ready) that unlock from your live
  state — Moufida celebrates the first time one unlocks.
- **Score chart:** your composite scores over time (across diagnostic runs).
- **Compare diagnostics:** a card with a **Compare** button that diffs the two
  latest runs (`GET /history/compare`) — per-score deltas plus which blockers were
  resolved or newly appeared.
- **History list:** every past diagnostic with its stage and blockers.
- **Completed actions:** the roadmap actions you've checked off.

---

## 13. How live updates reach the screen (SSE)

Whenever a project is open, the app holds an **SSE connection** to
`/api/v1/project/{id}/events/stream` (a dedicated stream path, separate from the
REST `/events` list). The backend pushes typed events and the UI reacts (the
sidebar real-time indicator and the companion's reactions are driven from here):

- `score_update`, `maturity_update`, `roadmap_update`, `review_ready` — diagnostic
  results stream in.
- `event_new` — a new Event Card (from any of the four sources).
- `daemon_status` — pause/alive/focus changes → drives the status pill **and the
  sleeping/awake character**.
- `competitor_update` — refreshes the Competitor Board.
- `opportunity_new` — refreshes the Opportunity Radar.
- `watch_targets_updated` — the daemon's adaptive targets were re-derived.
- `concept_update` — the concept breakdown / bottlenecks were refreshed (e.g.
  after a daemon-triggered re-run).
- `kb_updated` / `horizon_complete` — roadmap staleness / horizon celebration.

You never need to refresh — the screen reflects background work as it happens.

---

## 14. Quick reference — "if I click X, then Y"

| You do this | What happens in the background |
|---|---|
| **Got an idea? → Build** | Create project (creation state) + save idea → Creation flow |
| **📁 Mes Projets** | Fetch project list + daemon focus → Projects page |
| **Open a project** | Switch project (no refresh) → Dashboard; auto-diagnostic if no scores |
| **⚡ Diagnose (Projects)** | Open the project + immediately run a full diagnostic |
| **✎ Update profile (Projects)** | Adaptive intake (update mode) → back to Dashboard |
| **👁 Focus a project** | Daemon hot-swaps watchers onto it + re-derives its watch targets |
| **⏸ / ▶ in sidebar** | Pause/resume daemon work → character sleeps/wakes via `daemon_status` |
| **Run diagnostic** | 3-wave axis fan-out → scores/blockers/roadmap streamed over SSE |
| **Approve (creation)** | Persist section → auto-generate next axis |
| **Apply an event** | Re-run downstream axes as proposals |
| **Connect (Composio tool)** | OAuth popup → poll until active → bidirectional triggers + actions |
| **Double-click the character** | Run a quick diagnostic on the open project |
| **Pause the daemon** | Watching stops, heartbeat continues → character sleeps (z z z) |
| **Expand an axis (concept breakdown)** | Shows named concepts + the bottleneck + projected fix |
| **What If? → Project** | 9 parallel RAG-grounded axis projections with confidence + sources |
| **Adopt a scenario** | Patches the profile with the overrides → re-runs the diagnostic |
| **Generate personas** | LLM builds 3 evidence-grounded personas from your diagnostic |
| **Talk to a persona** | Role-play chat; objections tracked; close-strategy after a few rounds |
| **Start a pitch session** | AI investor questions grounded in your data → readiness report |
| **Open `localhost:3002`** | Admin panel: health, request traces, LLM calls, daemon log, live logs |

---

## 15. The analytical features (Pitch · Scenario · Persona · Concepts)

These features turn your diagnostic into something you can *rehearse and
interrogate*. **Personas, Pitch, and Scénarios are now their own sidebar pages**
(not dashboard cards); the concept breakdown stays on the dashboard. They share
one rule: **every output is evidence-grounded** — each claim carries a "Sources"
trace pointing at a real axis field, KB document, competitor snapshot,
opportunity, or background signal.

### Investor Pitch Simulator — **Pitch** page
- Pick an investor persona (Seed VC, Angel, Impact fund, Strategic) and press
  **Start session**. The character takes the **skeptic** pose (blue costume).
- The investor asks one tough question at a time, **only** about things it can
  see in your diagnostic (a low score, a critical blocker, a competitor's
  pricing, a missed grant). Each question shows its evidence trace.
- You type (or dictate) answers. Strong answers visibly relax the character;
  weak/evasive ones make it push harder.
- **End & assess** produces a **readiness report**: an overall 0–100 ring,
  per-axis readiness with gaps, the hardest questions you faced, and prep
  actions you can push to the roadmap.

### Pivot Scenario Planner — **Scénarios** page
- Opened from the sidebar (or the dashboard **What If?** button). Define up to
  three scenarios; each is a set of parameter overrides (e.g. `target_segment →
  B2B`, `pricing → SaaS`). Your drafts are **persisted per project**.
- **Project** runs nine axis projections in parallel, each grounded in a KB query
  for your sector. The comparison table shows the projected score and a ▲/▼/─
  delta per axis per scenario.
- Click any cell to see the **reasoning**, a **confidence** level (high/medium/
  low), and the KB sources behind it.
- **Adopt** the strongest scenario: it patches your profile and re-runs the
  diagnostic so the dashboard reflects the pivot.

### Customer Persona Simulator — **Personas** page
- **Generate personas** builds three realistic customers from your market/
  product/brand axes + KB (name, archetype, region, budget, top objection,
  buying triggers) — each field annotated with where it came from.
- Click a persona to **chat**. It stays in character; every substantive reply
  lists its claim sources. Raised objections appear in a tracker (🔴) and turn
  green (✅) as the conversation resolves them.
- After a few exchanges, **How to close them?** produces a tailored
  close-strategy (key triggers + objections to address).

### Concept breakdown & bottleneck (on the dashboard)
- Under the score gauges, expand any axis to see its score decomposed into named
  concepts scored 0–1. The **bottleneck** (⚡) is the one concept dragging the
  score down the most, with the projected score if you lifted it to 0.80.
- The weights start from sensible defaults ("prior") and **calibrate to your own
  history** over repeated diagnostics ("calibrated").

### Knowledge Base browser — **Base de Connaissances** page
- Browse what Moufida knows: the curated Tunisian-ecosystem resources, with
  filters by **stage / type / sector** and inline reading (title, provider,
  body, source link, last-verified date). Backed by `GET /kb/resources`.

---

## 16. The admin / observability panel (browser, port 3002)

A separate, **read-only** web panel for inspecting Moufida's internals — useful
for demos, debugging, and trust. Open **http://localhost:3002** in any browser
(it talks to the orchestrator at `localhost:8001`). If an `ADMIN_TOKEN` was set in
`.env`, paste it into the Connect field once.

Tabs:
- **Health** — live status + latency of Postgres, Redis, Qdrant, Ollama,
  SearXNG, the signal service, and the daemon, plus per-collection KB health.
- **Requests** — every orchestrator request (method, path, status, duration).
  Click **Trace →** to see the request's correlated **LLM calls** (model, token
  counts, prompt/response previews) — a distributed trace of one operation.
- **LLM Calls** — every Ollama call across the app; click a row for prompt and
  response previews.
- **Daemon** — the background watcher activity log (competitor changes, grants
  found, signals published).
- **Logs** — a real-time, colour-coded log stream (filter by level).

Nothing here changes application state; it only observes.

---

## 17. Behind the scenes: the interpretability service

Two of the features above are powered by **`moufida-signal`**, a small Rust
service (port 8010) you never click directly:
- **Concept Bottleneck scoring** turns each axis's concept activations into the
  composite score and identifies the bottleneck. Its weights are recalibrated
  from your diagnostic history by ridge regression.
- **Axis-direction probing** makes knowledge-base retrieval *axis-aware*: a chunk
  that is really about "business model" is down-weighted when the market axis is
  being scored, and newly ingested documents are auto-tagged to the right axes.

Both are best-effort: if the service is offline, the diagnostic and retrieval
still work — they simply skip the extra interpretability layer.

---

*For the architecture, services, and developer setup, see the
[README](README.md). For build-plan detail, see
[`docs/plan/implementation/`](docs/plan/implementation/) and the research
write-ups in [`docs/research/`](docs/research/).*
