# 7. How the Solution Meets Every PRD Functionality

The following table maps each expected capability from the PRD to the Moufida component that implements it. All descriptions are non-technical and focus on behaviour.

**Table 2: PRD capability → Moufida implementation**

| PRD Capability | Moufida Implementation (Component & Behaviour) |
|---|---|
| Adaptive intake (branching) | Orchestrator's intake endpoint – questions change based on sector, revenue, team size, etc., and populate the typed StartupProfile fields of Table 1. |
| Maturity classification (evidence) | Axis 01's diagnose – LLM assigns stage and lists specific evidence from profile; performance is measured against the 50-vignette benchmark of Tier 1, Section 6. |
| Gap detection | Orchestrator compares user's self-assessed stage (from intake) with Axis 01's output. |
| Blocker identification | Each axis returns domain-specific blockers; orchestrator aggregates and ranks them. |
| Diagnostic synthesis | Orchestrator collects all outputs into a structured JSON summary sent to dashboard. |
| Persistent project memory | PostgreSQL stores all data across sessions; profile is reloaded on wake. |
| 5 composite scores | Axis 02 (Market), Axis 03 (Commercial Offer), Axis 04 (Innovation, with inputs from Axes 01/02), Axes 05/09 (Scalability), Axis 06 (Green). |
| Sub-scores + explicit weights | Affinitree library computes each score using literature-based weights and evidence-tier confidence multipliers; components are returned. |
| Natural-language justification | After Affinitree returns the breakdown, an LLM (or a template) generates a plain-language sentence, in the user's active language per Section 5. |
| Anomaly detection | Affinitree includes rule checks; e.g., high market score with no customer validation → flag. Recall is measured in Tier 2c of Section 6. |
| Improvement guidance | For each low sub-score, the system identifies the highest-weight component and maps it to a recommended action. |
| Score evolution | Score snapshots are stored in PostgreSQL; dashboard shows line chart over time. |
| Real knowledge base | Knowledge Base RAG service ingests 80–100 Tunisian programmes, financing options, and legal guides, structured by the Stage × Type × Sector taxonomy of Section 3.5. |
| Traceable retrieval | Every retrieved resource includes its source URL or document ID in the response. |
| Personalised roadmap | Axis 10's roadmap endpoint uses gaps, blockers, and low scores to query the metadata-filtered RAG pipeline and generate a time-horizoned plan. |
| Cross-module coherence | A diagnostic gap (e.g., "no customer validation") becomes a RAG query; a low market score triggers market-related resources. |
| Dashboard | Tauri UI shows maturity, all five scores (expandable), blockers, and roadmap in one interface. |
| "Mon Parcours" view | Separate UI component reading historical tables from PostgreSQL. |
| Connected conversational assistant | Voice chat is extended with a system prompt that forces answers to reference diagnostic results, scores, or roadmap – never generic LLM output. |
| Not a standalone chatbot | The core product is diagnostic + scoring + roadmap; chat is a secondary interface for commands. |
| Explainability | Affinitree provides traceable score components with evidence tiers; maturity classification includes evidence links. |
| Evaluation metric | Three-tier evaluation plan covering maturity classification, Affinitree stability, and RAG retrieval quality, each with ground-truth construction, target metrics, and a reported results card (Section 6). |
| Tunisian context / Arabic support | Knowledge base contains only Tunisian resources; language-aware pipeline with fine-tuned Tunisian-Arabic Whisper, language detection and routing, Derja-to-French translation, and MSA TTS (Section 5). |

---

# 8. Two-State Workflow Summary

## 8.1 State NEW – Starting a Project

1. The user says "Start new project" or selects the option from the system tray.
2. The orchestrator calls Axis 01 (Ideation) in execute mode. The axis generates brainstorming, feasibility scores, and validation experiments.
3. A review card appears. The user says "Approve", "Edit...", or "Retry because...".
4. Once approved, the data is saved to the StartupProfile.
5. The orchestrator moves to Axis 02 (Market Research) and repeats the process.
6. This continues through all ten axes. The user can skip, reorder, or revisit any axis.
7. At the end, the user has a complete startup plan (10 sections). They can transition to State EXISTING for continuous monitoring.

## 8.2 State EXISTING – First Diagnostic Run

1. The user says "Diagnose my project" or selects the option from the tray.
2. The orchestrator starts the adaptive intake: a voice-driven questionnaire that asks about sector, revenue, team, legal form, self-assessed stage, etc. Questions change based on previous answers, and the spoken input is first routed through the language detection step of Section 5.
3. The answers are stored in the StartupProfile following the field catalogue of Table 1.
4. The orchestrator calls the `diagnose` endpoint on Axes 01, 02, 03, 04, 05, 06, 09, 10.
   - Axis 01 returns a maturity stage (e.g., "Market Validation") with evidence.
   - Axis 02 returns a Market Score and market blockers.
   - Axis 03 returns a Commercial Offer Score and product gaps.
   - Axis 04 returns the Innovation Score, aggregated from its own brand inputs plus the TRL, IP, and competitor data already computed by Axes 01 and 02.
   - Axis 05 returns a Scalability Score and financial blockers.
   - Axis 06 returns a Green Score and legal blockers.
   - Axis 09 returns operational blockers.
5. The orchestrator compares the user's self-assessed stage with the system stage → if different, a "perception gap" is flagged.
6. All blockers are aggregated and ranked by severity (critical, warning, info).
7. The orchestrator calls Axis 10's roadmap endpoint, passing the gaps, blockers, and low scores. Axis 10 queries the Knowledge Base RAG service via the metadata-filtered pipeline of Section 3.5, retrieves relevant Tunisian resources, and generates a personalised action plan with immediate, short-term, and medium-term steps.
8. The dashboard displays the maturity stage, all five scores (with sub-score breakdowns), the ranked blockers, and the roadmap.
9. The user can then ask questions like "Why is my market score low?" – the system answers using the Affinitree breakdown.

## 8.3 State EXISTING – Continuous Liveness (After Diagnosis)

1. The Go daemon continues running 24/7, checking competitors, budget, legal news, milestones, trends, and knowledge-base resource staleness.
2. When the competitor watcher finds a new product launch, it publishes a message to Redis.
3. The orchestrator's Redis consumer forwards the message to Axis 02 (Market Research).
4. Axis 02 re-runs its Affinitree market score with the updated competition data.
5. If the market score drops by more than 0.5 points, Axis 02 pushes an SSE alert to the Tauri frontend.
6. The user sees a notification: "Your Market Score dropped from 3.2 to 2.7 because a direct competitor launched." The TTS reads it aloud in the user's active language.
7. The orchestrator may also automatically trigger Axis 10 to regenerate the roadmap, adding a new action: "Conduct a competitive response workshop using this guide."
8. Similarly, budget watcher signals trigger Axis 05 to update the scalability score and runway; legal radar signals trigger Axis 06 to update the green score and compliance blockers.
9. The dashboard and "Mon Parcours" view always show the latest state, and the user can ask for updates at any time by voice.

---

# 9. Conclusion

Moufida fully satisfies every mandatory and optional requirement of the AINS Hackathon PRD while preserving its original strengths: 100% local execution, voice-first interaction, 24/7 liveness via Go watchers, and a rich set of specialised entrepreneurial axes. The system is built on a fully specified StartupProfile schema with a three-tier evidence model (Section 3.3), an Affinitree-based explainable scoring engine with an explicitly owned and formula-defined Innovation Score (Section 4), a Tunisia-specific RAG knowledge base sized and structured for genuine multi-sector, multi-stage personalisation (Section 3.5), a first-class French/Tunisian-Arabic language pipeline (Section 5), and a three-tier evaluation plan with credible ground truth and reported metrics (Section 6). Taken together, these turn Moufida into a powerful Intelligent Entrepreneurial Orientation Engine that works both for new project creation and for diagnosing existing projects. All formulas are literature-based and not hardcoded, ensuring academic defensibility and easy maintainability. The system is modular, non-redundant, and the original axis services remain unchanged for the STATE_NEW workflow. The two states share the same components, avoiding duplication while offering distinct user journeys.

---

# References

[1] L. Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," NeurIPS, 2023.

[2] Langfuse, "LLM-as-a-Judge," https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge, 2026.

[3] J. Hauschildt and S. Salomo, Innovationsmanagement, 4th ed., Vahlen, 2007.

[4] OECD/Eurostat, Oslo Manual 2018: Guidelines for Collecting, Reporting and Using Data on Innovation, 4th ed., OECD Publishing, 2018.

[5] LinTO Team, "LinTO Audio and Textual Datasets to Train and Evaluate Automatic Speech Recognition in Tunisian Arabic Dialect," arXiv:2504.02604, 2025.

[6] A. Abdallah et al., "A New Tunisian Arabic Corpus and Benchmark for Automatic Speech Recognition (TuniSpeech-21h)," LREC-COLING, 2026.

[7] LinTO Team, "Leveraging Data Collection and Unsupervised Learning for Code-switched Tunisian Arabic ASR," arXiv:2309.11327, 2025.

[8] ACL Anthology, "Arabic Natural Language Processing Conference Proceedings (ArabicNLP 2025)," https://aclanthology.org/events/arabicnlp-2025/, 2025.

[9] MBZUAI-Paris, "Atlas-Chat: Adapting Large Language Models for Low-Resource Moroccan Arabic Dialect," arXiv:2409.17912, 2024.

[10] R. Gebru et al., "Developing a Maturity Assessment Tool for Startups – Bridging Academic Theory and Practical Application," ResearchGate, 2025.

[11] J. Cohen, "A coefficient of agreement for nominal scales," Educational and Psychological Measurement, vol. 20, no. 1, 1960.
