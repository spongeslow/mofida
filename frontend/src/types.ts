export type Lang = "fr" | "en" | "ar";
export type View =
  | "dashboard" | "hud" | "parcours" | "settings" | "intake" | "creation"
  | "personas" | "pitch" | "scenarios" | "kb" | "projects";
export type VoiceState = "idle" | "listening" | "transcribing" | "processing" | "speaking";

// Adaptive intake — matches the orchestrator's stateless questionnaire.
export interface IntakeQuestion {
  id: string;
  field: string;
  type: "choice" | "text" | "boolean" | "number";
  choices: string[] | null;
  question: string;
  lang: string;
}

export interface IntakeAnswerResponse {
  done: boolean;
  question?: IntakeQuestion;
  profile_patch?: Record<string, unknown>;
}

export interface RecentProject {
  project_id: string;
  name: string | null;
  sector: string;
  state: string;
  maturity_stage: string | null;
  created_at: string;
}

export interface Blocker {
  axis?: string;
  domain?: string;
  description: string;
  severity: "critical" | "warning" | "info";
}

export interface Alert {
  id: string;
  severity: "critical" | "warning" | "info";
  title: string;
  body: string;
  timestamp: number;
  dismissed: boolean;
}

export interface Review {
  id: string;
  axis: string;
  output: Record<string, unknown>;
}

export interface RoadmapAction {
  action: string;
  rationale?: string;
  source?: string;
  resource?: { title?: string; url?: string };
  horizon?: string;
}

export interface RoadmapHorizons {
  immediate?: RoadmapAction[];
  short_term?: RoadmapAction[];
  medium_term?: RoadmapAction[];
  actions?: Array<RoadmapAction & { horizon?: string }>;
}

// Axis 10 wraps the horizon buckets under a nested `roadmap` key alongside
// metadata; the flat keys are tolerated for forward/backward compatibility.
export interface Roadmap extends RoadmapHorizons {
  stage?: string;
  sector?: string;
  gaps?: string[];
  resources_used?: number;
  roadmap?: RoadmapHorizons;
}

export interface RoadmapActionStatus {
  action_key: string;
  action_text: string | null;
  horizon: string | null;
  completed: boolean;
  completed_at: string;
}

export interface BreakdownComponent {
  name: string;
  weight: number;
  normalised_value: number;
  tier?: string;
  contribution?: number;
}

export interface ScoreExplanation {
  components?: BreakdownComponent[];
  justification?: string;
}

export interface Recommendation {
  score_name: string;
  sub_dimension: string;
  action: string;
  current_value: number;
  weight: number;
  priority: "high" | "medium";
}

export interface ScoreSnapshot {
  score_name: string;
  score: number;
  created_at: string;
}

export interface DiagnosticHistoryEntry {
  maturity_stage: string;
  self_assessed: string | null;
  perception_gap: string | boolean | null;
  confidence: number | null;
  evidence: string[];
  blockers: Blocker[];
  created_at: string;
}

// Tool integration types
export interface ToolConfigField {
  type: "string" | "boolean" | "integer";
  title: string;
  description?: string;
  default?: unknown;
  format?: "uri" | "password" | "textarea";
  minimum?: number;
  maximum?: number;
}

export interface ToolConfigSchema {
  type: "object";
  properties: Record<string, ToolConfigField>;
  required?: string[];
}

export interface ToolState {
  slug: string;
  label: string;
  domain: string;
  direction: "push" | "pull" | "bidirectional";
  enabled: boolean;
  config: Record<string, unknown>;
  config_schema: ToolConfigSchema;
  last_sync_at: string | null;
  last_error: string | null;
}

// ── Shared evidence trace (Phase H, H1–H3 grounding contract) ────
export type EvidenceKind = "axis" | "kb" | "competitor" | "daemon" | "opportunity" | "profile";

export interface EvidenceRef {
  kind?: EvidenceKind;
  label: string;           // source label, e.g. "market axis", "KB"
  field?: string;          // e.g. "validated_customers"
  value?: string;          // e.g. "null"
  doc?: string;            // KB document name
  section?: string;        // KB section reference
  detail?: string;         // free-text detail
}

// ── Investor Pitch Simulator (Phase H, H1) ───────────────────────
export type InvestorProfile = "seed_vc" | "angel" | "impact_fund" | "strategic";

export interface PitchStartResponse {
  session_id: string;
  opening_question: string;
  reasoning: string;
  trace: EvidenceRef[];
}

export interface PitchRespondResponse {
  follow_up_question: string;
  reasoning: string;
  trace: EvidenceRef[];
  answer_quality?: string;
}

export interface AxisReadiness {
  score: number;
  gaps: string[];
}

export interface PitchReadiness {
  overall_readiness: number;
  per_axis_readiness: Record<string, AxisReadiness>;
  hardest_questions: string[];
  recommended_actions: string[];
  evidence_used: EvidenceRef[];
}

export interface PitchTurn {
  role: "investor" | "founder";
  text: string;
  reasoning?: string;
  trace?: EvidenceRef[];
  answer_quality?: string;
}

// ── Pivot Scenario Planner (Phase H, H2) ─────────────────────────
export type Confidence = "high" | "medium" | "low";

export interface AxisProjection {
  current_score: number | null;
  projected_score: number;
  delta: number;
  confidence: Confidence;
  reasoning: string;
  sources: EvidenceRef[];
}

export interface ScenarioProjection {
  label: string;
  overrides: Record<string, string>;
  axis_projections: Record<string, AxisProjection>;
  overall_delta: number;
  generated_at: string;
}

// ── Customer Persona Simulator (Phase H, H3) ─────────────────────
export interface Persona {
  id: string;
  name: string;
  archetype: string;
  age_range?: string;
  region?: string;
  goal?: string;
  budget_range?: string;
  top_objection?: string;
  buying_triggers?: string[];
  source_refs?: Record<string, string>;
}

export interface PersonaClaim {
  claim: string;
  source_ref: string;
}

export interface PersonaChatResponse {
  reply: string;
  claims: PersonaClaim[];
  objection?: string | null;
  buying_signal?: string | null;
}

export interface PersonaChatTurn {
  role: "founder" | "persona";
  text: string;
  claims?: PersonaClaim[];
  objection?: string | null;
  buying_signal?: string | null;
}

export interface CloseStrategy {
  strategy: string;
  key_triggers: string[];
  objections_to_address: string[];
}

// ── Concept Bottleneck layer (Phase H, paper 1) ──────────────────
export interface ConceptBottleneck {
  concept_id: string;
  label?: string;
  current: number;       // 0..1 activation
  weight: number;        // linear-head weight
  score_if_fixed: number; // projected axis score (0..5) if this concept → 0.80
}

export interface ConceptScore {
  axis?: string;
  concepts: Record<string, number>;            // concept_id → 0..1
  cbm_score: number | null;                    // 0..5 from the linear head
  actual_score?: number | null;                // mapped composite axis score
  weighted_contributions?: Record<string, number>;
  bottleneck: ConceptBottleneck | null;
  calibrated: boolean;                         // data-driven weights vs. priors
  labels: Record<string, string>;             // concept_id → human label
}

export interface ConceptScoresResponse {
  project_id: string;
  axes: ConceptScore[];
  count: number;
}

export interface DiagnosticResult {
  project_id: string;
  maturity_stage: string | null;
  self_assessed_stage: string | null;
  perception_gap: boolean;
  confidence?: number;
  evidence?: string[];
  blockers: Blocker[];
  scores: Record<string, number>;
  score_breakdowns: Record<string, ScoreExplanation>;
  justifications?: Record<string, string>;
  recommendations?: Recommendation[];
  roadmap?: Roadmap;
  axis_outputs?: Record<string, Record<string, unknown>>;
  concept_scores?: Record<string, ConceptScore>;
}

// Creation mode — plan sections and generation proposals
export interface PlanSection {
  axis_slug: string;
  version: number;
  content: Record<string, unknown>;
  summary: string | null;
  approved: boolean;
  source: string;
  created_at: string;
}

export interface AxisProposal {
  axis: string;
  mode: string;
  content: Record<string, unknown>;
  summary: string;
  assumptions: string[];
  needs_input: string[];
  error?: string;
}

export interface Project {
  project_id: string;
  name: string | null;
  sector: string;
  state: string;
  mode: "creation" | "diagnosis";
  plan_complete: boolean;
  maturity_stage: string | null;
  created_at: string;
}

export interface DebateResponse {
  reply: string;
  score_changed: boolean;
  new_score: number | null;
  locked: boolean;
  rationale: string;
}

export interface CompareResult {
  project_id: string;
  from: { created_at: string; maturity_stage: string | null };
  to: { created_at: string; maturity_stage: string | null };
  score_deltas: Record<string, { from: number | null; to: number | null; delta: number }>;
  blockers_resolved: Blocker[];
  blockers_new: Blocker[];
}

// Continuous-updates event feed
export interface EventRecord {
  id: string;
  source: "manual" | "chat" | "tool" | "daemon";
  type: string;
  severity: "critical" | "warning" | "info";
  summary: string;
  detail: string | null;
  axes_affected: string[];
  diff: Record<string, unknown>;
  suggestion: Record<string, unknown>;
  status: "new" | "acted" | "manual" | "ignored";
  created_at: string;
}

export interface WhatsNewResult {
  summary: string | null;
  events: Array<{
    id: string;
    severity: string;
    summary: string;
    axes_affected: string[];
    created_at: string;
  }>;
}

// ── Phase F: daemon control + companion ──────────────────────────
export interface DaemonControl {
  paused: boolean;
  alive: boolean;
  last_beat: string | null;
  focus_project_id: string | null;
}

// ── Phase F: competitor analysis board ───────────────────────────
export interface CompetitorPricingTier {
  name?: string;
  price?: string;
  features?: string[];
}

export interface Competitor {
  id: string;
  name: string;
  url: string | null;
  pricing: { tiers?: CompetitorPricingTier[] };
  positioning: string | null;
  funding: { stage?: string; amount?: string; investors?: string[] };
  news: Array<{ headline: string; url: string | null; date: string }>;
  swot: { strengths?: string[]; weaknesses?: string[]; opportunities?: string[]; threats?: string[] };
  updated_at: string;
}

export interface CompetitorBoardData {
  you: { name: string; positioning: string; is_you: true };
  competitors: Competitor[];
}

// ── Phase F: grant / deadline radar ──────────────────────────────
export interface Opportunity {
  id: string;
  title: string;
  source: string;
  url: string | null;
  deadline: string | null;
  match_reason: string | null;
  match_score: number;
  created_at: string;
}

// Roadmap provenance
export interface RoadmapProvenance {
  roadmap_version: number | null;
  kb_version: number | null;
  trigger: string | null;
  generated_at: string | null;
  stale: boolean;
  sources: Array<{ source: string; created_at: string }>;
}
