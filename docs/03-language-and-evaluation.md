# 5. French/Arabic Language Support

Tunisian entrepreneurs commonly communicate in a mix of Tunisian Arabic dialect (Derja), French, and occasionally Modern Standard Arabic (MSA). Standard Whisper.cpp achieves Word Error Rates of 50–80%+ on Tunisian Arabic [5, 6], and smaller open-source LLMs (Mistral 7B, Llama 3.1) have significantly weaker Arabic reasoning capabilities than French. Language support is therefore treated not as a UI toggle but as a language-aware pipeline architecture that runs through every layer of the voice pipeline, with French and Tunisian Arabic as first-class processing paths.

## 5.1 Speech-to-Text: Whisper fine-tuned on Tunisian data

Standard Whisper (large-v2 or large-v3) fails on Tunisian Arabic dialect, as demonstrated by LinTO (WER 50–100%) and TuniSpeech-21h evaluations [5, 6]. The solution is a two-step fallback:

1. **Primary**: Whisper large-v2 fine-tuned on the publicly available TuniSpeech-21h corpus [6], which reduces WER to approximately 25% on broadcast speech. This fine-tuned checkpoint (released under Apache-2.0) is bundled with Moufida's Docker image.
2. **Fallback**: If the detected language confidence is low (Whisper's `avg_logprob < -0.5`), the system prompts the user to switch to French and re-transcribes with the standard French Whisper model, which achieves WER < 10% on French.

**Code-switching.** Tunisian speech regularly mixes Arabic and French within a single sentence. Whisper large-v2 handles this better than smaller models; the fine-tuned variant preserves this capability because TuniSpeech-21h includes code-switched segments [7].

## 5.2 Language detection and routing

The orchestrator adds a `lang_detect` step immediately after transcription. We use a lightweight langdetect model (fastText language identification, 2 MB) to classify each utterance as `ar-TN` (Tunisian Arabic), `fr` (French), or `other`. The detected language is attached to every message in the conversation context and is used to route LLM prompts to the appropriate system prompt variant.

## 5.3 LLM prompt localisation

Mistral 7B and Llama 3.1 have strong French capabilities and moderate MSA capability, but limited Tunisian dialect generation ability. We therefore adopt the following policy:

| Layer | Language policy |
|---|---|
| Structured Affinitree scoring | Language-agnostic (numeric computation). No LLM involved. |
| Rubric scoring of text fields | The text field is passed as-is; Mistral 7B can score French and MSA inputs; Derja inputs are first translated to French by a dedicated step (see below). |
| Natural-language justification | Generated in the user's active language (French or MSA). Derja output is not attempted due to model capability gap. |
| Roadmap narration | Generated in French (default) or MSA (user preference). Document titles from the knowledge base are preserved in their original language (mostly French). |
| Voice output (TTS) | Piper with French model (high quality). For Arabic TTS, we use the open-source Kokoro-82M Arabic voice, which supports MSA and produces acceptable quality on short utterances. |

## 5.4 Derja-to-French translation step

For free-text profile fields entered in Tunisian Arabic (Derja), a lightweight translation step is inserted before rubric scoring:

1. The text is detected as `ar-TN` by the language detector.
2. Llama 3.1 8B is prompted with a 5-shot Derja-to-French translation prompt (shots drawn from publicly available TuniFra corpus examples [8]).
3. The French translation is used for rubric scoring.
4. Both the original Derja text and the translated French text are stored in the StartupProfile, so the entrepreneur can verify the translation was correct before the score is accepted.

## 5.5 UI localisation

The Tauri frontend stores all UI strings in a JSON locale file. Two locale files are provided: `fr.json` (French, primary) and `ar.json` (MSA). Right-to-left layout is toggled via a CSS `dir="rtl"` attribute on the root element when Arabic is selected. The system tray language selector persists the choice to the StartupProfile.

**Known limitation.** Generating fluent Tunisian dialect (Derja) text output from Mistral 7B or Llama 3.1 is currently unreliable. Moufida does not attempt Derja output; voice responses and dashboard text are always in French or MSA. This is a deliberate product decision, disclosed to the user in the onboarding flow. As open-source Derja-capable generative models mature (TunBERT's successor projects, Atlas-Chat variants [9]), this constraint can be lifted by swapping the generation model without architectural changes.

---

# 6. Evaluation Framework

Moufida's claim to explainability and traceability depends on credible measurement, not a single weak metric. We define a three-tier evaluation plan covering the three independently testable subsystems: the maturity classifier (Axis 01), the scoring engine (Affinitree), and the RAG roadmap (Axis 10).

## 6.1 Tier 1 – Maturity Classification (Axis 01)

**Ground truth construction.** We construct a labelled benchmark of 50 startup vignettes drawn from three sources: (i) published Tunisian startup case studies from ANAVA and Startup Tunisia; (ii) anonymised real projects provided by at least two partner incubators; (iii) synthetic profiles generated by prompting an LLM different from the one used in production (to avoid evaluation contamination). Each vignette is a structured paragraph of approximately 200 words describing the project state.

**Labelling protocol.** Each vignette is independently labelled by three annotators: one domain expert (entrepreneur or VC analyst with Tunisia context), one team member, and the production Axis 01 model. The gold label is the majority class among the three human annotations. We compute Cohen's κ [11] between the two human annotators to verify rubric clarity; target κ ≥ 0.65 (substantial agreement). Profiles where κ < 0.65 are revised or excluded.

**Metric.** Primary metric is macro-averaged F1 across the six maturity stages (Ideation, Market Validation, Structuration, Fundraising, Launch Planning, Growth). Macro averaging penalises the model for ignoring low-frequency stages. Secondary metric is top-2 accuracy (the correct stage is among the model's top-2 predictions, relevant because adjacent stages are often ambiguous).

**Target:** macro-F1 ≥ 0.65, top-2 accuracy ≥ 0.85.

## 6.2 Tier 2 – Affinitree Scoring Stability

Because Affinitree is deterministic for structured fields and rubric-based for text fields, we evaluate two properties:

- **Determinism test.** For structured-input profiles (no text fields), the same profile run ten times must produce identical scores. This is a unit test, not a statistical evaluation.
- **Text-field stability.** For profiles containing free-text fields, we run the rubric LLM call five times per field and report the standard deviation of the resulting score. Target: σ ≤ 0.15 normalised (i.e., less than 0.6 points on a 0–4 rubric). Fields that exceed this threshold trigger a rubric refinement iteration before the hackathon demo.
- **Anomaly detection precision.** We craft 10 deliberately contradictory profiles (e.g., MRR > 0 with `market.customer_interviews_count = 0`) and verify that the anomaly flag fires on all 10. This is a recall test of the rule engine.

## 6.3 Tier 3 – RAG Retrieval Quality

We construct a retrieval evaluation set of 20 (query, expected-resource) pairs, where the expected resource is a specific entry in the knowledge base that a domain expert judged as the most relevant response to that query. Metrics:

- **Recall@3**: proportion of queries where the expected resource appears in the top-3 retrieved chunks. Target ≥ 0.80.
- **Mean Reciprocal Rank (MRR)**: average of 1/rank of the first relevant result. Target ≥ 0.70.

| Tier | Subsystem | Metric / Target |
|---|---|---|
| T1 | Maturity classifier (Axis 01) | Macro-F1 ≥ 0.65, Top-2 Acc. ≥ 0.85 |
| T2a | Affinitree structured | Determinism: 100% (unit test) |
| T2b | Affinitree text fields | Score std. dev. σ ≤ 0.15 |
| T2c | Anomaly detection | Recall (10 cases) = 100% |
| T3 | RAG retrieval | Recall@3 ≥ 0.80, MRR ≥ 0.70 |

**Reporting.** All evaluation results are reported in a structured results card attached to the hackathon submission. The card records dataset size, labelling protocol, annotator profiles, inter-annotator κ, and the metric value. Where a target is missed, the card includes a diagnosis and the mitigation applied.
