import { create } from "zustand";
import type {
  Alert,
  AxisProposal,
  Blocker,
  ConceptScore,
  DiagnosticResult,
  EventRecord,
  Lang,
  PlanSection,
  Recommendation,
  Review,
  Roadmap,
  ScoreExplanation,
  ToolState,
  View,
  VoiceState,
} from "./types";

interface Store {
  projectId: string | null;
  lang: Lang;
  view: View;
  voiceState: VoiceState;

  // Diagnostic state
  scores: Record<string, number>;
  scoreBreakdowns: Record<string, ScoreExplanation>;
  justifications: Record<string, string>;
  recommendations: Recommendation[];
  maturityStage: string | null;
  selfAssessedStage: string | null;
  perceptionGap: boolean;
  confidence: number;
  evidence: string[];
  blockers: Blocker[];
  roadmap: Roadmap | null;

  // Concept Bottleneck layer (Phase H) — keyed by axis slug
  conceptScores: Record<string, ConceptScore>;
  conceptNonce: number;

  // Live feed
  alerts: Alert[];
  reviews: Review[];

  // Actions
  setProjectId: (id: string) => void;
  clearProject: () => void;
  setLang: (lang: Lang) => void;
  setView: (view: View) => void;
  setVoiceState: (s: VoiceState) => void;
  applyDiagnosticResult: (result: DiagnosticResult) => void;
  setConceptScores: (scores: Record<string, ConceptScore>) => void;
  bumpConcept: () => void;
  applyScoreUpdate: (p: { score_name: string; score: number }) => void;
  applyAlert: (p: { severity: string; title: string; body: string }) => void;
  applyRoadmapUpdate: (p: { roadmap?: Roadmap }) => void;
  applyReviewReady: (p: { axis: string; output: Record<string, unknown> }) => void;
  applyMaturityUpdate: (p: {
    maturity_stage: string;
    self_assessed_stage: string;
    perception_gap: boolean;
  }) => void;
  dismissAlert: (id: string) => void;
  dismissReview: (axis: string) => void;

  // Tools settings
  tools: ToolState[];
  toolsLoading: boolean;
  setTools: (tools: ToolState[]) => void;
  updateTool: (slug: string, patch: Partial<ToolState>) => void;
  setToolsLoading: (loading: boolean) => void;

  // Preferences
  companionVisible: boolean;
  setCompanionVisible: (visible: boolean) => void;

  // Reactive companion mood (Phase 2) — components pulse a transient state that
  // the floating companion plays for a few seconds, then falls back to idle.
  companionPulse: { state: string; nonce: number };
  pulseCompanion: (state: string) => void;

  // Bumped when the knowledge base changes (e.g. a PDF dropped on the
  // companion is ingested) so the KB browser re-fetches uploaded documents.
  kbRefreshNonce: number;
  bumpKbRefresh: () => void;

  // SSE connection status (Phase 3.3) — surfaced as a live/offline indicator.
  sseConnected: boolean;
  setSseConnected: (connected: boolean) => void;

  // Daemon control plane (Phase F)
  daemonPaused: boolean;
  daemonAlive: boolean;
  daemonFocusProjectId: string | null;
  applyDaemonStatus: (p: {
    paused: boolean;
    alive: boolean;
    focus_project_id: string | null;
  }) => void;

  // Phase F live-refresh nonces (SSE bumps → components refetch)
  competitorNonce: number;
  opportunityNonce: number;
  bumpCompetitor: () => void;
  bumpOpportunity: () => void;

  // Cross-component action requests (keyboard shortcuts, companion double-click).
  // Components watch the nonce and act when it increments.
  diagnosticRequest: { nonce: number; quick: boolean };
  requestDiagnostic: (quick: boolean) => void;
  voiceRequest: number;
  requestVoice: () => void;

  // Event feed (continuous updates)
  eventFeed: EventRecord[];
  roadmapStale: boolean;
  horizonCompleteNonce: number;
  applyEventNew: (e: EventRecord) => void;
  updateEventStatus: (id: string, status: EventRecord["status"]) => void;
  setRoadmapStale: (stale: boolean) => void;
  bumpHorizonComplete: () => void;

  // Creation mode state
  projectMode: "creation" | "diagnosis" | null;
  planSections: PlanSection[];
  currentProposal: AxisProposal | null;
  currentAxisIndex: number;
  creationPhase: "idle" | "generating" | "reviewing" | "done";
  setProjectMode: (mode: "creation" | "diagnosis" | null) => void;
  setPlanSections: (sections: PlanSection[]) => void;
  setCurrentProposal: (p: AxisProposal | null) => void;
  setCurrentAxisIndex: (i: number) => void;
  setCreationPhase: (phase: "idle" | "generating" | "reviewing" | "done") => void;
  resetCreationState: () => void;
}

const COMPANION_PREF_KEY = "moufida.companionVisible";
function loadCompanionPref(): boolean {
  try {
    return localStorage.getItem(COMPANION_PREF_KEY) !== "false";
  } catch {
    return true;
  }
}

// Shared across all Tauri windows of the same origin so the standalone companion
// window can read the active project when a PDF is dropped onto it.
const PROJECT_ID_KEY = "moufida.projectId";
function persistProjectId(id: string | null): void {
  try {
    if (id) localStorage.setItem(PROJECT_ID_KEY, id);
    else localStorage.removeItem(PROJECT_ID_KEY);
  } catch { /* ignore */ }
}

export const useStore = create<Store>((set) => ({
  projectId: null,
  lang: "fr",
  view: "dashboard",
  voiceState: "idle",

  scores: {},
  scoreBreakdowns: {},
  justifications: {},
  recommendations: [],
  maturityStage: null,
  selfAssessedStage: null,
  perceptionGap: false,
  confidence: 0,
  evidence: [],
  blockers: [],
  roadmap: null,

  conceptScores: {},
  conceptNonce: 0,

  alerts: [],
  reviews: [],

  tools: [],
  toolsLoading: false,

  setProjectId: (id) => { persistProjectId(id); set({ projectId: id }); },
  clearProject: () => { persistProjectId(null); set({ projectId: null, view: "dashboard" }); },
  setLang: (lang) => set({ lang }),
  setView: (view) => set({ view }),
  setVoiceState: (voiceState) => set({ voiceState }),

  applyDiagnosticResult: (result) =>
    set((s) => ({
      scores: result.scores,
      scoreBreakdowns: result.score_breakdowns,
      justifications: result.justifications ?? {},
      recommendations: result.recommendations ?? [],
      maturityStage: result.maturity_stage,
      selfAssessedStage: result.self_assessed_stage,
      perceptionGap: result.perception_gap,
      confidence: result.confidence ?? 0,
      evidence: result.evidence ?? [],
      blockers: result.blockers,
      roadmap: result.roadmap ?? null,
      // Quick mode omits concept_scores — keep the previous breakdown.
      conceptScores: result.concept_scores ?? s.conceptScores,
    })),

  setConceptScores: (conceptScores) => set({ conceptScores }),
  bumpConcept: () => set((s) => ({ conceptNonce: s.conceptNonce + 1 })),

  applyScoreUpdate: (p) =>
    set((s) => ({ scores: { ...s.scores, [p.score_name]: p.score } })),

  applyAlert: (p) =>
    set((s) => ({
      alerts: [
        ...s.alerts,
        {
          id: crypto.randomUUID(),
          severity: p.severity as Alert["severity"],
          title: p.title,
          body: p.body,
          timestamp: Date.now(),
          dismissed: false,
        },
      ],
    })),

  applyRoadmapUpdate: (p) =>
    set((s) => ({ roadmap: p.roadmap ?? s.roadmap })),

  applyReviewReady: (p) =>
    set((s) => ({
      reviews: [
        ...s.reviews.filter((r) => r.axis !== p.axis),
        { id: crypto.randomUUID(), axis: p.axis, output: p.output },
      ],
    })),

  applyMaturityUpdate: (p) =>
    set({
      maturityStage: p.maturity_stage,
      selfAssessedStage: p.self_assessed_stage,
      perceptionGap: p.perception_gap,
    }),

  dismissAlert: (id) =>
    set((s) => ({
      alerts: s.alerts.map((a) => (a.id === id ? { ...a, dismissed: true } : a)),
    })),

  dismissReview: (axis) =>
    set((s) => ({ reviews: s.reviews.filter((r) => r.axis !== axis) })),

  setTools: (tools) => set({ tools }),
  updateTool: (slug, patch) =>
    set((s) => ({
      tools: s.tools.map((t) => (t.slug === slug ? { ...t, ...patch } : t)),
    })),
  setToolsLoading: (toolsLoading) => set({ toolsLoading }),

  companionVisible: loadCompanionPref(),
  setCompanionVisible: (companionVisible) => {
    try { localStorage.setItem(COMPANION_PREF_KEY, String(companionVisible)); } catch { /* ignore */ }
    set({ companionVisible });
  },

  companionPulse: { state: "idle", nonce: 0 },
  pulseCompanion: (state) =>
    set((s) => ({ companionPulse: { state, nonce: s.companionPulse.nonce + 1 } })),

  kbRefreshNonce: 0,
  bumpKbRefresh: () => set((s) => ({ kbRefreshNonce: s.kbRefreshNonce + 1 })),

  sseConnected: false,
  setSseConnected: (sseConnected) => set({ sseConnected }),

  daemonPaused: false,
  daemonAlive: false,
  daemonFocusProjectId: null,
  applyDaemonStatus: (p) =>
    set({
      daemonPaused: p.paused,
      daemonAlive: p.alive,
      daemonFocusProjectId: p.focus_project_id,
    }),

  competitorNonce: 0,
  opportunityNonce: 0,
  bumpCompetitor: () => set((s) => ({ competitorNonce: s.competitorNonce + 1 })),
  bumpOpportunity: () => set((s) => ({ opportunityNonce: s.opportunityNonce + 1 })),

  diagnosticRequest: { nonce: 0, quick: false },
  requestDiagnostic: (quick) =>
    set((s) => ({ diagnosticRequest: { nonce: s.diagnosticRequest.nonce + 1, quick } })),

  voiceRequest: 0,
  requestVoice: () => set((s) => ({ voiceRequest: s.voiceRequest + 1 })),

  eventFeed: [],
  roadmapStale: false,
  horizonCompleteNonce: 0,
  applyEventNew: (e) =>
    set((s) => ({
      eventFeed: [e, ...s.eventFeed.filter((ev) => ev.id !== e.id)].slice(0, 200),
    })),
  updateEventStatus: (id, status) =>
    set((s) => ({
      eventFeed: s.eventFeed.map((e) => (e.id === id ? { ...e, status } : e)),
    })),
  setRoadmapStale: (roadmapStale) => set({ roadmapStale }),
  bumpHorizonComplete: () =>
    set((s) => ({ horizonCompleteNonce: s.horizonCompleteNonce + 1, roadmapStale: false })),

  projectMode: null,
  planSections: [],
  currentProposal: null,
  currentAxisIndex: 0,
  creationPhase: "idle",
  setProjectMode: (mode) => set({ projectMode: mode }),
  setPlanSections: (planSections) => set({ planSections }),
  setCurrentProposal: (currentProposal) => set({ currentProposal }),
  setCurrentAxisIndex: (currentAxisIndex) => set({ currentAxisIndex }),
  setCreationPhase: (creationPhase) => set({ creationPhase }),
  resetCreationState: () => set({
    planSections: [],
    currentProposal: null,
    currentAxisIndex: 0,
    creationPhase: "idle",
  }),
}));
