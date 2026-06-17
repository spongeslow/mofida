# Moufida

## Intelligent Entrepreneurial Orientation Engine

### Full Technical Specification

**Team Makrouna Kadheba** | June 2026

---

## Abstract

This document provides a comprehensive technical specification of Moufida, a voice-first, locally run AI companion for entrepreneurs. It first summarises the mandatory features of the hackathon PRD. Then it describes in detail each component of Moufida – what each service implements, how they interact, and how the overall system satisfies every functional requirement of the PRD. The document explains Moufida's two-state operation (new project creation vs. existing project diagnosis) and preserves its unique "liveness", voice interface, and 100% local execution. Throughout, the specification defines the StartupProfile input schema and evidence-collection strategy for Affinitree scoring, a three-tier evaluation plan covering the maturity classifier, the scoring engine, and the RAG roadmap, a dense, taxonomy-driven Tunisian knowledge base, an explicit ownership and formula for the Innovation Score, and a first-class French/Tunisian-Arabic language pipeline.

---

## Table of Contents

1. [Hackathon PRD – Mandatory Functional Requirements](#1-hackathon-prd--mandatory-functional-requirements)
   - 1.1 Feature 1 – Adaptive Diagnostic Engine
   - 1.2 Feature 2 – Explainable Multi-Dimensional Scoring
   - 1.3 Feature 3 – RAG-Grounded Roadmap & Resource Orientation
   - 1.4 Non-Functional Rules and Prohibitions
2. [Moufida – System Overview and Two-State Operation](#2-moufida--system-overview-and-two-state-operation)
3. Detailed Component Responsibilities (in separate file)
4. Innovation Score Architecture (in separate file)
5. French/Arabic Language Support (in separate file)
6. Evaluation Framework (in separate file)
7. How the Solution Meets Every PRD Functionality (in separate file)
8. Two-State Workflow Summary (in separate file)
9. Conclusion (in separate file)

---

## 1. Hackathon PRD – Mandatory Functional Requirements

The PRD defines three mandatory features that must work together. Below is a distilled list of expected capabilities.

### 1.1 Feature 1 – Adaptive Diagnostic Engine

- **Adaptive structured intake**: a dynamic questionnaire whose questions change based on previous answers (branching logic).
- **Maturity classification**: assign the project to one of six stages – Ideation, Market Validation, Structuration, Fundraising, Launch Planning, Growth – with explicit evidence linking each decision to collected data points.
- **Gap detection**: compare the entrepreneur's self-assessed stage (asked explicitly) with the system's classification; clearly surface any divergence.
- **Blocker identification**: detect and rank priority blockers (financial, legal, market, technical, organisational) and link them to the maturity stage.
- **Diagnostic synthesis**: produce a structured, readable output (not a raw score) that the entrepreneur can act upon.
- **Contextual project memory**: persist the project profile across sessions so that the diagnosis refines over time as new information is added.

### 1.2 Feature 2 – Explainable Multi-Dimensional Scoring

- **Five composite scores**: Market Score, Commercial Offer Score, Innovation Score, Scalability Score, Green Score.
- **Decomposition**: each composite score breaks down into at least three explicit sub-scores with documented weights.
- **Weighted criteria model**: every criterion's contribution to the final score is visible to the user.
- **Natural-language justification**: each score is accompanied by a plain-language explanation of what drove the result.
- **Anomaly detection**: the system flags contradictory or unsubstantiated signals (e.g., high market traction with no validation evidence).
- **Improvement guidance**: for each score, identify the highest-leverage gap and suggest a concrete action to improve it.
- **Score evolution**: as the project profile is updated, scores recalculate and changes are tracked over time.

### 1.3 Feature 3 – RAG-Grounded Roadmap & Resource Orientation

- **Real knowledge base**: documented Tunisian resources (support programmes, financing, legal procedures, ecosystem actors), sized and structured for genuine personalisation rather than a flat minimum count.
- **RAG pipeline**: retrieve relevant resources based on the diagnostic output and scoring profile; every retrieved item must be traceable to its source.
- **Personalised roadmap**: produce an ordered, prioritised action plan with time horizons (immediate, short-term, medium-term).
- **Cross-module coherence**: a diagnostic gap or a low sub-score must trigger retrieval of relevant support resources.
- **Dashboard restitution**: a visual interface presenting maturity level, composite scores with sub-score breakdowns, priority blockers, and the roadmap.
- **"Mon Parcours" tracking view**: a persistent view where the entrepreneur sees their current stage, past recommendations, actions taken, and next steps.
- **Connected conversational assistant**: a secondary layer that answers questions using the diagnostic results, scores, and knowledge base – not generic LLM output.

### 1.4 Non-Functional Rules and Prohibitions

- The solution must not be a standalone chatbot. The diagnostic engine, explainable scoring, and RAG roadmap are mandatory; conversational features are secondary.
- Every output must be traceable and explainable.
- The team must define measurable evaluation metrics and report results on a credibly constructed test set with a defined ground-truth and labelling protocol.
- The primary user context is Tunisia; French and/or Arabic language support is strongly preferred, and must be treated as a first-class architectural concern given the prevalence of code-switched Tunisian dialect (Derja) among the target users.

---

## 2. Moufida – System Overview and Two-State Operation

**What is Moufida?** Moufida (Arabic for "useful") is a desktop application that lives in your computer's system tray. You wake it by saying "Hey Moufida", then give commands by voice. It answers by speaking back. Everything runs on your own machine, no data leaves your computer. It is designed for entrepreneurs in Tunisia but works for any startup founder.

**Key characteristics:**

- **Voice-first**: main interaction is voice (wake word, spoken commands, speech output). Uses Porcupine (wake word), Whisper.cpp (STT), Piper (TTS) – with a Tunisian-Arabic-aware variant of the STT pipeline described in Section 5.
- **100% local**: All AI models (LLMs, embeddings, STT, TTS) run on your hardware via Docker. No cloud APIs.
- **Liveness**: A lightweight Go daemon runs 24/7, watching competitors, budget, legal news, milestones, and trends. Even when the overlay is closed, monitoring continues.
- **Two operation modes**:
  - **STATE_NEW**: Guides you step by step through ten areas of building a startup (from idea to launch). You approve each step.
  - **STATE_EXISTING**: Diagnoses a project you already have, gives scores in five dimensions, and creates a personalised roadmap using real Tunisian resources.

**Two-state operation in detail:**

- **STATE_NEW (Starting a project)**: The entrepreneur builds a startup from scratch. The orchestrator calls the ten axis services in sequence (from Ideation to Go-to-Market), each time using the original `execute` endpoint. After each axis output, a human review card is presented (Approve/Edit/Retry). The full StartupProfile (whose full field catalogue is defined in Section 3.3) is progressively filled.

- **STATE_EXISTING (Diagnosing an existing project)**: The entrepreneur already has a running project. The orchestrator first runs an adaptive intake questionnaire, then calls selected axes in diagnostic mode (a separate endpoint). It aggregates maturity stage, gaps, blockers, and scores, then calls Axis 10 to generate a personalised roadmap. After that, the system remains alive: the Go monitoring daemon continuously feeds real-time signals into the axes, which update scores and the roadmap reactively.

All axis services (ports 8101–8110) retain their original `execute` endpoint for STATE_NEW. For STATE_EXISTING they expose a new `diagnose` endpoint, but no existing functionality is removed or altered.
