# Core Product Logic — Project Creation & Continuous Monitoring

> Comprehensive specification of the Moufida desktop application's two-mode
> design, multi-project support, continuous update architecture, and adaptive
> roadmap engine.
>
> **Status:** Design document — guides upcoming implementation.

---

## 1. Two Operating Modes — Same Axis Services, Different Behavior

The ten axis services (Ideation, Market, Product, Brand, Business Model, Legal,
Operations, Marketing, Sales, Roadmap) are the same regardless of mode. **What
changes is the mode the orchestrator passes to each service:**

| Mode | Purpose | Service Mode | Output |
|------|---------|-------------|--------|
| **Creation** | Build a startup plan from a raw idea | `generate` | Structured plan section (proposal) |
| **Diagnosis** | Evaluate an existing project | `evaluate` | Score, confidence, evidence, blockers |

The orchestrator selects the mode at flow start and propagates it to every axis
call. A project is created in one mode and stays there, but the **diagnosis mode
can be re-run at any time** against the current state of the project (whether it
was originally created in the app or imported from outside).

### 1.1 Mode Comparison

| Aspect | Creation Mode | Diagnosis Mode |
|--------|--------------|---------------|
| Entry | "Got any idea?" button + raw idea text | "Diagnose existing" → intake + file upload |
| Axis role | Generate/refine a section of the plan | Evaluate the project against the axis criteria |
| User interaction | Review cards with Approve/Edit/Retry per axis | Score report with optional chat-based debate |
| End state | A complete, exportable startup plan (PDF) | A detailed diagnostic report with scores & blockers |
| Persistence | Plan sections stored per project | Scores, evidence, blockers stored per diagnostic run |
| Re-trigger | When user edits a plan section | On demand or when significant updates occur |

---

## 2. Creation Flow — "Got any idea?"

### 2.1 Entry Point

On the landing page the user sees a **"Got any idea?"** button alongside the
existing "Diagnose existing" button. Clicking it opens a **textarea** where the
user describes their startup idea in free text:

```
┌─────────────────────────────────────────────┐
│  Got any idea?                              │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │ A mobile app that connects local      │  │
│  │ farmers to restaurants so they can    │  │
│  │ sell surplus produce directly...      │  │
│  │                                       │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  [  Let's build it  ]                       │
└─────────────────────────────────────────────┘
```

### 2.2 Step-by-Step Generation Loop

Each of the nine axes (Ideation through Sales, excluding Roadmap) runs
sequentially in `generate` mode. The output of each approved axis becomes input
for the next:

```
Raw idea → [Ideation] → approved → [Market] → approved → [Product] → ... → [Sales] → approved
                ↓                              ↓                              ↓
          Validated idea                 Market research                 GTM plan
          + positioning                  + segments                      + channels
```

#### Per-Axis Flow

1. **Axis receives:**
   - The original raw idea
   - All previously approved axis outputs (as accumulated context)
   - Its own generation prompt (varies per axis)

2. **Axis generates** a structured proposal for its domain:
   - **Ideation** — validates the idea, proposes a refined version with
     positioning, vision statement, and problem-solution fit
   - **Market** — proposes target segments, market size estimate, competitor
     landscape, differentiation strategy
   - **Product** — proposes MVP feature set, user stories, technical stack
     recommendations
   - **Brand** — proposes brand values, tone of voice, visual direction
   - **Business Model** — proposes revenue streams, pricing model, cost
     structure
   - **Legal** — proposes legal structure, IP considerations, regulatory needs
   - **Operations** — proposes team structure, processes, tools, timeline
   - **Marketing** — proposes acquisition channels, content strategy, launch
     plan
   - **Sales** — proposes sales channels, pipeline model, partnership strategy

3. **User reviews the proposal** in a card UI with three actions:
   - **Approve** — accepts the proposal as-is. The output is saved as the
     axis's plan section. The flow moves to the next axis.
   - **Edit** — the user modifies the proposal (inline textarea or structured
     fields). The modified version is sent back to the **same axis** to
     re-generate with the user's edits as constraints. The new proposal is
     shown for approval. Loop repeats until approved.
   - **Retry** — the axis re-runs without user edits (useful if the proposal
     seems low quality or something changed contextually). A new proposal is
     shown.

4. **Stepper sidebar** shows all axes with status (pending / current / done)
   and a progress counter: "4 / 9 axes complete"

### 2.3 Completion

After all nine axes are approved, the **Roadmap axis (Axis 10)** runs last to
generate a milestone plan based on the complete plan. The user then sees a
**completion screen** with:

- The full assembled plan in an interactive document view
- An **"Export as PDF"** button
- A **"View Dashboard"** button to transition into monitoring mode

### 2.4 Interactive Plan Document

The completed plan is displayed as a structured, collapsible document with one
section per axis. Each section shows:

- Axis label and summary
- Key decisions made (e.g., target market, pricing, tech stack)
- The proposal text
- **Inline edit buttons** — user can edit any section at any time, triggering
  the dependency resolution engine (see §5.5)

This document is the **living project plan** — it is never "done", it evolves as
the project evolves.

---

## 3. Diagnosis Flow — "Diagnose existing"

### 3.1 Entry Point

Clicking **"Diagnose existing"** on landing or selecting an existing project
opens the **Intake Wizard**:

- Branching questionnaire (adaptive, ~9 questions about sector, revenue, team,
  legal form, etc.)
- **Optional PDF upload** — user can upload relevant documents (business plan,
  pitch deck, financial statements, etc.). The system extracts text and feeds
  it as additional evidence context to each axis service.

### 3.2 Thorough Diagnostic Run

All ten axes run in `evaluate` mode. Each axis receives:

- The intake answers (structured profile)
- Extracted text from uploaded PDFs (if any)
- Previously stored plan sections (if the project was created in the app)

Each axis returns:
- **Score** — numeric value out of 5
- **Confidence** — percentage (how sure the system is about this score)
- **Evidence** — bullet list of what was found that supports the score
- **Blockers** — critical, major, or minor issues identified
- **Justification** — natural-language explanation of why this score was given

### 3.3 Interactive Per-Axis Review

After all axes complete, the user sees a **diagnostic report** — one section
per axis with score gauges, evidence, blockers, and justifications.

For each axis, the user can **click "Debate"** to open a chat with Moufida
about that specific axis score. The user can argue, provide additional context,
or ask for clarification. If Moufida is convinced by the user's argument, the
score is **recalculated** and locked. If not convinced, the score stays as-is.

This replaces the Approve/Edit/Retry cycle of creation mode — in diagnosis
mode, there are no user actions to approve; only optional debate.

### 3.4 Diagnostic History

Every diagnostic run is saved as a snapshot in the project's history. The user
can:

- View past reports
- Compare scores across runs (improvement/decline per axis)
- See what evidence changed between runs
- Track blocker resolution over time

---

## 4. Multi-Project Dashboard

### 4.1 Project Selector

The dashboard has a **project selector** at the top — a dropdown or tab bar
listing all projects the user has created or imported:

```
[ My Projects ▼ ]

┌─────────────────────────────────────┐
│  FarmLink (Creation)    ● Maturite   │
│  GreenCart (Diagnosis)  ● Emergence  │
│  My SaaS (Diagnosis)    ● Structuration │
│  [+ New Project]                     │
└─────────────────────────────────────┘
```

### 4.2 Per-Project State

Each project maintains its own independent state:

| State | Creation Mode | Diagnosis Mode |
|-------|--------------|---------------|
| Scores | Set from the plan (theoretical baseline) | Set from diagnostic runs |
| Roadmap | Milestone plan from Axis 10 | Improvement plan from Axis 10 |
| Plan sections | Full structured document | Not applicable (no plan generated) |
| Events | Feed of all updates | Feed of all updates |
| History | Plan version timeline | Diagnostic run timeline |

### 4.3 Cross-Project Operations

- Create a new project from scratch
- Import a project from JSON/PDF
- Delete a project
- Switch between projects without losing state

---

## 5. Continuous Updates — Four Sources of Ground Truth

A project is never static. The user continuously updates it, and Moufida
continuously monitors it. There are four sources of update signals, each
feeding into the **dependency resolution engine** which determines which axes
to re-run.

### 5.1 Source A: Manual UI Edits

The user opens the interactive plan document and directly modifies a section:

- Edits the Ideation section's vision statement
- Updates the budget figure in Business Model
- Adds a new team role in Operations

**Flow:**
```
User edits section X
  → Dependency engine determines which axes depend on X
  → Affected axes re-run in creation mode (generate updated proposals)
  → User reviews the updated proposals (Approve/Edit/Retry)
  → Changes propagate to downstream axes
  → Event logged: "You updated the budget — Business Model and Operations re-generated"
```

### 5.2 Source B: Chat-Driven Updates

The user tells Moufida in natural language via the chat HUD:

- "I just hired a CTO"
- "We pivoted from B2C to B2B"
- "The seed round closed at 500k"
- "Our main competitor launched a similar feature"

**Flow:**
```
User message
  → Moufida LLM interprets the signal
  → Identifies which plan sections need updating
  → Identifies which axes are affected (dependency resolution)
  → Applies updates to plan sections
  → Re-runs affected axes (in creation or diagnosis mode as appropriate)
  → Reports back: "I updated the team section and re-ran Operations.
     Here's what changed. The Product score may also be affected —
     would you like me to re-run Product too?"
```

If the user agrees to the suggested scope, Moufida proceeds. If not, the user
can narrow or expand the scope.

### 5.3 Source C: Tool Integration Signals

Connected third-party tools push structured data. Each tool has a defined
schema of what signals it can emit:

| Tool | Signals | Affected Axes |
|------|---------|--------------|
| Accounting (e.g., Odoo) | Revenue change, expense spike, cash flow alert | Business Model, Operations |
| CRM (e.g., Twenty) | New deals, churn rate, pipeline changes | Sales, Marketing |
| Project Management (e.g., Plane) | Milestone reached, sprint velocity | Operations, Product |
| Analytics (e.g., Plausible) | User growth, engagement metrics | Product, Marketing |
| HR (e.g., Frappe HR) | New hires, departures, role changes | Operations |

**Flow:**
```
Tool signal arrives
  → Moufida interprets the signal against the current project plan
  → Determines which plan sections and axes are affected
  → Updates plan sections automatically (structured data → structured updates)
  → Re-runs affected axes
  → Reports: "Your CRM shows 3 new enterprise deals this week.
     I updated the Sales pipeline section and re-ran Sales.
     Revenue projection increased 22%. Would you like to see the updated Business Model?"
```

### 5.4 Source D: Go Daemon Events

The Go daemon watches external data sources and detects significant changes.
These could be:

- Market news relevant to the project's sector
- Regulatory changes
- Competitor activity
- Macroeconomic indicators

**Event Card UI:**

```
┌─────────────────────────────────────────────────────┐
│  📡 New regulation published for AgriTech sector    │
│  ─────────────────────────────────────────────────  │
│  The Ministry of Agriculture published new          │
│  labeling requirements for direct-to-consumer       │
│  produce sales, effective Q3 2025.                  │
│                                                     │
│  🤖 Moufida suggests: This affects your Legal and   │
│  Operations axes — compliance section needs review. │
│                                                     │
│  [  Act — Moufida, handle it  ]  [  Manual  ]  [ Ignore ] │
└─────────────────────────────────────────────────────┘
```

User has three options:

| Option | Behavior |
|--------|----------|
| **Act** | Moufida executes the suggested update (edits relevant plan sections + re-runs affected axes + reports back) |
| **Manual** | Opens the relevant plan section(s) for the user to edit themselves |
| **Ignore** | Dismisses the event. Does nothing. Event can be revisited from the event feed. |

### 5.5 Dependency Resolution Engine

This is the core intelligence that decides **what to re-run** when anything
changes.

**Dependency Graph** (simplified):

```
Ideation ← Market ← Product ← Brand
    ↕         ↕        ↕        ↕
Business Model ← Legal ← Operations ← Marketing ← Sales
                                        ↕
                                    Roadmap
```

Each axis declares its **direct dependencies**:

| Axis | Depends On |
|------|-----------|
| Ideation | — (root) |
| Market | Ideation |
| Product | Market, Ideation |
| Brand | Ideation, Product |
| Business Model | Product, Market, Operations |
| Legal | Business Model, Ideation |
| Operations | Business Model, Product |
| Marketing | Product, Brand, Operations |
| Sales | Marketing, Operations, Business Model |
| Roadmap | All axes |

**When an update occurs on axis X:**
1. Mark X as dirty
2. Walk the dependency tree forward from X to find all transitive dependents
3. Re-run all dirty axes in topological order
4. Merge results back into the plan

**Example:** User edits the pricing model (Business Model section)
```
Business Model edited
  → Direct dependents: Legal, Operations
  → Transitive dependents: Operations → Marketing → Sales
  → Re-run: Legal, Operations, Marketing, Sales
  → Roadmap also re-runs (depends on everything)
  → Updates NOT re-run: Ideation, Market, Product, Brand
```

### 5.6 Event Feed UI

A chronological, filterable feed of **every update** from any source:

```
┌──────────────────────────────────────────────────────────────┐
│  📋 Event Feed                                [Filter ▼]     │
│  ──────────────────────────────────────────────────────────── │
│  📡  Today 14:23  — Daemon: New regulation (AgriTech)      │
│       Moufida updated Legal & Operations. [View diff]       │
│  📡  Today 11:05  — Tool: CRM — 3 new enterprise deals     │
│       Sales re-run. Revenue +22%. [View diff]               │
│  💬  Yesterday  — You: "I hired a CTO"                     │
│       Team section updated. Operations re-run. [View diff]   │
│  ✎   Yesterday  — You edited: Budget (Business Model)      │
│       Legal, Operations, Marketing, Sales re-run. [View diff]│
│  📡  2 days ago — Tool: Accounting — Expense spike alert   │
│       [ Ignored ]                                           │
└──────────────────────────────────────────────────────────────┘
```

Each event has:
- Timestamp and source icon (manual ✎ / chat 💬 / tool 📡 / daemon 🛰️)
- Summary of what happened
- Which axes were affected
- Moufida's action (what she updated)
- **View diff** — side-by-side comparison of what changed in the plan
- **Revisit** button (for ignored events)
- Filter by source, axis, date range, severity

### 5.7 "What's New?" Query

User asks via voice or chat: *"What's new?"*, *"What changed since yesterday?"*,
*"Any updates to my roadmap?"*

Moufida responds with a natural-language summary of recent events, prioritised
by impact:

> "Since yesterday, three things happened:
> 1. Your CRM logged 3 new enterprise deals — I updated Sales and your
>    revenue projection went up 22%.
> 2. You edited the budget — I re-ran Legal, Operations, and Marketing.
> 3. A new regulation was published for your sector. I updated the
>    compliance section. Would you like me to show you the changes?"

The user can drill into any item for details.

---

## 6. Roadmap (Axis 10) — Live, Adaptive, Continuously Improving

The roadmap axis is special — it is the last to run, depends on all other axes,
and its output is the most dynamic. It uses **RAG (Retrieval-Augmented
Generation)** over a knowledge base to produce actionable milestone plans.

### 6.1 Evolving RAG Knowledge Base

The knowledge base is **not static**. It grows and improves over time:

**Sources of knowledge:**
- **Initial seed** — a curated set of startup playbooks, sector guides,
  regulatory frameworks, and best practices
- **Tool integrations** — structured data from connected tools becomes
  searchable context (e.g., actual market data from CRM, actual burn rates
  from accounting)
- **User uploads** — any PDF or document the user uploads during diagnosis
  becomes part of the project's context (and, with permission, can be
  anonymized and added to the global KB)
- **Manual additions** — user can explicitly add resources, links, or notes
- **External feeds** — optional curated feeds (regulatory updates, market
  reports, sector news) pulled by the Go daemon

**Versioning:** Each roadmap generation records which version of the KB was
used, so the user can see "this recommendation was based on these sources".

### 6.2 Progress-Aware Roadmap

The roadmap is a living document, not a one-shot output:

**When user checks off an action:**
- The action card gets a green check, strikethrough text, reduced opacity
- The "Completed Actions" counter increments
- A celebration animation plays (Moufida reacts)
- The completed action moves to the "Completed" log (visible in Mon Parcours)
- **New actions are generated for the next horizon** based on what was
  accomplished

**Example:**
```
Day 1 — Roadmap generated:
  Immediate:  [✓] Define MVP scope  [ ] Find beta testers  [ ] Set up dev
  Short-term: [ ] Build v1  [ ] Launch to beta users  [ ] Set up analytics
  Medium-term:[ ] Scale to 1000 users  [ ] Hire support team  [ ] Raise seed

Day 7 — User checks "Define MVP scope" and "Set up dev environment":
  Immediate:  [✓] Define MVP scope  [ ] Find beta testers  [✓] Set up dev
  Short-term: [ ] Build v1  [ ] Launch to beta users  [ ] Set up analytics
              ← NEW: "Create user onboarding flow"
  Medium-term:[ ] Scale to 1000 users  [ ] Hire support team  [ ] Raise seed
```

**Milestone UI updates:**
- When all immediate actions are done → the immediate column shows a
  completion badge and collapses
- Short-term actions shift up visually as the new "current" focus
- Moufida announces: "Great progress! All immediate actions are done. I've
  added a new action for the next phase based on what you've accomplished."

### 6.3 Score-Driven Re-Prioritization

If a diagnostic run or a significant update changes axis scores, the roadmap
automatically re-prioritizes:

**Rules:**
- An axis whose score **drops** significantly (>=1.0 point drop) gets its
  related actions moved to higher priority (medium-term → short-term,
  short-term → immediate)
- An axis whose score **improves** significantly gets its completed actions
  archived and new, more advanced actions proposed
- The user sees a notification badge: "3 actions re-prioritized due to
  Market score change"

**Example:**
```
Before:
  Market score: 3.8
  Roadmap: [Medium-term] Conduct competitive analysis

After competitor launch:
  Market score: 2.4 (dropped 1.4 points)
  Roadmap auto-update:
  → "Conduct competitive analysis" moved from Medium-term → Short-term
  → New immediate action: "Schedule customer interviews to assess competitor"
  → User notified: "Market score dropped. I've re-prioritized 2 actions."
```

### 6.4 Generation Cadence

The roadmap generates:

- **On-demand** — user clicks "Re-generate roadmap" button
- **After any significant update** — when an axis re-runs and produces
  materially different output, the roadmap is flagged as stale and a
  re-generation is suggested (not automatic — user approves)
- **Never on a timer** — no scheduled auto-runs. The user decides when to
  refresh.

---

## 7. Service Behavior by Mode (Reference Table)

| Axis | Creation Mode (`generate`) | Diagnosis Mode (`evaluate`) |
|------|---------------------------|---------------------------|
| **Ideation** | Validates the raw idea, proposes a refined version with positioning, vision, problem-solution fit | Scores the idea's clarity, viability, originality, and problem-solution fit. Lists gaps |
| **Market** | Proposes target segments, market size estimate, competitor landscape, differentiation | Scores market understanding, segment specificity, competitive awareness. Lists blind spots |
| **Product** | Proposes MVP features, user stories, technical stack recommendations | Scores product readiness, feature-market fit, technical feasibility. Lists risks |
| **Brand** | Proposes brand values, tone of voice, visual direction | Scores brand identity strength, consistency, differentiation |
| **Business Model** | Proposes revenue streams, pricing model, cost structure, unit economics | Scores business viability, margin health, revenue model robustness. Lists financial risks |
| **Legal** | Proposes legal structure, IP strategy, regulatory considerations | Scores legal compliance, IP protection status, regulatory exposure. Lists compliance gaps |
| **Operations** | Proposes team structure, processes, tools, timeline | Scores operational maturity, process documentation, resource allocation. Lists inefficiencies |
| **Marketing** | Proposes acquisition channels, content strategy, launch plan | Scores marketing readiness, channel strategy, campaign effectiveness. Lists gaps |
| **Sales** | Proposes sales channels, pipeline model, partnership strategy | Scores sales capability, pipeline health, revenue forecasts. Lists risks |
| **Roadmap** | Generates milestone plan from the assembled plan | Generates improvement plan from diagnostic results |

---

## 8. Data Model Additions

The following new tables or extended fields are needed to support this logic:

| Entity | Purpose | Key Fields |
|--------|---------|-----------|
| `projects` | Multi-project support | `id`, `name`, `mode` (creation/diagnosis), `sector`, `state`, `created_at` |
| `plan_sections` | Per-axis plan content with versioning | `project_id`, `axis_slug`, `version`, `content` (JSONB), `approved`, `created_at` |
| `dependency_graph` | Axis-to-axis dependency edges | `axis`, `depends_on` (array), `version` |
| `events` | All update events from any source | `id`, `project_id`, `source` (manual/chat/tool/daemon), `type`, `summary`, `axes_affected` (array), `diff`, `ignored`, `created_at` |
| `knowledge_base` | Versioned RAG content with sources | `id`, `source`, `content`, `metadata` (JSONB), `version`, `created_at` |
| `tool_signals` | Raw data from tool integrations | `project_id`, `tool_slug`, `signal_type`, `payload` (JSONB), `processed`, `created_at` |
| `roadmap_action_status` | (already exists) Per-action completion tracking | `project_id`, `action_key`, `completed`, `completed_at` |

---

## 9. Comparison with Current Implementation

| Component | Current State | What Changes |
|-----------|--------------|-------------|
| Landing page | "New Project" + "Diagnose Existing" buttons | Replace "New Project" with "Got any idea?" → textarea |
| Intake Wizard | Used for both new and existing projects | Used only for Diagnosis mode (existing projects + PDF upload) |
| Creation Flow | Review cards from diagnostic output | Replace with generation loop: services propose, user approves/edits/retries per axis |
| Dashboard | Single project, scores from diagnostic | Add project selector, per-project state |
| Roadmap | Checkboxes for completion | Add progress-aware generation (new actions on completion), score-driven re-prioritization, evolving KB |
| Chat | Generic Q&A | Add chat-driven updates: Moufida interprets, applies, re-runs, reports |
| Tool integrations | CRUD + sync | Add signal interpretation: structured data → plan updates → re-run affected axes |
| Daemon | Metric alerts → SSE | Add event cards with Act/Manual/Ignore options + Moufida suggestions |
| Event feed | Not implemented | New chronological feed of all updates from any source |
| "What's new?" | Not implemented | Voice/chat query → Moufida summarizes recent changes |
| Multi-project | Single project at startup | Full multi-project CRUD with selector |
| PDF export | Not implemented | Export assembled plan as PDF |
| PDF import | Not implemented | Upload PDF during diagnosis → text extraction → evidence for axes |
| Dependency engine | Not implemented | Compute transitive closure of affected axes on any update |
| KB versioning | Not implemented | Track which KB version was used per roadmap generation |
