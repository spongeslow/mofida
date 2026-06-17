# 3. Detailed Component Responsibilities

## 3.1 Orchestrator (FastAPI + LangGraph) – Port 8001

**Role.** The orchestrator is the "brain" that decides what to do next. It listens to your voice commands, runs the adaptive questionnaire, calls the right axis services, collects their answers, and stores everything in a database. It also listens to the Go daemon's signals and forwards them to the relevant axes. Where voice commands are involved, the orchestrator first consults the `lang_detect` step described in Section 5 so that downstream prompts are routed to the correct language variant.

**Technical responsibilities:**

- **State router**: decides whether to run STATE_NEW or STATE_EXISTING based on user selection or an existing profile.
- **Adaptive intake endpoint**:
  - Implements a branching questionnaire that adapts to the entrepreneur's sector, revenue, team size, legal form, and previous answers.
  - Stores all answers in the StartupProfile under a diagnostic context field, following the field catalogue and evidence tiering defined in Section 3.3.
  - Example branching: if the user selects "agri-food", additional questions about certifications appear; if revenue is reported above zero, questions about validation evidence appear.
- **Diagnostic pass orchestrator**:
  - Calls the `diagnose` endpoint on a predefined set of axes (Ideation, Market Research, Product Design, Business Model, Legal, Operations, Go-to-Market).
  - Collects maturity stage (from Axis 01), blockers (from each axis), and scores (Market, Commercial Offer, Scalability, Green, Innovation – the latter owned by Axis 04 as detailed in Section 4).
  - Aggregates the results, computes the perception gap (user's self-assessed stage vs. system stage), and ranks blockers by severity.
  - Invokes Axis 10's roadmap endpoint with the aggregated gaps, blockers, and low scores.
  - Stores all diagnostic outputs in PostgreSQL.
- **Background Redis consumer**:
  - Listens to the Redis channel `moufida:metrics` where the Go daemon publishes real-time signals.
  - Forwards each metric only to the axes that are affected (e.g., competitor news → Axis 02, budget update → Axis 05, legal alert → Axis 06). Uses a static routing table.
  - When a metric arrives, it calls the axis's `metric_update` endpoint, which triggers a re-evaluation of scores and blockers.
- **Human review integration**: forwards user decisions (Approve, Edit, Retry) to the appropriate axis or to the roadmap generator.

---

## 3.2 Axis Services (Ports 8101–8110) – Each Specialised Agent

Each axis is a FastAPI microservice with its own LLM agent and domain logic. Below is a breakdown of what each axis implements for diagnostic mode.

### 3.2.1 Axis 01 – Ideation

**Business logic.** This axis helps the entrepreneur turn a raw idea into a concrete concept. It uses creativity techniques (SCAMPER, Design Thinking, TRIZ) to generate variations of the idea and tests feasibility. In diagnostic mode, it acts as a maturity classifier: it reads everything known about the project and decides which of the six stages it belongs to, providing evidence for that decision.

**Technical implementation.**

- **Original `execute` endpoint**: unchanged – generates brainstorming, SCAMPER variations, feasibility scores.
- **`diagnose` endpoint**:
  - Reads the StartupProfile (intake answers and any existing data).
  - Uses a lightweight LLM (Mistral 7B) with a prompt that asks: "Based on the collected evidence, assign one maturity stage (Ideation, Market Validation, Structuration, Fundraising, Launch Planning, Growth) and list 3–5 specific evidence points."
  - Returns the maturity stage, a confidence score, and the evidence list.
- **`metric_update` endpoint**: receives milestone completion signals (from Go daemon) and may upgrade the maturity stage if major milestones are achieved.

The maturity classifier produced by this endpoint is evaluated against a labelled 50-vignette benchmark rather than an ad hoc smoke test; the full ground-truth construction, labelling protocol, and target metrics are given in Tier 1 of Section 6.

### 3.2.2 Axis 02 – Market Research

**Business logic.** This axis analyses the market size, customer segments, and competition. It produces a Market Score based on how well the entrepreneur has validated the market, how clear the revenue model is, and how intense the competition is. It also flags blockers like missing customer interviews.

**Technical implementation.**

- **Original `execute` endpoint**: unchanged – generates market segmentation, competitor analysis, TAM/SAM/SOM, personas.
- **`diagnose` endpoint**:
  - Computes the Market Score using the shared Affinitree library. The score decomposes into sub-dimensions: addressable market size, customer validation evidence, revenue model clarity, and competitive intensity, fed from the `market.*` fields of the StartupProfile catalogued in Table 1.
  - Returns the score, per-component contributions, and a list of market blockers (e.g., "no customer interviews", "missing competitor analysis").
- **`metric_update` endpoint**:
  - Receives competitor watcher signals (new product launches, funding events, etc.).
  - Re-runs the Affinitree market score with updated competition data. If the score drops significantly, it pushes an SSE alert to the frontend.

### 3.2.3 Axis 03 – Product Design

**Business logic.** Evaluates the product or service itself. Looks at how clearly the value proposition is defined, how mature the product is (prototype, MVP, full product), whether the pricing makes sense, and how differentiated the offer is from competitors.

**Technical implementation.**

- **`diagnose` endpoint**:
  - Computes the Commercial Offer Score using Affinitree. Sub-dimensions: value proposition clarity, product/service maturity, pricing coherence, differentiation. The two free-text sub-dimensions (value proposition, differentiation) are scored via the rubric-based LLM-as-judge procedure described in Section 3.3.3.
  - Returns the score, component breakdown, and product gaps (e.g., "missing prototype", "unclear pricing").

### 3.2.4 Axis 04 – Brand Identity

**Business logic.** Assesses the strength of the brand: does it have a clear personality, a recognisable logo, a consistent voice? Axis 04 is the designated owner and aggregator of the Innovation Score (Section 4), since brand and product novelty are the dominant expressions of innovation for early-stage ventures, and contributes separately to the Commercial Offer Score (how attractive the brand is to customers).

**Technical implementation.**

- **`diagnose` endpoint**:
  - Receives the full aggregated StartupProfile, together with the outputs already computed by Axes 01 and 02 (TRL, IP status, competitor count), and calls `Affinitree(profile, "innovation")` to assemble the four canonical sub-dimensions of the Innovation Score (product/tech novelty, market novelty, brand distinctiveness, value-creation novelty) defined in Section 4.
  - Separately returns a brand strength indicator and positioning gaps that feed into the Commercial Offer Score.

### 3.2.5 Axis 05 – Business Model

**Business logic.** This is the financial heart of Moufida. It calculates unit economics (CAC, LTV, payback period), checks if the revenue model can scale, and evaluates funding readiness (runway, burn rate). It produces the financial part of the Scalability Score.

**Technical implementation.**

- **Original `execute` endpoint**: unchanged – generates Business Model Canvas, pricing, financial forecasts, unit economics.
- **`diagnose` endpoint**:
  - Computes the Scalability Score using Affinitree. Sub-dimensions: unit economics (CAC, LTV, payback period), revenue model scalability, funding readiness (runway, burn rate), read from the `finance.*` fields of Table 1.
  - Uses a deterministic financial engine (pure Python) to calculate exact numbers from the profile.
  - Returns the scalability score, component breakdown, and financial blockers (e.g., "negative unit economics", "runway less than 6 months").
- **`metric_update` endpoint**:
  - Receives budget watcher signals (spending thresholds crossed). Re-computes runway and scalability score. If runway becomes critical, it sends an alert.

### 3.2.6 Axis 06 – Legal

**Business logic.** Checks legal compliance (GDPR, AI Act, local Tunisian regulations) and environmental impact. Produces the Green Score, which includes both legal compliance and sustainability practices. Flags missing documents like privacy policies or trademark registrations.

**Technical implementation.**

- **Original `execute` endpoint**: unchanged – generates IP strategy, compliance checklists, legal documents.
- **`diagnose` endpoint**:
  - Computes the Green Score using Affinitree. Sub-dimensions: compliance with GDPR, AI Act, environmental regulations, alignment with SDGs, drawn from the `legal.*` fields of Table 1; the SDG-alignment field is rubric-scored as free text per Section 3.3.3.
  - Returns the green score, component breakdown, and legal blockers (e.g., "missing privacy policy", "no trademark registration").
- **`metric_update` endpoint**:
  - Receives legal radar signals (new regulations published). Updates the compliance checklist and re-computes the green score. Alerts the user if a new legal blocker appears.

### 3.2.7 Axis 07 – Marketing

**Business logic.** Measures marketing readiness: does the entrepreneur have a clear marketing plan, SEO strategy, and social media presence? This feeds into the Market Score.

- **`diagnose` endpoint**: returns a marketing readiness score (used as a secondary input to Market Score).

### 3.2.8 Axis 08 – Sales

**Business logic.** Measures sales readiness: sales funnel, channel strategy, CRM adoption. This contributes to the Scalability Score.

- **`diagnose` endpoint**: returns a sales readiness score (used as a secondary input to Scalability Score).

### 3.2.9 Axis 09 – Operations

**Business logic.** Looks at how the project runs day-to-day. How much manual work is required? Is the supply chain resilient? Are there quality processes? This produces the operational part of the Scalability Score.

**Technical implementation.**

- **Original `execute` endpoint**: unchanged – generates workflow plans, agile/lean recommendations, supply chain plans.
- **`diagnose` endpoint**:
  - Computes the operational part of the Scalability Score using Affinitree. Sub-dimensions: manual dependency (degree of automation), supply chain scalability, quality framework maturity, read from the `ops.*` fields of Table 1.
  - Returns the ops scalability score and operational blockers (e.g., "heavy manual intervention", "no documented SOPs").

### 3.2.10 Axis 10 – Go-to-Market

**Business logic.** This axis is responsible for turning diagnostic results into a concrete action plan. It takes the gaps, blockers, and low scores identified by other axes, searches the Tunisian knowledge base for relevant resources, and uses an LLM to organise them into a timeline: what to do immediately (days), in the short term (weeks), and in the medium term (months).

**Technical implementation.**

- **Original `execute` endpoint**: unchanged – generates launch playbook, beta program, RACI matrix, full startup plan.
- **Roadmap endpoint (new)**:
  - Input: aggregated gaps, blockers, and low scores from the diagnostic pass.
  - For each gap or low sub-score, it formulates a query against the Knowledge Base RAG service (e.g., "customer validation support programme Tunisia"), which is first pre-filtered by maturity stage and score dimension and then retrieved via the metadata-aware hybrid pipeline described in Section 3.5.
  - Retrieves relevant resources (programmes, financing, guides) with source citations.
  - Uses an LLM (Llama 3.1) to order the retrieved resources into a time-horizoned action plan: immediate actions (days), short-term (weeks), medium-term (months). Narration language follows the policy in Section 5.
  - Returns a structured roadmap containing actions, rationales, resource links, and suggested deadlines.
- **`metric_update` endpoint**:
  - Receives milestone completion signals (from Go daemon) and new resource additions to the knowledge base.
  - Regenerates the roadmap to reflect progress and new opportunities.

---

## 3.3 Shared Affinitree Library (Python Module)

**What is Affinitree and why do we need it?** Affinitree is a deterministic scoring engine that uses formulas from academic literature (e.g., OECD, Kotler, Blank) instead of black-box AI. Each of the five composite scores is computed as a weighted sum of sub-dimensions, with weights and citations stored in a JSON file. This makes every score fully explainable: the user can see exactly which sub-dimension contributed how much.

### 3.3.1 Three-tier evidence model

A central design question for Affinitree is what the StartupProfile actually contains and how reliable each of its fields is. If scoring collapsed to a set of self-reported yes/no fields, the outputs would only be as reliable as the entrepreneur's self-assessment – which the diagnostic gap feature implicitly treats as unreliable. We therefore separate declared data from verified signals using a three-tier evidence model.

| Tier | Source | Weight modifier |
|------|--------|-----------------|
| T1 – Declared | Entrepreneur's self-reported answers during intake (boolean, numeric, or ordinal) | × 0.6 |
| T2 – Artefact-backed | Answer is accompanied by an uploaded document, URL, or data extract that the system verifies exists (e.g. a bank statement for revenue, a signed contract for customers) | × 1.0 |
| T3 – Daemon-observed | Signal automatically detected by the Go watcher (e.g. competitor listing, budget crossing a threshold) | × 1.2 |

Each sub-dimension in Affinitree receives a raw value from the profile and a confidence multiplier derived from its evidence tier. The final contribution of a sub-dimension to the composite score is:

```
ci = wi × vi × mi
```

where `wi` is the literature-based weight (stored in the JSON config), `vi` is the normalised raw value ∈ [0, 1], and `mi ∈ {0.6, 1.0, 1.2}` is the confidence multiplier.

### 3.3.2 StartupProfile schema

The table below defines the minimum required fields that Affinitree reads for each of the five composite scores. Fields are typed as: Boolean, Numeric, Enum, or Text (the last being passed to a rubric-scoring LLM call, described in Section 3.3.3).

**Table 1: Affinitree StartupProfile field catalogue**

| Field name | Type | Purpose / sub-score mapped to |
|---|---|---|
| **Market Score (Axis 02)** | | |
| `market.tam_usd` | N | Total Addressable Market in USD – addressable market size |
| `market.sam_usd` | N | Serviceable Addressable Market – addressable market size |
| `market.customer_interviews_count` | N | Number of structured customer interviews conducted |
| `market.paid_pilots_count` | N | Number of paying or letter-of-intent pilot customers |
| `market.nps_score` | N | Net Promoter Score if available, else null |
| `market.revenue_model` | E | {none, usage, subscription, transactional, marketplace} |
| `market.mrr_usd` | N | Monthly Recurring Revenue in USD (0 if pre-revenue) |
| `market.competitor_count` | N | Known direct competitors – competitive intensity |
| `market.competitor_funded_count` | N | Funded competitors – competitive intensity |
| `market.customer_interviews_doc` | B | Artefact: interview notes or transcript uploaded |
| **Commercial Offer Score (Axis 03)** | | |
| `offer.value_prop_text` | T | Free-text description of core value proposition |
| `offer.product_stage` | E | {concept, prototype, mvp, ga, mature} |
| `offer.pricing_model` | E | {undefined, cost-plus, value-based, freemium, other} |
| `offer.price_point_usd` | N | Intended or current price per unit or per month |
| `offer.differentiation_text` | T | Free-text description of competitive differentiation |
| `offer.brand_name_registered` | B | Trademark or brand name legally registered |
| `offer.logo_exists` | B | Visual brand identity exists |
| **Innovation Score (Axis 04, owner; inputs from Axes 01/02)** | | |
| `innovation.tech_readiness_level` | N | TRL 1–9 (NASA/EU scale) |
| `innovation.ip_type` | E | {none, trade-secret, patent-pending, patent-granted, copyright} |
| `innovation.prior_art_search_done` | B | Prior art or competitor technology audit conducted |
| `innovation.novelty_text` | T | Free-text description of what is genuinely new |
| `innovation.sector_first` | B | First-to-market in the identified sector/geography |
| `innovation.brand_distinctiveness_text` | T | Free-text: what makes brand positioning unique |
| **Scalability Score (Axes 05 + 09)** | | |
| `finance.cac_usd` | N | Customer Acquisition Cost in USD |
| `finance.ltv_usd` | N | Lifetime Value per customer in USD |
| `finance.gross_margin_pct` | N | Gross margin percentage |
| `finance.runway_months` | N | Current cash runway in months |
| `finance.burn_rate_usd` | N | Monthly burn rate in USD |
| `finance.funding_stage` | E | {bootstrapped, pre-seed, seed, series-a, series-b-plus} |
| `ops.manual_steps_pct` | N | Estimated % of core operations requiring manual intervention |
| `ops.sop_documented` | B | Standard Operating Procedures documented |
| `ops.supply_chain_single_point` | B | True if single supplier for a critical input |
| **Green Score (Axis 06)** | | |
| `legal.gdpr_policy_exists` | B | Privacy policy compliant with GDPR exists |
| `legal.tunisia_data_law_compliant` | B | Compliant with Tunisian Organic Law 2004-63 |
| `legal.ip_registered` | B | IP rights registered (patent, trademark, or copyright) |
| `legal.sdg_alignment_text` | T | Free-text: alignment with UN Sustainable Development Goals |
| `legal.environmental_impact_assessed` | B | Environmental impact assessment conducted |
| `legal.ai_act_applicable` | B | Product falls under EU AI Act scope |
| `legal.ai_act_compliant` | B | If applicable, conformity assessment completed |

### 3.3.3 Handling free-text fields with rubric scoring

Several fields are typed T (text): value proposition, differentiation, novelty, brand distinctiveness, and SDG alignment. These cannot be scored deterministically. We adopt an LLM-as-judge rubric approach, widely validated in the evaluation literature [1, 2]:

1. A scoring rubric is defined for each text field (0–4 integer scale) with explicit descriptors for each level. The rubric is stored alongside the Affinitree JSON config.
2. Mistral 7B is prompted with the rubric, asked to output a structured JSON object `{"score": int, "evidence_quote": str, "reasoning": str}`.
3. The integer score is normalised to [0, 1] and treated as `vi` with confidence multiplier `mi = 0.6` (tier T1) unless the entrepreneur also uploads a supporting document, in which case `mi = 1.0`.
4. To reduce LLM variance, the same prompt is run twice with different random seeds; if the two scores differ by more than 1, a third run is used and the median is taken.

**Example rubric – value proposition clarity (0–4):**

- **0**: No value proposition stated, or completely generic (e.g. "we improve efficiency").
- **1**: Problem identified but no solution differentiation.
- **2**: Problem and solution stated; customer segment vague.
- **3**: Clear problem, solution, and target segment; benefit quantified partially.
- **4**: Specific problem, measurable benefit, named segment, validated by at least one customer quote or data point.

This hybrid approach preserves Affinitree's deterministic core – the weighted aggregation formula never changes – while handling the inherently qualitative fields through a constrained, rubric-bounded LLM call whose output is logged alongside the final score for full traceability.

**Implementation:**

- **Purpose**: provide explainable, literature-based scoring without hardcoding formulas.
- **Implementation**:
  - Loads a single JSON configuration file at startup. This file contains, for each of the five composite scores, the list of sub-dimensions, their weights, the aggregation method (weighted sum, geometric mean, etc.), and a citation (DOI or URL) for each formula.
  - Exposes a function that takes a StartupProfile and a score name, validates that all required fields are present, applies the formula and confidence multipliers above, and returns a result object.
  - The result object includes the final score (normalised to a 0–5 scale), a list of per-component contributions (each with name, raw value, weight, evidence tier, and contribution), and an internal explanation tree that can be serialised.
- **Use by axes**: Axes 02, 03, 04, 05, 06, and 09 call this library to compute their respective scores. No LLM is involved in the deterministic part of the score calculation – only the bounded rubric calls described above touch free-text fields.
- **Natural-language justification**: after the library returns the score breakdown, the calling axis may optionally invoke a small LLM (e.g., Mistral 7B) to translate the numerical components into a plain-language sentence. This keeps the core scoring traceable while adding readability.

The library is also used to detect anomalies (e.g., high market score without validation evidence) by applying simple rule checks on the input fields; the precision of this anomaly detector is itself measured as part of Tier 2 of the evaluation plan in Section 6.

---

## 3.4 Go Monitoring Daemon

**What problem does it solve?** Entrepreneurs cannot monitor competitors, budget, regulations, and deadlines 24/7. The Go daemon automates this. It is a lightweight, always-running program that scrapes the web, checks thresholds, and publishes any changes to Redis. Because it is written in Go, it uses very little memory (10 MB) and has no dependencies.

**The five watchers:**

- **Budget watcher**: every 6 hours, reads the current spending and budget limit from the profile. If spending reaches 80%, 90%, or 100%, it publishes an alert.
- **Competitor watcher**: every 12 hours, scrapes a list of competitor RSS feeds and web pages. It stores hashes of previous titles and publishes a signal whenever a new article or product appears.
- **Legal radar**: daily, fetches regulatory feeds (e.g., EU AI Act updates, Tunisian official gazette). Filters by keywords (e.g., "GDPR", "Startup Act") and publishes a signal if a new relevant regulation is found.
- **Milestone checker**: every day, compares project milestones against today's date. Publishes alerts at 14, 7, 1, and 0 days before each deadline.
- **Trend scanner**: weekly, counts keyword occurrences in general news feeds (TechCrunch, Wamda, etc.). Compares with the previous week and publishes a signal if a keyword's frequency changes by more than 50%.

**Technical implementation.**

- **Unchanged structure**: a standalone 10 MB binary that runs five concurrent watchers (budget, competitor, legal, milestone, trend). It never uses an LLM – only HTTP scraping, parsing, comparisons, and arithmetic.
- **New output format**: instead of publishing only alerts, it now publishes all metric changes to a Redis channel called `moufida:metrics`. Each message contains the project identifier, the metric type, the new value, and a timestamp.
- **Example messages**:
  - Competitor: `type: competitor, value: {name: "AgriTechPlus", event: "new product launch"}`
  - Budget: `type: budget, value: {spent: 42000, limit: 50000, percentage: 84}`
  - Legal: `type: legal, value: {regulation: "EU AI Act", status: "new draft"}`
  - Milestone: `type: milestone, value: {name: "MVP complete", days_left: 7}`
- **Interaction with axes**: the orchestrator's Redis consumer forwards relevant messages to the appropriate axis's `metric_update` endpoint. This preserves the "liveness" concept because axes react to changes without user intervention.
- **Resource staleness extension**: the same daemon also drives nightly verification of the knowledge base described in Section 3.5, fetching resource source URLs whose `last_verified` date has aged past 90 days and comparing response hashes to detect stale or changed government programmes.

---

## 3.5 Knowledge Base RAG Service (Port 8300)

**Why do we need a separate knowledge base?** Generic LLMs hallucinate program names and invent resources. To provide trustworthy recommendations, Moufida builds a curated vector database of real Tunisian support programmes, financing options, legal guides, and ecosystem actors. Every resource includes a source URL.

**Sizing and taxonomy.** A system that must generate personalised roadmaps across six maturity stages, five scoring dimensions, and multiple sectors (agri-food is explicitly branched in the intake) cannot rely on a flat list of resources without risking very sparse coverage per query cell – a fundraising-stage fintech startup and a market-validation-stage agri-food startup would otherwise retrieve largely the same documents. We therefore decompose the knowledge base along three axes: Maturity Stage, Resource Type, and Sector. Each cell in the matrix defines an independent coverage requirement.

| Taxonomy axis | Values |
|---|---|
| Maturity Stage (6) | Ideation, Market Validation, Structuration, Fundraising, Launch Planning, Growth |
| Resource Type (5) | Financing, Legal/Regulatory, Training/Coaching, Networking/Ecosystem, Technical/Infrastructure |
| Priority Sector (4) | Agri-food, Digital/Tech, Industry/Manufacturing, Cross-sector |

Rather than a flat list, the knowledge base targets at least 2 resources per (Stage × Type) cell, giving a floor of 6 × 5 × 2 = 60 entries before sector specialisation. With sector-specific additions for Agri-food, Digital, and Industry, the practical target is 80–100 resources, collected from official sources: APII, BFPME, BTS, Startup Act, ANPE, incubators, accelerators, bank financing programmes, EU funds, UNDP programmes, legal guides, and administrative procedures. Documents are ingested from PDFs, web pages, and structured lists, and each resource is manually verified for accuracy.

Each resource record in Qdrant carries the following mandatory metadata fields, enabling filtered retrieval:

```json
{
    "id": "apii-startup-act-grant-2024",
    "title": "Startup Act -- Prime à l'Innovation (APII)",
    "type": "financing",
    "stage": ["ideation", "market_validation", "structuration"],
    "sector": ["cross-sector"],
    "score_dimensions": ["innovation", "scalability"],
    "url": "https://www.apii.tn/...",
    "language": "fr",
    "last_verified": "2026-05-01",
    "provider": "APII"
}
```

**Listing 1: Qdrant resource metadata schema**

**Ingestion pipeline.**

- Documents are split into chunks (paragraphs or sections).
- Each chunk is embedded using the `nomic-embed-text` model running on Ollama.
- Embeddings are stored in Qdrant along with the metadata fields above.

**Metadata-filtered hybrid retrieval (`/retrieve`).** Rather than a single hybrid (dense + keyword) search, retrieval is run as a three-step pipeline:

1. **Pre-filter**: restrict the candidate set to resources whose `stage` intersects the diagnosed maturity stage and whose `score_dimensions` intersects the low-score dimensions identified by Affinitree.
2. **Hybrid retrieval**: run dense (nomic-embed-text cosine) and sparse (BM25) retrieval over the filtered candidate set; merge with Reciprocal Rank Fusion (RRF).
3. **Sector boost**: multiply the RRF score by 1.3 for resources whose `sector` matches the entrepreneur's declared sector.

This pipeline ensures that a fundraising-stage fintech startup and a market-validation-stage agri-food startup receive structurally different ranked lists even when their query text is similar, because the pre-filter eliminates irrelevant documents before semantic similarity is computed.

The retrieval endpoint accepts a natural-language query plus optional filters (e.g., `stage = "Market Validation"`, `dimension = "market"`, `type = "financing"`) and returns the top-k chunks with a relevance score, the original source URL, and a human-readable title. The retrieval quality of this pipeline is itself measured against a dedicated benchmark in Tier 3 of Section 6.

**Updatability and staleness control.** Government programmes in Tunisia change frequently. Each resource record includes a `last_verified` date, checked nightly by the Go daemon extension described above; if the response hash differs from the previous check, the resource is flagged as `needs_review` and removed from retrieval until manually re-verified. New resources can also be added via an admin endpoint without rebuilding the whole pipeline or vector index.

**Used by:** Axis 10's roadmap endpoint. Each gap or low score is translated into a query, and the retrieved resources become the basis for recommended actions.

---

## 3.6 Tauri Desktop Application (React + TypeScript)

**What the user sees and hears.** Moufida's frontend is a small, efficient desktop app built with Tauri (Rust + React). It lives in the system tray, appears as an overlay when woken, and includes a full dashboard for the PRD features.

**Technical components.**

- **System tray**: icon, context menu (start new project, diagnose existing project, open settings, quit). The tray icon pulses occasionally when the Go daemon detects a non-urgent update. The settings menu includes the language selector described in Section 5.
- **HUD overlay**: appears when the user says "Wake up Moufida". Contains:
  - Chat panel for voice or text interaction.
  - Review cards for human approval (Approve/Edit/Retry).
  - Alert feed for real-time notifications from Go watchers and score changes.
- **Dashboard view**:
  - Displays the current maturity stage, confidence level, and a collapsible list of evidence points.
  - Shows the five composite scores as gauges or number cards. Each score can be expanded to reveal its sub-score breakdown (per-component contributions, weights, and evidence tiers) and a natural-language explanation.
  - Lists priority blockers with severity badges (critical, warning, info).
  - Displays the roadmap as a timeline: immediate actions (cards), short-term, and medium-term sections. Each action includes a rationale and a clickable link to the source resource.
- **"Mon Parcours" view**:
  - A persistent history screen that shows the evolution of the project over time.
  - Includes a line chart of scores (one line per composite score) with timestamps.
  - Lists past roadmap actions marked as completed, with dates.
  - Shows previous maturity stage assignments and the evidence that led to each change.
  - Fetches data from PostgreSQL via the orchestrator.
- **Voice pipeline integration**:
  - Uses Porcupine for wake word detection ("Hey Moufida").
  - Uses Whisper.cpp – fine-tuned for Tunisian Arabic as described in Section 5 – for speech-to-text transcription of user commands.
  - Uses Piper for French text-to-speech, and the Kokoro-82M Arabic voice for MSA output, as detailed in Section 5.
  - The voice state machine (IDLE → LISTENING → TRANSCRIBING → PROCESSING → SPEAKING) is fully implemented.
- **SSE consumer**: listens to events from the orchestrator:
  - `event: score_update` – refreshes the score widgets.
  - `event: alert` – shows a notification and optionally reads it via TTS.
  - `event: roadmap_update` – refreshes the roadmap timeline.
  - `event: review_ready` – displays a review card.

---

## 3.7 PostgreSQL Database

**Purpose.** Stores all project data permanently. Even if the user restarts their computer, Moufida remembers everything – the profile, scores, roadmap, and history.

**Schema (simplified).**

- Stores the StartupProfile as a JSONB field (flexible schema, following the field catalogue of Table 1) plus relational tables for efficient querying.
- **Tables**:
  - `profiles`: core profile, state (NEW/EXISTING), creation date, last update.
  - `diagnostic_history`: historical entries of maturity stages, blockers, scores, with timestamps.
  - `score_snapshots`: stores each composite score and its component breakdown (including evidence tiers and rubric outputs) at different points in time.
  - `roadmap_versions`: full roadmap JSON for each generation event.
  - `alerts`: log of all alerts sent to the frontend.
- Used by the orchestrator for checkpointing (LangGraph) and by the "Mon Parcours" view for historical data.

---

# 4. Innovation Score Architecture

Among the five composite scores, the Innovation Score is the only one without an obviously single owning axis: contributing signals are spread across ideation (Axis 01), market analysis (Axis 02), and brand identity (Axis 04). Without one orchestration step responsible for assembling these inputs into a coherent score, the result would not be reproducible. We therefore give the Innovation Score an explicit owner, a canonical sub-dimension list, and a defined formula.

## 4.1 Ownership: Axis 04 (Brand Identity)

Axis 04 is the natural owner of the Innovation Score because:

- Innovation in an early-stage startup is predominantly expressed through product novelty and brand/market positioning, not through R&D output metrics (which are more relevant for deep-tech ventures).
- Axis 04 already computes brand novelty and positioning distinctiveness.
- Axes 01 and 02 contribute inputs (TRL, IP status, prior art, competitor count) to the Innovation Score but are not responsible for its aggregation.

Axis 04's `diagnose` endpoint is extended to accept the full StartupProfile (not just the brand-related slice) and to call Affinitree with the `score_name = "innovation"` parameter.

## 4.2 Canonical sub-dimension specification

The Innovation Score is defined as the following weighted sum, drawing on the OECD Oslo Manual (2018) and Hauschildt's degree-of-innovation framework [3, 4]:

```
S_innovation = Σ(i=1 to 4) wi × ci
```

| Sub-dimension | Definition | Weight | Profile field(s) |
|---|---|---|---|
| Product/tech novelty | Degree to which the solution is new (TRL, IP type, prior art) | 35% | `innovation.tech_readiness_level`, `innovation.ip_type`, `innovation.prior_art_search_done` |
| Market novelty | First-mover or re-segmentation position in the identified sector/geography | 25% | `innovation.sector_first`, `market.competitor_count` |
| Brand distinctiveness | Uniqueness of brand positioning relative to competitors (rubric-scored free text) | 20% | `innovation.brand_distinctiveness_text` |
| Value-creation novelty | Degree to which the value proposition addresses an unmet need vs. incremental improvement (rubric-scored) | 20% | `innovation.novelty_text`, `offer.value_prop_text` |

## 4.3 Data flow

The orchestrator's diagnostic pass reflects this ownership as follows:

1. Axes 01, 02, and 03 run their `diagnose` endpoints as before.
2. Axis 04 receives the full aggregated StartupProfile plus the outputs of Axes 01 and 02 (to use competitor count and TRL already computed).
3. Axis 04 calls `Affinitree(profile, "innovation")` and returns the Innovation Score with full sub-dimension breakdown.
4. The orchestrator treats the Innovation Score as owned by Axis 04 in all downstream operations (blocker ranking, RAG query formulation, "Mon Parcours" history).

## 4.4 Affinitree JSON config entry

```json
{
    "score_name": "innovation",
    "owner_axis": 4,
    "aggregation": "weighted_sum",
    "normalise_to": [0, 5],
    "sub_dimensions": [
        {
            "id": "product_novelty",
            "weight": 0.35,
            "inputs": ["innovation.tech_readiness_level",
                       "innovation.ip_type",
                       "innovation.prior_art_search_done"],
            "formula": "trl_normalised * 0.5 + ip_score * 0.35 + prior_art_bonus * 0.15",
            "citation": "OECD Oslo Manual (2018), Chapter 3"
        },
        {
            "id": "market_novelty",
            "weight": 0.25,
            "inputs": ["innovation.sector_first",
                       "market.competitor_count"],
            "formula": "sector_first_score * 0.6 + (1 / (1 + ln(competitor_count + 1))) * 0.4",
            "citation": "Hauschildt (2007), Degree of Innovation"
        },
        {
            "id": "brand_distinctiveness",
            "weight": 0.20,
            "inputs": ["innovation.brand_distinctiveness_text"],
            "formula": "rubric_score / 4",
            "citation": "Rubric v1.0 (Team Moufida, 2026)"
        },
        {
            "id": "value_creation_novelty",
            "weight": 0.20,
            "inputs": ["innovation.novelty_text", "offer.value_prop_text"],
            "formula": "(novelty_rubric + vp_rubric) / 8",
            "citation": "Rubric v1.0 (Team Moufida, 2026)"
        }
    ]
}
```

**Listing 2: Innovation Score config block**
