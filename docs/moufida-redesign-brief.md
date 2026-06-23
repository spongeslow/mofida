# Moufida — Product & Brand Brief for a UI Redesign

> **Purpose of this document.** This is the full context a designer needs to redesign
> Moufida's interface from scratch (e.g. in Figma). It describes **what Moufida is**,
> **who it serves**, **what it represents** (brand, personality, colour, the character),
> **what it can do** (capabilities, expressed as neutral user stories), and **what content
> and behaviours the UI must support**.
>
> **It deliberately does NOT prescribe any layout, navigation, screen structure, or
> component arrangement.** Where the current product places things is intentionally
> omitted. Treat every capability below as "the user must be able to reach/see/do this" —
> *how* that is arranged on screen is the designer's job. The only things presented as
> fixed identity are the brand elements the redesign should carry forward (name meaning,
> personality, the pixel character concept, the colour world, typography) — and even those
> may be evolved as long as the spirit is preserved.

---

## 1. What Moufida is

Moufida is an **AI co-founder and startup diagnostic companion for Tunisian entrepreneurs**.
She helps a founder go from a raw idea to an investor-ready venture by doing three things:

1. **Build** — turn a one-line idea into a structured, evidence-grounded business plan.
2. **Diagnose** — analyse an existing venture across nine business axes, score its maturity,
   surface blockers, and recommend concrete next steps.
3. **Accompany** — stay present over time: watch the market, funding deadlines, competitors
   and regulations for the founder's specific project, and react as things change.

Everything Moufida says is **grounded in evidence** — a local knowledge base of curated
Tunisian-ecosystem resources plus live web search — and every claim can be traced back to a
source. She is designed to be **honest** (investor-grade scrutiny, never flattery), **alive**
(continuously working in the background, not a one-shot report), and **useful** — which is
literally what her name means.

Moufida is a **desktop application** that runs largely **local-first** (the analysis,
scoring and knowledge retrieval happen on the user's machine; only optional third-party
integrations reach out). It is **trilingual**: French, English, and Arabic (with full
right-to-left support for Arabic).

---

## 2. Who it's for

- **Primary user:** a Tunisian entrepreneur or early-stage founder — often non-technical,
  often a solo founder or a very small team, frequently working in French and/or Arabic.
  They may be at the "I have an idea" stage, or already running something and wanting to
  understand how investible/mature it is.
- **Their goals:** understand whether their idea holds up; know what to fix first; prepare
  for investors; find funding and support programmes; keep up with their market without
  having to monitor it manually; feel guided rather than judged.
- **Their context:** limited time, limited access to mentors and analysts, a fast-moving
  local ecosystem (grants, accelerators, regulations specific to Tunisia), and a need to
  eventually speak the language of international investors.
- **Their emotional state:** often uncertain, sometimes overwhelmed, needing both honest
  truth and encouragement. The product should make them feel **supported and capable**, not
  graded and dismissed.

---

## 3. What Moufida represents — brand & identity

### 3.1 The name

**Moufida (مفيدة)** is a Tunisian female given name meaning **"useful / beneficial / she
who brings benefit."** The product is personified as **a person** — a warm, knowledgeable
woman who acts as the founder's co-founder, mentor, and advocate. The name and personhood
are central: the experience should feel like working *with someone*, not operating a tool.

### 3.2 Personality & voice

Moufida's character should come through everywhere — in copy, motion, and the character art.

- **Warm and encouraging** — she's on the founder's side; she celebrates progress and
  softens hard news without hiding it.
- **Honest and rigorous** — she gives investor-grade, evidence-backed assessments. She will
  tell a founder their score is low and exactly why. She never flatters and never invents.
- **Knowledgeable and grounded** — she cites sources; she speaks about the *Tunisian* market
  specifically (real grants, real regulations, real competitors).
- **Always present** — she works in the background 24/7 and reacts to what she finds; she
  feels alive rather than on-demand.
- **Bilingual-native** — she's equally natural in French, Arabic, and English, and switches
  to investor English when rehearsing a pitch.

Tone in copy: encouraging, plain-spoken, concrete, never corporate-jargon-heavy. Think
"a sharp, kind mentor who happens to know the whole ecosystem."

### 3.3 The character (a 2D pixel-art companion)

Moufida is embodied as a **2D pixel-art character** — a friendly, retro-game-styled woman.
She is the **face and emotional core** of the product, not a decorative mascot. The redesign
should keep a **pixel-art companion character** as a brand pillar, but is free to reinterpret
her exact look.

What matters about her:

- **She is expressive and reactive.** She has an emotional range that responds to what's
  happening, and the experience should let her *communicate state and react to the user's
  actions*. The emotional/behavioural states she needs to be able to convey include (at
  minimum): **idle/at-rest, listening, thinking/working, speaking, celebrating, alert/alarmed,
  worried, surprised, sleeping/resting, skeptical, presenting/explaining, reading, and
  pointing/guiding.** These map to real moments (running an analysis → working; a milestone
  reached → celebrating; a critical problem found → alert; background watching paused →
  resting; rehearsing a pitch → skeptical investor stance; etc.).
- **She is a companion, present over time** — including as an **always-available presence**
  (the product is a desktop app and she can live as a small persistent companion), reacting
  to background events even when the user isn't actively working.
- **She has personality through motion** — small idle animations, reactions, and celebratory
  moments are part of what makes the product feel *alive and entertaining*, which is an
  explicit experience goal (see §8).
- **Aesthetic:** warm, hand-crafted, retro pixel charm — approachable and a little playful,
  balanced against the seriousness of the analysis. The character should feel Tunisian and
  feminine in spirit. The exact sprite, palette application, costumes/accessories, and
  animation style are open to the designer.

### 3.4 Colour world

The current identity is a **warm-autumn palette** — earthy, warm, optimistic, and distinctly
non-corporate. The redesign should preserve this *warmth and earthiness* as the emotional
signature (it differentiates Moufida from cold "dashboard" SaaS tools), while being free to
refine exact values.

Reference palette (current brand identity, to carry forward in spirit):

| Role | Feel | Example |
|---|---|---|
| Background | cream / sand, warm and soft | `#F5EBDD` |
| Surfaces / panels | warm sand, deeper sand for nesting | `#EDE0CE`, `#E3D3BE` |
| Primary | coffee brown | `#6F4E37` |
| Accent / calls-to-action | "fallen leaves" orange | `#C96A2D` (hover gold `#D98A3A`) |
| Text | dark espresso | `#2C1E17` |
| Muted text / borders | warm brown | `#8B6E5A`, `#CBBAA8` |

Two systematic colour ideas the redesign must support:

- **Sector-adaptive accent.** The accent colour can shift to reflect the founder's *industry*,
  so the app "dresses for" their sector — e.g. green for agri-food, blue for tech, teal for
  health, purple for education, etc. The design should accommodate an accent that varies by
  project sector.
- **A status / score colour grammar.** Scores and health states use a consistent, **colour-
  blind-conscious** tiered scale from "excellent" to "critical" (a green → yellow → amber →
  red progression). Status severities (critical / warning / info) likewise need consistent,
  distinguishable colours. Important: **colour must never be the only signal** — pair it with
  text labels, icons, or numbers.

### 3.5 Typography

The current identity pairs a **serif display face for headings/personality** (Playfair
Display) with a **clean humanist sans for body/UI** (Plus Jakarta Sans). The redesign should
keep a **warm, characterful heading face + a highly legible body face**, and must support
**Latin and Arabic** scripts well.

### 3.6 Values the design must embody

- **Evidence over assertion** — sourced, traceable claims are a feature; the UI should make
  "where did this come from?" always answerable.
- **Honesty with kindness** — bad news is delivered clearly but constructively.
- **Alive, not static** — the product reflects ongoing background work in real time.
- **Local-first & private** — analysis stays on the user's machine; this is a trust signal.
- **Inclusive & trilingual** — FR/EN/AR with proper RTL; nothing should feel bolted-on.
- **Guided, low-anxiety** — a founder should always feel they know what to do next.

---

## 4. The two core journeys

Described as **goals**, not screens.

### 4.1 Creation — "I have an idea"

A founder describes an idea in plain language. Moufida builds a structured plan across **nine
business axes**, one at a time, explaining each axis and grounding each section in evidence.
The founder reviews each generated section and can **accept, refine (with their own
guidance), or regenerate** it. When all axes are done, the plan is assembled into a
**roadmap of concrete next steps drawn from real Tunisian support programmes**, and the
founder ends with a complete, exportable plan document.

The nine axes (the founder should understand each and why it matters):
1. **Ideation** — is the idea clear, original, defensible?
2. **Market** — size, target customers, competitors (Tunisia-specific).
3. **Product** — the MVP and its essential features.
4. **Brand & Innovation** — differentiation and what makes it unique.
5. **Business Model** — how it creates and captures value.
6. **Legal & Green** — legal structure, compliance, sustainability/impact.
7. **Operations** — what's needed to deliver day to day.
8. **Marketing** — how to attract and retain customers.
9. **Sales** — how to turn interest into revenue.

### 4.2 Diagnosis — "I have a venture, how strong is it?"

A founder answers an **adaptive questionnaire** (it branches based on sector and prior
answers) describing their venture. Moufida runs a **full diagnostic** across the nine axes and
returns: **composite scores**, a **maturity stage**, **blockers**, **recommendations**, a
**roadmap**, and deeper interpretability (see §5). The founder can re-run diagnostics over
time and watch their venture evolve.

Both journeys converge on the same living workspace where the founder monitors, interrogates,
and improves their venture.

---

## 5. Capabilities the UI must support (the feature catalogue)

Each item is something the founder must be able to reach and understand. **Layout is open.**

### Health & assessment
- **Composite scores** across five dimensions — **Market, Commercial Offer, Innovation,
  Scalability, Green** — each rated on a 0–5 scale, each decomposable into sub-dimensions
  (with weights, evidence tiers, and a plain-language justification).
- **Maturity stage** on a progression ladder: *Ideation → Market Validation → Structuration
  → Fundraising → Launch Planning → Growth*, with a confidence level and, where relevant, a
  **perception gap** (how the founder self-assessed vs. what the evidence shows).
- **Concept breakdown & bottleneck** — each axis decomposes into named micro-concepts scored
  0–1; the single **bottleneck** concept holding an axis back is highlighted, with the
  projected score lift if it were fixed.
- **Blockers** — issues ranked critical / warning / info.
- **Recommendations** — prioritised, concrete actions tied to the weakest areas.
- **Score debate** — the founder can *argue* a score conversationally; if their evidence is
  convincing, the score updates.

### Planning & progress
- **Roadmap** across three horizons (immediate / short-term / medium-term), with actionable
  steps the founder can check off; completing a horizon generates the next. Roadmap items
  trace back to real Tunisian support programmes, and the founder can see *why* a roadmap was
  produced (its provenance) and regenerate it when underlying data changes.
- **History over time** — composite scores tracked across diagnostic runs; past runs with
  their stage and blockers; completed actions.
- **Compare diagnostics** — diff two runs to see how scores moved and which blockers were
  resolved or newly appeared.
- **Progress & milestones** — the journey from idea to growth is inherently a progression;
  the experience should make advancement feel rewarding and visible (the product lends itself
  to celebrating milestones — the designer decides how, if at all, to express this).

### Rehearsal & exploration (flagship "analytical" features)
- **Investor Pitch Simulator** — rehearse against an AI investor of a chosen archetype
  (Seed VC, Angel, Impact fund, Strategic). The investor asks tough questions grounded *only*
  in the founder's own diagnostic; strong answers ease the pressure, weak ones increase it.
  Ends with a **readiness report** (overall score, per-axis readiness, hardest questions,
  prep actions).
- **Customer Persona Simulator** — generate realistic, evidence-grounded customer personas,
  then **chat** with each one to hear objections and buying signals. Objections are tracked
  and resolved through conversation; a tailored **close-strategy** emerges.
- **Pivot Scenario Planner** — define "what-if" pivots (parameter changes like segment or
  pricing) and see their projected effect across all nine axes, each with a confidence level
  and sources; **adopt** a scenario to apply it and re-diagnose.

> These three (Pitch, Persona, Scenario) are flagship features and should feel substantial
> and focused — they are deep, interactive experiences, not afterthoughts.

### Conversation & assistance
- **Grounded chat assistant** — answers from *the founder's own* diagnostic and data, not
  generic advice. It also **detects change intent** ("we pivoted to B2B", "we hired a CTO")
  and proposes which analyses to re-run, keeping the founder in control.
- **Voice** — the founder can speak to Moufida and hear her reply (speech-to-text and
  text-to-speech run locally); a wake word can summon her.

### Living intelligence (background work made visible)
- **Continuous market watch** — for the founder's focused project, Moufida monitors news
  feeds, legal/regulatory sources, keywords, and competitors. The founder can see and refresh
  *what is being watched*.
- **Competitor intelligence** — a comparison of the founder's venture vs. competitors
  (positioning, pricing, funding) plus strengths/weaknesses analysis, refreshed as competitors
  change.
- **Opportunity radar** — funding/grants and support programmes surfaced with deadlines,
  urgency, and a match score; the founder can act on or dismiss them.
- **Activity digest** — a periodic plain-language summary of what changed recently.
- **Event feed** — every change is an explicit event from one of four sources (the founder's
  manual edits, things said in chat, connected tools, or the background watcher), each with a
  before→after diff and accept / handle / ignore actions.
- **Alerts** — timely notifications when something important happens (e.g. a critical blocker
  detected, a deadline approaching).
- **The background watcher as a presence** — the founder can point Moufida at a specific
  project to watch, and pause/resume that watching; the product should communicate clearly
  whether she is **actively watching, paused, or offline**, and this ties into the character's
  state (watching = awake/active; paused = resting).

### Knowledge & inputs
- **Knowledge base** — browse the curated Tunisian-ecosystem resources Moufida draws on,
  filterable by stage / type / sector, readable inline; the founder can also **add their own**
  notes/links to teach her.
- **Document upload** — attach a business plan, market study, pitch deck, or financial model
  (PDF or text) to enrich the analysis.
- **Evidence & citations everywhere** — analytical outputs carry a traceable "sources" line
  pointing at the exact axis field, knowledge-base document, competitor snapshot, or signal
  they came from. Inline source references should be supported in generated text.

### Portfolio & lifecycle
- **Multiple projects** — a founder may have several ventures; they need to see their
  portfolio, open any one, start a fresh diagnostic on one, update its profile, create new
  ones, import/export, and switch between them.
- **Tool integrations** — optionally connect external tools (e.g. Slack, Notion, Google
  Sheets, GitHub, Analytics) so changes there can flow in as events. Connection state and
  what each integration does should be clear and trustworthy.

---

## 6. User stories (neutral, goal-oriented)

Grouped by intent. Phrased so the redesign can satisfy each however it sees fit.

### Getting started
- As an entrepreneur, I want to **describe my idea in a sentence or two** and have Moufida
  build a structured plan from it, so I don't start from a blank page.
- As an entrepreneur with an existing venture, I want to **answer a short, adaptive set of
  questions** about my business so Moufida can assess it without me filling endless forms.
- As an entrepreneur, I want to **understand what each business axis means and why it
  matters** before I'm asked to judge or approve anything about it.
- As a returning user, I want to **see all my projects and pick up where I left off**, and
  switch between ventures without losing my place.

### Understanding where I stand
- As an entrepreneur, I want to **see my venture's overall health at a glance** — scores,
  maturity, and the most urgent problems — so I immediately know if I'm on track.
- As an entrepreneur, I want to **understand *why* a score is what it is**, broken down into
  sub-factors with plain-language reasoning, not just a number.
- As an entrepreneur, I want to **know my maturity stage and exactly what it would take to
  reach the next one**, so progress feels concrete.
- As an entrepreneur, I want to **find the single biggest thing holding an axis back** and
  see how much fixing it would help.
- As an entrepreneur, I want to **disagree with a score and make my case**, and have Moufida
  reconsider if I bring real evidence.
- As a colour-blind or low-vision user, I want **status conveyed by more than colour** so I
  can always tell critical from healthy.

### Knowing what to do next
- As an entrepreneur, I want a **prioritised list of concrete next actions**, tied to my
  weakest areas.
- As an entrepreneur, I want a **roadmap broken into near / medium / longer-term steps** that
  references real Tunisian programmes, and I want to check actions off and unlock the next set.
- As an entrepreneur, I want to **see how my scores and blockers changed between two
  diagnostics**, so I can tell if my work is paying off.
- As an entrepreneur, I want to **track my scores over time** and feel a sense of progress.

### Rehearsing and exploring
- As an entrepreneur preparing to fundraise, I want to **rehearse against a realistic
  investor** whose questions are based on *my* actual weaknesses, and get a readiness report.
- As an entrepreneur, I want to **talk to simulated versions of my target customers**, hear
  their objections, and learn how to win them over.
- As an entrepreneur considering a pivot, I want to **model "what if I changed X" and see the
  projected impact** across my whole venture before committing — and adopt it if it's better.
- As an entrepreneur, I want **every simulated claim to show its sources**, so I trust the
  rehearsal is grounded in reality.

### Staying current without effort
- As an entrepreneur, I want Moufida to **watch my market, competitors, regulations, and
  funding deadlines for me**, and tell me when something relevant changes.
- As an entrepreneur, I want to **see what Moufida is monitoring** on my behalf and adjust it.
- As an entrepreneur, I want to **discover funding and grants I qualify for**, with deadlines
  and how well they match me, and act on or dismiss them.
- As an entrepreneur, I want to **understand every change as a clear event** with a
  before/after, and decide whether to act on it — nothing should change silently.
- As an entrepreneur, I want to **know whether Moufida is actively watching, paused, or
  offline** at a glance.

### Conversing and inputting
- As an entrepreneur, I want to **ask Moufida questions and get answers grounded in my own
  data**, not generic advice.
- As an entrepreneur, I want to **tell Moufida about a change in plain language** and have her
  recognise it and offer to update the relevant analyses.
- As an entrepreneur, I want to **talk and listen** rather than type, when that's easier.
- As an entrepreneur, I want to **upload my existing documents** so the analysis reflects what
  I've already prepared.
- As an entrepreneur, I want to **browse and add to what Moufida knows**, so I trust and can
  extend her knowledge.

### Trust, language, and feel
- As an entrepreneur, I want to **trace any claim back to its source**, so I trust the advice.
- As a Tunisian user, I want to **work in French, Arabic, or English**, with Arabic laid out
  right-to-left and feeling first-class.
- As an entrepreneur, I want the experience to feel **encouraging and alive** — I want to feel
  I have a companion, not a report generator.

---

## 7. Content & data the UI must convey

So the designer knows the shape of the information to compose:

- **Scores:** five composite scores, each 0–5, each with: a tier (excellent→critical), a set
  of weighted sub-dimensions (name, weight, normalised value, tier), and a justification
  paragraph. Scores can update live and can change over time (deltas matter).
- **Maturity:** one of six ordered stages, a confidence percentage, supporting evidence
  bullets, and possibly a self-vs-computed perception gap.
- **Concepts:** per axis, a set of named concepts each scored 0–1, with one flagged as the
  bottleneck plus a target and projected lift.
- **Blockers:** each has a severity, an axis/domain, and a description.
- **Recommendations:** each has a priority and ties to a score/area.
- **Roadmap:** three horizons, each a list of actions (text, done/not-done), plus provenance
  and staleness state.
- **Personas:** name, archetype, region, budget, top objection, buying triggers, each field
  annotated with its source; plus a chat transcript and tracked objections.
- **Pitch session:** a sequence of investor questions (each with its evidence trace) and
  founder answers; a final readiness report (overall 0–100, per-axis readiness, hardest
  questions, prep actions).
- **Scenarios:** named scenarios, each a set of parameter overrides and a projected per-axis
  effect (delta, confidence, reasoning, sources).
- **Competitors:** per competitor — positioning, pricing, funding, strengths/weaknesses; plus
  the founder's own row for comparison.
- **Opportunities:** title, type, deadline, urgency, match score, source link.
- **Events:** source (manual/chat/tool/watcher), severity, summary, affected axes, a
  before→after diff, a suggested action.
- **Alerts:** severity, title, body, timestamp.
- **Knowledge resources:** title, provider, summary/body, type, stage(s), sector(s), source
  URL, last-verified date.
- **Watch targets:** news feeds, legal sources, keywords, competitors being monitored.
- **Citations/evidence:** a list of sources (title, URL, provider, kb-vs-web), referenced
  inline in generated text.
- **Projects:** name, sector, mode (creation/diagnosis), maturity stage, created date,
  watched-or-not.
- **Connection/real-time state:** whether the live connection is active; whether the
  background watcher is watching/paused/offline.

---

## 8. Experience goals (the bar to clear)

The redesign should make the experience:

- **Smooth** — flows feel continuous and low-friction; the founder is never stranded or
  confused about what to do next.
- **Intuitive** — capabilities are discoverable; nothing important is hidden; the founder
  doesn't need a manual.
- **Entertaining & alive** — the character, motion, reactions, and small celebratory moments
  make the product enjoyable to open daily. Seriousness of analysis + warmth of personality.
- **Meaningful & helpful** — every screen should advance the founder's actual journey, not
  just present data. The founder should leave each session knowing more and with a clearer
  next step.
- **Trustworthy** — grounded, sourced, honest; it admits uncertainty and never fakes
  confidence.

---

## 9. Cross-cutting requirements & constraints

- **Real-time:** the interface reflects background work as it happens (scores streaming in,
  new events/alerts, watcher status) without manual refresh; communicate live-connection state.
- **Trilingual + RTL:** FR / EN / AR with full right-to-left layout for Arabic — plan for text
  expansion/contraction and mirrored layouts from the start.
- **Evidence-first:** "where did this come from?" should be answerable for analytical output;
  inline citations and source traces are first-class.
- **Voice-capable:** speaking and listening are supported modalities, not just typing.
- **Desktop app, local-first:** it runs as a desktop application with analysis on-device; an
  always-present companion presence is part of the concept. Privacy/local-first is a trust
  signal worth surfacing.
- **Graceful states:** design for empty, loading, in-progress (long-running analyses can take
  a while), error, and "no connection" states — long operations especially need honest
  progress and the option to keep working.
- **Accessibility:** never rely on colour alone; ensure contrast; support keyboard use;
  legible type at small sizes; respect reduced-motion preferences for the animations.
- **The character is functional, not decorative:** her state should be meaningful (working,
  alerting, celebrating, resting), and she should be reusable across many contexts and at
  multiple sizes.

---

## 10. Glossary

- **Axis** — one of the nine business dimensions Moufida analyses/builds.
- **Composite score** — one of five 0–5 ratings (Market, Commercial Offer, Innovation,
  Scalability, Green) aggregated from weighted sub-dimensions.
- **Maturity stage** — the venture's position on the Ideation→Growth ladder.
- **Bottleneck (concept)** — the single sub-concept most limiting an axis's score.
- **Blocker** — a critical/warning/info issue to resolve.
- **Roadmap horizon** — immediate / short-term / medium-term band of actions.
- **Diagnostic** — a full run of the nine-axis analysis producing scores, blockers, roadmap.
- **The watcher / background presence** — Moufida's continuous, project-scoped monitoring of
  market, competitors, regulations, and funding.
- **Event** — an explicit, reviewable change from one of four sources.
- **Evidence trace / citation** — the source chain behind a claim.
- **Persona / Pitch / Scenario** — the three flagship interactive "rehearsal" features.

---

*This brief describes the product, its brand, and what the interface must enable — not how to
arrange it. The designer owns layout, navigation, information hierarchy, component design, and
the visual interpretation of Moufida's character and warmth.*
