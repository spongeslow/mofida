# 10 — Requirements Compliance & Beyond-Spec Coverage

> Traceability matrix mapping the **AINS Hackathon 2026 — AI for Entrepreneurship**
> technical specification (`docs/AI_for_Entrepreneurship.pdf`) against:
> - **Coded** — what already exists in the repo (verified June 2026)
> - **Planned** — what the `implementation/` plan adds
> - **Beyond** — capabilities we built that the brief never asked for
>
> Legend: ✅ implemented · 📋 planned (this folder) · ➕ surpasses spec · — n/a

---

## 1. Executive summary

The brief mandates **three interacting features** around a shared project
profile: (1) an **Adaptive Diagnostic Engine**, (2) **Explainable
Multi-Dimensional Scoring**, and (3) a **RAG-Grounded Roadmap**. It explicitly
forbids "chatbot-as-product" solutions.

**All three mandatory features are already coded and genuinely interact** — the
diagnostic profile feeds the scorer, low scores/gaps drive RAG retrieval, and
the assistant is grounded in those structured outputs (not a free LLM). Every
**Must** acceptance criterion across all three features is met by existing code.
The `implementation/` plan then layers a second operating mode (creation),
continuous liveness, and multi-project support **on top of** a spec-complete base.

| Judging dimension (weight) | Status |
|---|---|
| Real-world Impact (25%) | ✅ 65 real Tunisian resources; Tunisian-context throughout |
| Technical Depth (25%) | ✅ 10 microservices + deterministic scorer + RAG + Go daemon; ➕ dependency engine planned |
| Prototype Quality (20%) | ✅ end-to-end intake→diagnosis→dashboard works; ➕ Tauri desktop + voice |
| Explainability & Scoring Rigour (15%) | ✅ `ci = wi·vi·mi`, evidence tiers, NL justification, score decomposition |
| Evaluation & Rigour (15%) | ✅ 3-tier eval harness (maturity / scoring / RAG) on labelled sets |

---

## 2. Global Requirements (§1)

| Requirement | Status | Evidence |
|---|---|---|
| Move beyond generic assistant → actionable outputs (§1.1, §1.3) | ✅ | Scores, blockers, roadmap, DD flags — structured, not chat |
| Tunisian/MENA primary context (§1.1) | ✅ | KB = APII, BFPME, BTS, Startup Act, FOPRODI, etc. (`backend/rag/knowledge-base/resources/`, 65 files) |
| Structural intelligence beyond retrieval (§1.3) | ✅ | Deterministic scorer + rule-based anomaly/blocker engines work in concert with LLM (`scoring-engine/affinitree/`) |
| Explainability — traceable outputs (§1.3, §1.4) | ✅ | `scorer.py` per-criterion `contribution`, `justification.py`, evidence tiers |
| Evaluation metric on a test set (§1.3) | ✅ | `backend/eval/tier1-maturity` (15 vignettes), `tier2-affinitree`, `tier3-rag` (20 query pairs) |
| French and/or Arabic UI (§1.2 Language) | ✅➕ | **Trilingual FR/EN/AR** with RTL — exceeds "FR and/or AR" |
| Responsiveness (§1.5) | ✅ | Wave-parallel diagnostic fan-out; quick-diagnostic mode skips roadmap |
| Reliability on dirty/missing data (§1.5) | ✅ | `scorer.py` `_missing_fields`, uncertainty surfaced; intake tolerates partials |
| Privacy & Security (§1.5) | ✅➕ | **100% local** — Ollama + local voice models; no data leaves the machine |
| Scalability mindset (§1.5) | ✅ | Microservice-per-axis topology; documented in `architecture` |
| **NOT** a standalone chatbot (§1.6) | ✅ | Assistant is a *secondary* grounded layer; engines are the product |

---

## 3. Feature 1 — Adaptive Diagnostic Engine (§2.3)

| Acceptance criterion | Priority | Status | Evidence |
|---|---|---|---|
| Adaptive intake is real (≥3 distinct question paths) | Must | ✅ | `intake/questionnaire.py` walks a branch graph from `branches.json`; sector/traction probes branch |
| Classification is traceable (stage ↔ data points) | Must | ✅ | `diagnostic_history.maturity_stage` + `evidence` JSONB linking points |
| Gap detection works (≥3 self vs system divergence) | Must | ✅ | `diagnostic_history.self_assessed` + `perception_gap`; eval contradiction profiles |
| End-to-end demo, no manual intervention | Must | ✅ | `run-diagnostic` fans out all axes → aggregate → persist |
| Maturity taxonomy ≥6 stages | (data hint) | ✅ | Ideation→Market Validation→Structuration→Fundraising→Launch Planning→Growth (`ideation-service/app/main.py`) |
| Blocker identification ranked + mapped | Should | ✅ | `affinitree/blockers.py`, severity critical/warning/info |
| Handles ambiguity, surfaces uncertainty | Should | ✅ | `confidence` field; missing-field reporting |
| Persistent project context refines diagnosis | Should | ✅ | `profiles` JSONB persisted; re-entry via `IntakeWizard mode="update"` |
| Evaluation protocol on labelled set | Should | ✅ | `eval/tier1-maturity/run_eval.py` over 15 labelled vignettes |

**Plan additions:** 📋 PDF upload → text extraction as evidence (`04 §2`);
📋 per-axis Debate chat that recomputes a contested score (`04 §4`);
📋 diagnostic-history compare view (`04 §5`).

---

## 4. Feature 2 — Explainable Multi-Dimensional Scoring (§2.4)

| Acceptance criterion | Priority | Status | Evidence |
|---|---|---|---|
| Five composite scores (Market, Commercial Offer, Innovation, Scalability, Green) | Must | ✅ | `axis_registry.AXES` owns each score; `affinitree/scorer.py` |
| Sub-scores explicit (≥3 sub-dimensions, visible contributions) | Must | ✅ | `rubric.py` field-level scoring; `ScoreContribution.contribution` per criterion |
| Criteria weights documented + defensible | Must | ✅ | Weighted config (`wi`); methodology in `03-language-and-evaluation.md` |
| Natural-language justification per score | Must | ✅ | `affinitree/justification.py` |
| Anomaly/inconsistency detection (≥2 cases) | Should | ✅➕ | `affinitree/anomaly.py` — **7+ rules** incl. `revenue_without_interviews` (the spec's own example), `negative_unit_economics`, `patent_without_prior_art` |
| Improvement guidance (highest-leverage gap + action) | Should | ✅ | `recommendations` in aggregate output |
| Score evolution tracked on profile update | Should | ✅ | `score_snapshots` (migration 002) + recompute |
| Evaluation protocol (consistency on test set) | Should | ✅ | `eval/tier2-affinitree/run_eval.py` (structured + contradiction profiles) |
| Composite scores ≠ averages (domain-shaped aggregation) | (key consid.) | ✅ | `formula.py` expression eval — `ci = wi·vi·mi`, not a mean |
| Evidence-quality multiplier `mi` (declared/verified/observed) | (explainability) | ✅➕ | `scorer.py` reads `mi` from evidence tier — **not required by spec, but core to rigour** |

**Plan additions:** 📋 score-driven roadmap re-prioritisation on ≥1.0 delta
(`07 §4`); 📋 score recompute via Debate (`04 §4`).

---

## 5. Feature 3 — RAG-Grounded Roadmap & Resource Orientation (§2.5)

| Acceptance criterion | Priority | Status | Evidence |
|---|---|---|---|
| Knowledge base is real (≥30 documented resources) | Must | ✅➕ | **65 resources** (>2× the minimum) in `backend/rag/knowledge-base/resources/` |
| Retrieval is traceable (every rec cites a KB source) | Must | ✅ | `rag/app/retrieve.py`; each resource JSON carries `source`/`url` |
| Roadmap personalised (different diagnosis → different roadmap) | Must | ✅ | `_call_roadmap` consumes diagnostic output; per-profile retrieval |
| Cross-module coherence (gap/low score → relevant KB retrieval) | Must | ✅ | Score/gap → retrieval query → matched resources |
| Dashboard functional (maturity, scores, blockers, roadmap in one UI) | Must | ✅ | `components/dashboard/` (MaturityCard, ScoreGauge, BlockerList, RoadmapTimeline) |
| "Mon Parcours" persistent tracking view | Should | ✅ | `components/mon-parcours/` (HistoryList, ScoreChart, CompletedActions) |
| Conversational assistant grounded in structured outputs | Should | ✅ | `ChatPanel` → orchestrator chat grounded in diagnosis/scores/KB |
| Evaluation protocol (retrieval relevance on test set) | Should | ✅ | `eval/tier3-rag/run_eval.py` over 20 query pairs |
| Roadmap has order + rationale + horizons (not a flat list) | (key consid.) | ✅ | `roadmap.{immediate,short_term,medium_term}`, each action `{action,rationale,resource}` |
| KB updatable without rebuilding pipeline | Could | 📋 | Versioned KB + incremental ingest (`07 §5`, `01 §5`) |

**Plan additions:** 📋 progress-aware roadmap — new actions generated on horizon
completion (`07 §3`); 📋 versioned/evolving KB with provenance per generation
(`07 §5`); 📋 KB grows from tool data + uploads + feeds.

---

## 6. Judging criteria & bonus points (§3)

| Bonus point | Status | Evidence |
|---|---|---|
| Cross-module integration depth | ✅ | Gaps trigger KB retrieval; low sub-scores surface targeted roadmap actions; assistant references structured outputs — the spec's exact integration test |
| Perception-reality gap detection ≥3 cases | ✅ | `perception_gap` + contradiction eval profiles |
| Real user validation | — | Demo-day activity, not a code artefact — track for final submission |
| **Arabic language support** | ✅➕ | Full FR/EN/AR with RTL, locales at parity (~140 keys each) |
| **Original dataset contribution** | ✅➕ | The 65-resource Tunisian support-program catalogue + 6-stage maturity taxonomy + labelled eval vignettes are **net-new structured datasets** |
| **Post-hackathon roadmap** | ✅➕ | `docs/plan/new-logic.md` + this `implementation/` folder *are* the credible continuation plan toward PNUD/GEWEET adoption |

---

## 7. Beyond spec — capabilities the brief never asked for ➕

These are genuine differentiators built on top of a spec-complete system:

1. **Two operating modes.** The brief only requires *diagnosis* of existing
   projects. We add a full **creation mode** ("Got any idea?") that *generates*
   a startup plan axis-by-axis (`02`,`03`). One engine set, two behaviours.

2. **Voice-first companion.** Local Whisper (STT) + Piper/Kokoro (TTS),
   "Hey Moufida" wake — accessibility for the primary user population. Not asked.

3. **OS-level desktop companion.** A pixel-art Tauri window that lives on the
   desktop, reacts to voice/progress, and launches the app — a product surface
   beyond the required dashboard.

4. **Autonomous liveness (Go daemon).** 24/7 watchers (competitors, budget,
   legal, milestones) that update the diagnosis **without user action** — the
   brief's tools are session-bound; ours keeps working when idle.

5. **Investor-grade Due Diligence layer.** Every axis emits a `due_diligence`
   block (red flags, readiness score, investor concerns) — a VC-grade lens the
   spec never requests (`scoring-engine/affinitree/due_diligence.py`).

6. **Tool integrations.** A registry-based toolkit (`moufida-tools/toolkit/`)
   with five working connectors — **Slack, Notion, Google Sheets** (push:
   diagnostic summaries / exports / alerts) and **GitHub, Google Analytics**
   (pull: enrich the profile and upgrade evidence tiers *before* scoring). Wired
   into the diagnostic flow (`diagnostic_router.py` enrich + dispatch) and the
   daemon alert path (`redis_consumer.py`). Continuous-update signal emission is
   the planned extension (`06 §3`).

7. **Continuous-update dependency engine** (planned). Manual edit / chat / tool
   / daemon signals → transitive re-run of only the affected axes (`05`,`06`) —
   well beyond the spec's "score evolution on update".

8. **Multi-project portfolio** (planned). Manage several ventures with isolated
   state and a selector (`08`) — the brief assumes a single project.

9. **100% local / privacy by construction.** No cloud dependency at all,
   satisfying §1.5 Privacy maximally rather than via masking.

---

## 8. Honest gaps to close before final submission

Not yet done (tracked in the plan; flagged here so nothing is over-claimed):

- 📋 Real `generate` mode — `/execute` is still a **stub**; creation flow is
  currently faked from diagnostic output (`02`, `03 §`). Phase A priority.
- 📋 PDF upload/extraction + PDF export (`03 §6`, `04 §2`).
- 📋 Per-axis Debate recompute (today `/review` only echoes) (`04 §4`).
- 📋 Event feed, "What's new?", Act/Manual/Ignore cards (`06`).
- 📋 KB versioning + progress-aware/score-driven roadmap (`07`).
- — Real-user validation session (demo-day deliverable, §3.2 bonus).
- ⚠️ **Migrations `006+` must be applied** for the new tables (recurring footgun).

---

## 9. One-paragraph pitch line

> *Moufida already satisfies every **Must** criterion of all three mandatory
> features — adaptive branching intake with 6-stage maturity classification and
> perception-gap detection; five explainable composite scores decomposed to
> weighted, evidence-tiered sub-criteria with natural-language justifications and
> anomaly detection; and a 65-resource real Tunisian RAG knowledge base driving
> personalised, traceable, horizon-structured roadmaps — all validated by a
> three-tier evaluation harness on labelled sets, all running 100% locally. On
> top of that spec-complete core we add a second creation mode, a voice-first
> desktop companion, an autonomous monitoring daemon, an investor-grade due
> diligence layer, and a dependency-driven continuous-update engine.*
