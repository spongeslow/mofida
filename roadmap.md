# Moufida — Roadmap

> The post-hackathon plan for taking Moufida from a working multi-service
> submission to a deployed, trusted, local-first companion for entrepreneurs.
>
> This roadmap is organised into four horizons. **Horizon 0** closes the
> disclosed gaps from the hackathon build; **Horizons 1–3** grow the product
> from a single-founder tool into the diagnostic backbone for entire support
> ecosystems. Items are grounded in the current architecture (`README.md`,
> `technical-pitch.md`, `business-pitch.md`); anything speculative is labelled
> *(exploratory)*.

---

## Guiding Principles (unchanged)

Every item on this roadmap is held to the four commitments that define Moufida:

- **Private by construction** — diagnosis, scoring, and RAG stay 100% local. New
  capabilities default to on-device; any remote edge is named, optional, and off
  by default.
- **Traceable by construction** — every claim cites a real source; every score
  decomposes to `cᵢ = wᵢ × vᵢ × mᵢ`.
- **Explainable by construction** — the Concept Bottleneck stays a first-class
  output, never a black box.
- **Alive by construction** — the daemon keeps the analysis current without user
  action.

A feature that violates one of these does not ship.

---

## Horizon 0 — Close the Hackathon Gaps (0–1 month)

Finish what was openly disclosed as stubbed or pending. This is the credibility
bridge from "demo" to "v1.0".

- [ ] **Compile the LangGraph `StateGraph`** over the existing `MoufidaState`
      TypedDict — replace the implicit orchestration with an explicit, inspectable
      graph.
- [ ] **Harden Axis-10 `/diagnose`** — replace the orchestrator-side RAG stub with
      a first-class diagnose endpoint, matching the other nine axes.
- [ ] **Ship signed desktop builds** — real app icon, code-signed binaries for
      macOS/Windows/Linux, reproducible Tauri release pipeline.
- [ ] **One-command install** — collapse the 6-step setup into a single bootstrap
      script (models, voice assets, KB ingest, Docker stack).

---

## Horizon 1 — Product Hardening & Trust (1–3 months)

Make Moufida something a founder relies on daily, not just demos once.

### Reliability & Performance
- [ ] First-run model warm-up + progress UI (cold Ollama loads are the worst
      first impression).
- [ ] Quantisation/perf tuning so the full diagnosis pipeline runs comfortably on
      8 GB machines, not just 16 GB.
- [ ] Resilience pass on the daemon: crash recovery, watcher backoff, and a
      health self-report surfaced in the companion's state.

### Knowledge Base
- [ ] **Grow the KB beyond 83 resources** — expand Tunisian ecosystem coverage
      (programmes, grants, financing, legal procedures) with a versioned, auditable
      ingest process.
- [ ] **KB freshness automation** — let the daemon's KB-staleness watcher propose
      re-ingests and flag dead source URLs.
- [ ] **User-contributed sources** — drag-and-drop PDF ingest (already supported)
      extended with a review/verify step before a doc counts as evidence.

### Trust & Explainability
- [ ] **CBM calibration loop** — accumulate anonymised, on-device diagnostic
      history to improve concept-weight calibration (`/cbm/calibrate`) without any
      data leaving the machine.
- [ ] **Score-evolution timeline** — visualise how scores moved over time,
      attributing each change to its source (manual edit · chat · tool · daemon).
- [ ] **Exportable diagnostic report** — polished, branded PDF/markdown export of
      the full diagnosis + roadmap, citations intact.

### Voice & Language
- [ ] **Deepen Tunisian Derja support** — move from STT-awareness to first-class
      Derja understanding and TTS.
- [ ] **Full Arabic voice output** (currently FR + EN TTS).

---

## Horizon 2 — From Tool to Platform (3–9 months)

The wedge strategy: a founder's personal advisor becomes the shared diagnostic
layer that support programmes standardise on.

### Multi-Project & Collaboration
- [ ] **Workspace mode** — manage a portfolio of projects (for serial founders and
      small teams), each with its own focused daemon watchers.
- [ ] **Mentor/advisor view** *(exploratory)* — a read-only, consent-gated way to
      share a diagnostic snapshot with a human mentor, preserving the local-first
      default (export, not cloud sync).

### Incubator / Accelerator Edition
- [ ] **Cohort diagnostics** — let a programme run consistent, explainable
      diagnostics across many founders, with aggregate (privacy-preserving)
      insights into where a cohort is weak.
- [ ] **Configurable rubrics** — allow a programme to tune axis weights and
      evidence tiers to their thesis, while keeping the formula transparent.
- [ ] **Benchmarking** — anonymised, opt-in comparison of a startup's scores
      against an ecosystem baseline.

### Integrations
- [ ] Expand the optional Composio integration surface (still off by default,
      still the single named remote edge) — calendars, CRMs, data rooms — feeding
      the evidence pipeline with daemon-observed (1.2×) signals.
- [ ] **Public API / SDK** *(exploratory)* — let third parties build on the
      scoring engine and signal service.

---

## Horizon 3 — New Markets & The Living Analyst (9+ months)

Re-point the engine at new markets by changing data, not code — and push the
"alive" thesis further.

### Geographic & Sector Expansion
- [ ] **Swap-the-KB playbook** — document and tool the process to localise Moufida
      for another Francophone / Arabic-speaking or emerging market by replacing the
      knowledge base and language assets.
- [ ] **Second market pilot** *(exploratory)* — validate the architecture's
      market-portability claim with one new ecosystem.
- [ ] **Sector packs** — verticalised KBs (agritech, fintech, green economy) with
      tuned axis priors.

### Deeper Intelligence
- [ ] **Predictive watchers** — move the daemon from reactive alerts toward
      forward-looking signals (e.g. "this grant deadline pattern repeats quarterly").
- [ ] **Richer interpretability** — expand the Contrastive Axis Directions and CBM
      work; publish follow-up research from `docs/research/`.
- [ ] **Model upgrades** — track and adopt stronger local open models as they
      become viable on consumer hardware, preserving the 100%-local guarantee.

### Sustainability
- [ ] Define a sustainable model that does not compromise local-first / privacy —
      e.g. an institutional (incubator) edition and supported KB curation, with the
      core founder experience remaining free and on-device.

---

## What We Will *Not* Do

To keep the roadmap honest about the moat:

- **No mandatory cloud.** The core analytical pipeline (diagnosis, scoring, RAG)
  will never require sending a founder's data off their machine.
- **No black-box scoring.** We will not adopt any scoring approach we cannot
  decompose to a formula and an evidence tier.
- **No hallucinated resources.** Every roadmap action keeps linking to a real,
  verified source URL.

---

## How This Roadmap Is Maintained

- Horizons shift right as scope is learned; dates are directional, not contractual.
- Items graduate from *(exploratory)* to committed only once validated against the
  four guiding principles.
- Progress against the eval framework (`eval/run-all-evals.sh`) is the objective
  signal for Horizon 0/1 readiness.

*Moufida means "useful." The roadmap is in service of that — nothing ships that
doesn't make the companion more useful, more trustworthy, or more alive.*
