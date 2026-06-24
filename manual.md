# Moufida — User Manual

*This manual is written for entrepreneurs, not engineers. You do not need to understand how any of this works under the hood — just what each screen does and what you can expect from it.*

---

## Before you begin

Moufida runs entirely on your computer. Your startup data — your idea, your numbers, your plans — never leaves your machine. No subscription, no cloud account, no data harvesting. When the app is running, a small animated character named Moufida will appear at the bottom-right corner of your screen. That character is always watching over your project in the background.

To get started: your technical team runs `docker compose up --build` (the backend) and then `npm run tauri dev` (the desktop app). Once those are running, you interact with Moufida entirely through the graphical interface.

---

## The two windows

**The main window** — the app you interact with: dashboard, chat, analysis, history, settings.

**The companion window** — the small animated Moufida character in the corner of your screen. She is the "face" of the system. When she is walking and awake, the system is actively monitoring your project in the background. When she is sleeping, monitoring is paused.

You open the main window by:
- Clicking the Moufida icon in your system tray (bottom-right of your taskbar)
- Clicking on the companion character
- Pressing **Ctrl + Shift + M** on your keyboard

---

## The companion character — what her behaviour means

The character communicates the system's status through her animations. You do not need to open the app to know what's happening:

| What you see | What it means |
|---|---|
| Walking / roaming | System is active, monitoring your project |
| Thinking (hand on chin) | Running a diagnosis or processing your request |
| Celebrating (arms raised) | A milestone was completed or a diagnosis finished successfully |
| Worried (hand on cheek) | Something needs your attention — a score dropped or an alert arrived |
| Alert (eyes wide) | A critical signal from the background — open the app to check |
| Listening (leaning forward) | She heard "Hey Moufida" or you pressed the voice button |
| Speaking (mouth open) | Moufida is reading her response aloud |
| Sleeping (zzz) | Background monitoring is paused |

**Double-clicking the character** runs a quick diagnosis on your current project.

**Dragging a PDF file onto the character** adds that document (business plan, market study, pitch deck) to your project's knowledge base.

---

## Opening the app for the first time

When no project exists yet, you see the welcome screen with two options:

### "Got an idea?" — Create a new startup plan

Choose this if you have an idea but no formal plan yet. You will be guided through a nine-step process that builds a complete startup plan with evidence, citations, and a roadmap.

Click the button, describe your idea in a sentence or two (or say it out loud), and press **Build**.

### "Mes Projets" — Open your portfolio

Choose this if you have already created projects. Your projects appear here as cards with their latest scores and status.

---

## Your project portfolio (Mes Projets)

This page lists all your startup projects. You can reach it anytime from the sidebar on the left.

Each project card shows:
- The project name and sector
- Whether it's in **creation mode** (building a plan) or **diagnosis mode** (evaluating an existing startup)
- The latest maturity stage (if a diagnosis has been run)

### Actions on each project card

**Open** — opens the project and takes you to the Dashboard. No questionnaire is forced.

**Diagnose** — opens the project and immediately runs a full fresh diagnosis.

**Update profile** — opens the adaptive questionnaire so you can update the project's information before running a new diagnosis.

**Focus (eye icon)** — tells the background monitoring system to watch *this specific project*. The daemon hot-swaps its attention to this project's competitors, funding sources, and regulatory feeds. The character wakes up if she was sleeping.

**Import** — loads a project from a JSON file.

**Delete** — permanently removes the project and all its data.

---

## The adaptive intake questionnaire

This is the adaptive question-and-answer session that collects information about your startup before running a diagnosis.

What makes it "adaptive": the questions are chosen based on your previous answers. If your first answers clearly indicate an early-stage project, you will not be asked about things that only apply to revenue-stage companies. The system typically reaches a reliable assessment in **8–15 questions** rather than the 30+ questions a fixed form would require.

Answer each question honestly. The quality of the diagnosis depends on the accuracy of what you provide.

When the questionnaire ends, the system merges your answers into your project profile and you are taken to the Dashboard.

---

## Creation flow — building a plan from scratch

The creation flow guides you through nine axes of your startup, one at a time:

**Ideation → Market → Product → Brand → Business Model → Legal → Operations → Marketing → Sales**

For each axis, Moufida generates a proposal that is grounded in real Tunisian ecosystem resources and live web search. She narrates what each step is about and why it matters.

For each generated section, you have three choices:

**Approve** — accept the section and move to the next axis automatically.

**Edit with constraints** — type guidance (e.g., "focus more on mobile users" or "emphasise the export opportunity") and Moufida regenerates the section respecting your guidance.

**Retry** — regenerate the section from scratch.

If you close the app mid-plan, it resumes exactly where you left off when you reopen.

When the ninth axis is approved, Moufida generates your **personalised roadmap** — a time-horizoned action plan linked to real Tunisian support programmes, funding sources, and legal frameworks. You can export the full plan as a PDF.

---

## The Dashboard — your project's health overview

The dashboard is the home screen once a project is open. It gives you a complete picture of your startup's current state.

### Maturity stage

A card showing which stage your startup is in: Ideation, Market Validation, Structuration, Fundraising, Launch Planning, or Growth.

It shows:
- The **computed stage** (what the system determined from your data)
- Your **self-assessed stage** (what you said in the questionnaire)
- The **gap** between the two — many founders overestimate their stage; this is normal and the system flags it

### The five composite scores

Five numbers (each out of 5) measuring your startup from different angles:

| Score | What it measures |
|---|---|
| **Market** | How well you understand your market: size, customers, competition, timing |
| **Commercial Offer** | How strong your product/service is: value proposition, maturity, pricing, differentiation |
| **Innovation** | How novel your approach is: product novelty, market novelty, brand distinctiveness |
| **Scalability** | How well the business can grow: unit economics, revenue model, operations, funding readiness |
| **Green** | Legal compliance and sustainability: GDPR, AI Act, IP protection, SDG alignment |

Click any score to expand it. You will see:
- The sub-dimensions and their weights
- The quality of evidence behind the score (declared vs. verified vs. observed by the system)
- A plain-language explanation of why the score is what it is
- A **Debate** button — if you disagree with a score, you can argue your case. If your argument is convincing, the score updates.

### Concept breakdown — what is holding your score back?

Below the score gauges, each axis can be expanded to show a detailed breakdown of named concepts. For example, the Market axis breaks into: TAM Evidence, ICP Specificity, WTP Signal, Competitive Differentiation, Market Timing.

The system identifies the **bottleneck** — the single concept that is holding the score down the most — and tells you: "Fixing this concept from 0.18 to 0.60 would move your market score from 2.3 to 3.1."

This tells you exactly where to focus your energy. Not "improve your market score" but "sharpen your Ideal Customer Profile description."

### Blockers

A ranked list of critical issues the system detected. Three severity levels:

- **Critical** (red) — must address before moving to the next stage
- **Warning** (orange) — should address soon
- **Info** (blue) — worth noting

### Anomaly alerts

The system detects 10 types of internal contradictions in your data. Examples:
- Revenue claimed but zero customer interviews conducted
- LTV (lifetime value) reported without any CAC (customer acquisition cost) data
- AI product with no GDPR or AI Act compliance measures mentioned

These appear as red-flag cards and deserve immediate attention.

### "What's new?" digest

A one-paragraph summary of everything that changed since your last visit — daemon observations, tool integrations, score updates — written in plain language.

### Opportunity Radar

Funding cards from the background grant-watching system. Each card shows:
- The programme name and source
- How well it matches your project (match score out of 1.0)
- The application deadline (turns red when within 14 days)
- A direct Apply link

### Competitor Board

A live board of competitor observations from the background monitoring. For each tracked competitor:
- Latest positioning and pricing
- SWOT analysis
- An indication of what changed since the last check

### Roadmap

A three-horizon action plan (Immediate / Short-term / Medium-term) with each action linked to a real Tunisian support resource. Check off completed actions. When all actions in the active horizon are done, click **Advance horizon** to generate the next set of actions.

A **Stale** banner appears when underlying data changed and the roadmap should be regenerated.

---

## The Chat (HUD) — talking with Moufida

Reached via **Chat (HUD)** in the sidebar.

This is where you have a conversation with Moufida. Every answer she gives is grounded in your own diagnostic data — she does not give generic startup advice; she answers based on your specific scores, blockers, and profile.

### Telling Moufida about a change

If you say something like "we pivoted to B2B" or "we just hired a CTO," the system detects that this is a real update, not just a question. It logs an **Event Card** and asks you which analyses should be re-run in light of the change. You stay in control — nothing changes automatically without your permission.

### Voice input / output

Click the microphone button or press **Ctrl + Shift + V** to speak. Moufida transcribes your voice locally (using Whisper, a local speech recognition model). She responds in text and optionally reads her response aloud.

Language is auto-detected per utterance — you can switch between French and Arabic mid-conversation.

### Watch targets

A card showing what the background monitoring system is currently watching for your project: competitor URLs, news keywords, legal feeds. Click **Refresh** to update these based on your latest profile.

### Add knowledge

Paste a note, a link, or text that Moufida should know about. This is added to your project's knowledge base and enriches future diagnoses and conversations.

---

## The Event Feed — understanding what changed

Every meaningful change to your project is recorded as an **Event Card**. This includes changes you made, things you told Moufida in chat, data from your connected tools, and observations from the background monitoring daemon.

Each event card shows:
- The source (Manual edit / Chat / Tool integration / Background daemon)
- The severity (Critical / Warning / Info)
- Which axes are affected
- A field-level diff showing exactly what changed

For each event, you choose:

**Apply** — accept the change and let the system re-run the affected analyses.

**Handle myself** — mark the event as noted; you will deal with the underlying change manually.

**Ignore** — dismiss the event.

Filtering: you can filter the feed by status (new/acted/ignored) and by source.

---

## Background monitoring — what the daemon does

Once you focus a project (the eye icon in the project list), a background service begins watching the world on your project's behalf. It adapts to your specific sector and profile.

| What it watches | How often | Where you see it |
|---|---|---|
| Competitors (web pages, news) | Every 12 hours | Competitor Board on Dashboard |
| Funding & grants (APII, BFPME, EU calls…) | Daily | Opportunity Radar on Dashboard |
| Legal & regulatory updates (JORT, INNORPI…) | Daily | Event Feed |
| Market trends (your keywords in news) | Weekly | Event Feed / "What's new?" |
| Roadmap milestones | Daily | Event Feed (reminders) |
| Budget alerts (burn rate, runway) | Every 6 hours | Event Feed |

**Pausing monitoring:** Press the ⏸ button in the sidebar to pause the daemon. The character goes to sleep. The monitoring stops but the system stays running. Press ▶ to resume.

---

## Advanced tools

### Investor Pitch Simulator (Pitch page)

Practice your pitch against an AI investor. Choose a persona:
- **Seed VC** — focused on market size, growth potential, team
- **Angel investor** — focused on founder story, product vision, early traction
- **Impact fund** — focused on social impact, SDG alignment, sustainability
- **Strategic investor** — focused on synergies, market positioning, partnerships

The AI asks tough questions **based only on your actual diagnostic data** — if your market score is low, it will ask about that. If you have a competitor with stronger pricing, it will ask about your differentiation.

The session ends with a **Readiness Report**: your overall pitch readiness score, the questions that exposed your weakest points, and preparation actions you can push directly to your roadmap.

### Pivot Scenario Planner (Scénarios page)

A "what if" tool for de-risking decisions before you make them. Define parameter overrides — for example:
- "What if we change target segment from B2C to B2B?"
- "What if we switch from a one-time fee to a subscription model?"
- "What if we focus on the export market instead of domestic?"

The system projects the impact of each change on all nine axes of your startup, with confidence levels and reasons. The comparison shows exactly which axes would improve, which would decline, and by how much.

Click **Adopt** on the best scenario to apply the changes to your profile and run a new diagnosis.

### Customer Persona Simulator (Personas page)

Generates three realistic Tunisian customer personas based on your market and product data. Each persona has a name, archetype, age range, region, income level, goals, top objections, and buying triggers — all grounded in your diagnostic data and the knowledge base.

Click a persona to **chat with them**. The AI responds in character, expressing that persona's objections and buying signals. An objection tracker shows which objections have been addressed in the conversation. After a few exchanges, click **How to close them?** for a tailored close strategy.

### Knowledge Base browser (Base de Connaissances page)

Browse the 83 curated resources about the Tunisian entrepreneurship ecosystem:
- Financing institutions (Smart Capital, BFPME, BTS, Carthage Business Angels)
- Legal frameworks (StartupAct, INNORPI, APII registration)
- Training and accelerators (Flat6Labs, Orange Digital Center)
- Export support (CEPEX)

Filter by your stage, sector, and resource type. Read the full resource inline with the source link.

---

## History (Mon Parcours)

Your startup journey over time.

**Achievements** — milestone badges that unlock as you progress: first diagnosis, first strong score, all axes healthy, advanced stage, roadmap completed. Moufida celebrates when you earn a new badge.

**Score chart** — your five composite scores plotted over time, showing progress across diagnostic runs.

**Compare diagnostics** — select any two past diagnoses and see a side-by-side comparison: how each score moved, which blockers were resolved, which new ones appeared.

**History list** — every past diagnostic with its date, maturity stage, and top blockers.

**Completed actions** — the roadmap actions you have checked off.

---

## Settings

**Show companion** — toggle the desktop companion character on or off.

**Language** — French, English, or Arabic (Arabic flips the entire interface to right-to-left).

### Tool integrations

Connect Moufida to the tools you already use. There are two types:

**Manual-token tools** — paste a credential (API key, bot token), test the connection, and save. Simple but one-directional.

**Composio tools** — click Connect and authorise in a browser popup. No credentials to manage. These are **bidirectional**: changes in your connected tool (a Notion page updated, a new GitHub commit) flow back into Moufida and appear as Event Cards.

| Tool | What it does for your diagnosis |
|---|---|
| **GitHub** | Upgrades product and operations evidence tiers from "self-reported" to "observed" based on your actual commit and PR activity |
| **Notion** | Reads your spec documents and customer notes to enrich ideation, market, and product analyses |
| **Google Sheets** | Reads your financial metrics; pushes score summaries to your tracking sheet |
| **Google Analytics** | Reads your traffic and conversion data to enrich market and sales analyses |
| **Slack** | Posts diagnostic briefings and score alerts to your team channel |

**Why connecting tools improves your scores:** Moufida uses a three-tier evidence model. Data you provide yourself counts at 0.6× weight. Data from uploaded documents counts at 1.0×. Data observed directly from connected tools counts at 1.2×. A founder who says "we have strong engineering" scores lower on the product axis than one whose connected GitHub shows 200 commits in the last month. The tool integrations make your evidence more credible.

---

## The admin panel (for technical users)

Open a browser and go to **http://localhost:3002** while the backend is running.

This panel lets you see exactly what Moufida is doing internally: every HTTP request, every LLM call (with duration and token counts), every background daemon activity, and a live log stream.

It is read-only — nothing in this panel changes application data. It is useful for checking that all services are healthy, verifying that a diagnosis worked end-to-end, and understanding how the system used your data.

---

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| **Ctrl + Shift + M** | Show / hide the main window |
| **Ctrl + Shift + D** | Run a full diagnosis |
| **Ctrl + Shift + V** | Start voice input |
| **Ctrl + Enter** | Submit (in forms, chat) |
| **Double-click companion** | Quick diagnosis |

---

## Quick reference — "if I want to... then I..."

| Goal | Action |
|---|---|
| Start from a new idea | Welcome screen → "Got an idea?" |
| Evaluate an existing startup | Projects page → "Diagnose" |
| Update my project's information | Projects page → "Update profile" |
| Start background monitoring for a project | Projects page → eye icon (Focus) |
| Pause monitoring temporarily | Sidebar → ⏸ pause button |
| Tell Moufida about a change in my startup | Chat (HUD) → describe the change in conversation |
| Upload a business plan or pitch deck | Dashboard header → upload button, or drag onto the companion |
| Argue with a score I disagree with | Dashboard → click the score gauge → "Debate" |
| Practice my investor pitch | Sidebar → Pitch page |
| Explore "what if we pivoted to B2B?" | Sidebar → Scénarios page |
| Understand which customers to target | Sidebar → Personas page |
| Browse Tunisian funding programmes | Sidebar → Base de Connaissances |
| See how my scores evolved over time | Sidebar → Mon Parcours |
| Connect GitHub / Notion / Slack | Sidebar → Settings → Tool integrations |
| Check system health | Browser → http://localhost:3002 |
