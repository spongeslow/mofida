import type {
  AxisProposal, CloseStrategy, CompareResult, CompetitorBoardData, ConceptScoresResponse,
  DaemonControl, DebateResponse, DiagnosticHistoryEntry, DiagnosticResult, EventRecord,
  IntakeAnswerResponse, IntakeQuestion, InvestorProfile, Opportunity, Persona,
  PersonaChatResponse, PitchReadiness, PitchRespondResponse, PitchStartResponse, PlanSection,
  Project, Roadmap, RoadmapActionStatus, RoadmapProvenance, ScenarioProjection, ScoreSnapshot,
  ToolState, WhatsNewResult,
} from "./types";

const BASE = "http://localhost:8001";

async function post<T>(path: string, body?: unknown): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const resp = await fetch(`${BASE}${path}`);
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json() as Promise<T>;
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json() as Promise<T>;
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json() as Promise<T>;
}

export function createProject(sector: string, language: string): Promise<{ project_id: string }> {
  return post("/api/v1/project/new", { sector, language, profile: {} });
}

export function runDiagnostic(projectId: string, quick = false): Promise<DiagnosticResult> {
  return post(`/api/v1/project/${projectId}/run-diagnostic${quick ? "?quick=true" : ""}`);
}

// Concept Bottleneck breakdown (Phase H, paper 1) — latest per axis.
export function getConceptScores(projectId: string): Promise<ConceptScoresResponse> {
  return get(`/api/v1/project/${projectId}/concept-scores`);
}

// Investor Pitch Simulator (Phase H, H1)
export function pitchStart(projectId: string, investor_profile: InvestorProfile, language: string): Promise<PitchStartResponse> {
  return post(`/api/v1/project/${projectId}/pitch/start`, { investor_profile, language });
}
export function pitchRespond(projectId: string, session_id: string, answer: string, language: string): Promise<PitchRespondResponse> {
  return post(`/api/v1/project/${projectId}/pitch/respond`, { session_id, answer, language });
}
export function pitchEnd(projectId: string, session_id: string, language: string): Promise<PitchReadiness> {
  return post(`/api/v1/project/${projectId}/pitch/end`, { session_id, language });
}

// Customer Persona Simulator (Phase H, H3)
export function generatePersonas(projectId: string, language: string): Promise<{ personas: Persona[] }> {
  return post(`/api/v1/project/${projectId}/personas/generate?language=${language}`);
}
export function getPersonas(projectId: string): Promise<{ personas: Persona[]; count: number }> {
  return get(`/api/v1/project/${projectId}/personas`);
}
export function personaChat(
  projectId: string, personaId: string, message: string,
  history: { role: string; text: string }[], language: string,
): Promise<PersonaChatResponse> {
  return post(`/api/v1/project/${projectId}/persona/${personaId}/chat`, { message, history, language });
}
export function personaCloseStrategy(
  projectId: string, personaId: string,
  history: { role: string; text: string }[], language: string,
): Promise<CloseStrategy> {
  return post(`/api/v1/project/${projectId}/persona/${personaId}/close-strategy`, { history, language });
}

// Pivot Scenario Planner (Phase H, H2)
export function projectScenario(
  projectId: string, label: string, overrides: Record<string, string>, language: string,
): Promise<ScenarioProjection> {
  return post(`/api/v1/project/${projectId}/scenario/project`, { label, overrides, language });
}
export function adoptScenario(projectId: string, label: string): Promise<{ ok: boolean }> {
  return post(`/api/v1/project/${projectId}/scenario/${encodeURIComponent(label)}/adopt`);
}

export function getRoadmap(
  projectId: string,
): Promise<{ roadmap: Roadmap | null; version: number; created_at: string | null }> {
  return get(`/api/v1/project/${projectId}/roadmap`);
}

export function setRoadmapAction(
  projectId: string,
  action: { action_key: string; action_text?: string; horizon?: string; completed: boolean },
): Promise<{ ok: boolean; action_key: string; completed: boolean }> {
  return post(`/api/v1/project/${projectId}/roadmap/action`, action);
}

export function getRoadmapActions(
  projectId: string,
): Promise<{ actions: RoadmapActionStatus[] }> {
  return get(`/api/v1/project/${projectId}/roadmap/actions`);
}

export function chat(
  projectId: string,
  message: string,
  lang: string
): Promise<{ reply: string; detected_lang: string }> {
  return post("/api/v1/chat", { project_id: projectId, message, lang });
}

export function getScoreHistory(
  projectId: string
): Promise<{ snapshots: ScoreSnapshot[] }> {
  return get(`/api/v1/project/${projectId}/history`);
}

export function getDiagnosticHistory(
  projectId: string
): Promise<{ history: DiagnosticHistoryEntry[] }> {
  return get(`/api/v1/project/${projectId}/diagnostic-history`);
}

export function submitReview(
  projectId: string,
  axis: string,
  decision: "approve" | "edit" | "retry",
  edit?: string
): Promise<{ status: string }> {
  return post(`/api/v1/project/${projectId}/review`, { axis, decision, edit });
}

// ---- Tool integrations ----

export function listTools(): Promise<{ tools: ToolState[] }> {
  return get("/api/v1/tools");
}

export function getToolState(slug: string): Promise<ToolState> {
  return get(`/api/v1/tools/${slug}`);
}

export function saveTool(
  slug: string,
  enabled: boolean,
  config: Record<string, unknown>
): Promise<{ saved: boolean; slug: string; enabled: boolean }> {
  return put(`/api/v1/tools/${slug}`, { enabled, config });
}

export function testTool(
  slug: string,
  config: Record<string, unknown>
): Promise<{ ok: boolean; message: string }> {
  return post(`/api/v1/tools/${slug}/test`, { config });
}

export function syncTool(slug: string): Promise<{ synced: boolean; message?: string }> {
  return post(`/api/v1/tools/${slug}/sync`);
}

// ---- Composio managed-OAuth connect flow (Phase G) ----

export function connectTool(slug: string): Promise<{ redirect_url: string; connection_id: string }> {
  return post(`/api/v1/tools/${slug}/connect`);
}

export function getToolConnection(slug: string): Promise<{ connected: boolean; status: string }> {
  return get(`/api/v1/tools/${slug}/connection`);
}

export function disconnectTool(slug: string): Promise<{ slug: string; connected: boolean }> {
  return post(`/api/v1/tools/${slug}/disconnect`);
}

// ---- Intake (stateless: the client carries the full answers map) ----

export function startIntake(language: string): Promise<IntakeQuestion> {
  return post("/api/v1/intake/start", { language });
}

export function answerIntake(
  language: string,
  answers: Record<string, unknown>,
): Promise<IntakeAnswerResponse> {
  return post("/api/v1/intake/answer", { language, answers });
}

export function patchProfile(
  projectId: string,
  profilePatch: Record<string, unknown>,
): Promise<{ project_id: string; profile: Record<string, unknown> }> {
  return patch(`/api/v1/project/${projectId}/profile`, { patch: profilePatch });
}

export function startDiagnoseState(projectId: string): Promise<{ project_id: string; mode: string }> {
  return post(`/api/v1/project/${projectId}/diagnose`);
}

export function getRecentProjects(): Promise<{ projects: Project[] }> {
  return get("/api/v1/projects");
}

// ---- Creation mode (generation loop) ----

export function generateAxis(
  projectId: string,
  axis: string,
  constraints?: string,
): Promise<AxisProposal> {
  return post(`/api/v1/project/${projectId}/generate/${axis}`, { constraints: constraints ?? null });
}

export function approveAxis(
  projectId: string,
  axis: string,
  content: Record<string, unknown>,
  summary?: string,
): Promise<{ project_id: string; axis: string; version: number }> {
  return post(`/api/v1/project/${projectId}/generate/${axis}/approve`, { content, summary });
}

export function retryAxis(
  projectId: string,
  axis: string,
): Promise<AxisProposal> {
  return post(`/api/v1/project/${projectId}/generate/${axis}/retry`);
}

export function getPlan(
  projectId: string,
): Promise<{ project_id: string; sections: PlanSection[] }> {
  return get(`/api/v1/project/${projectId}/plan`);
}

export function finalizeProject(
  projectId: string,
): Promise<{ project_id: string; plan_complete: boolean; roadmap: unknown }> {
  return post(`/api/v1/project/${projectId}/finalize`);
}

// ---- Diagnosis flow additions ----

export function uploadDocument(
  projectId: string,
  file: File,
): Promise<{ project_id: string; filename: string; char_count: number; persisted: boolean; warning: string | null }> {
  const form = new FormData();
  form.append("file", file);
  return fetch(`${BASE}/api/v1/project/${projectId}/documents`, {
    method: "POST",
    body: form,
  }).then((r) => {
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json() as Promise<ReturnType<typeof uploadDocument> extends Promise<infer T> ? T : never>;
  });
}

export function debateAxis(
  projectId: string,
  axis: string,
  message: string,
  language: string,
  history: Array<{ role: string; content: string }>,
): Promise<DebateResponse> {
  return post(`/api/v1/project/${projectId}/axis/${axis}/debate`, { language, message, history });
}

export function compareHistory(
  projectId: string,
  fromIdx = 2,
  toIdx = 1,
): Promise<CompareResult> {
  return get(`/api/v1/project/${projectId}/history/compare?from_idx=${fromIdx}&to_idx=${toIdx}`);
}

export function deleteProject(projectId: string): Promise<{ project_id: string; deleted: boolean }> {
  return fetch(`${BASE}/api/v1/project/${projectId}`, { method: "DELETE" }).then((r) => {
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json() as Promise<{ project_id: string; deleted: boolean }>;
  });
}

// ---- Events feed (continuous updates) ----

export function listEvents(
  projectId: string,
  filters?: { source?: string; axis?: string; severity?: string; status?: string; limit?: number },
): Promise<{ events: EventRecord[] }> {
  const params = new URLSearchParams();
  if (filters?.source)   params.set("source",   filters.source);
  if (filters?.axis)     params.set("axis",      filters.axis);
  if (filters?.severity) params.set("severity",  filters.severity);
  if (filters?.status)   params.set("status",    filters.status);
  if (filters?.limit)    params.set("limit",     String(filters.limit));
  const qs = params.toString() ? `?${params.toString()}` : "";
  return get(`/api/v1/project/${projectId}/events${qs}`);
}

export function editSection(
  projectId: string,
  axis: string,
  content: Record<string, unknown>,
  summary?: string,
): Promise<{ project_id: string; axis: string; version: number; event_id: string; downstream_axes: string[] }> {
  return post(`/api/v1/project/${projectId}/section/${axis}`, { content, summary });
}

export function actOnEvent(eventId: string): Promise<{ event_id: string; status: string; proposals: unknown[] }> {
  return post(`/api/v1/event/${eventId}/act`);
}

export function manualEvent(eventId: string): Promise<{ event_id: string; status: string }> {
  return post(`/api/v1/event/${eventId}/manual`);
}

export function ignoreEvent(eventId: string): Promise<{ event_id: string; status: string }> {
  return post(`/api/v1/event/${eventId}/ignore`);
}

export function getEventDiff(
  eventId: string,
): Promise<{ event_id: string; axes_affected: string[]; summary: string; diff: Record<string, unknown> }> {
  return get(`/api/v1/event/${eventId}/diff`);
}

export function getWhatsNew(
  projectId: string,
  since?: string,
  language?: string,
): Promise<WhatsNewResult> {
  const params = new URLSearchParams();
  if (since)    params.set("since",    since);
  if (language) params.set("language", language);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return get(`/api/v1/project/${projectId}/whats-new${qs}`);
}

// ---- Roadmap engine ----

export function regenerateRoadmap(
  projectId: string,
): Promise<{ project_id: string; version: number; roadmap: unknown }> {
  return post(`/api/v1/project/${projectId}/roadmap/regenerate`);
}

export function advanceRoadmap(
  projectId: string,
  horizon: string,
  completedActions: string[],
): Promise<{ project_id: string; completed_horizon: string; next_horizon: string | null; version: number; roadmap: unknown }> {
  return post(`/api/v1/project/${projectId}/roadmap/advance`, {
    horizon,
    completed_actions: completedActions,
  });
}

export function addKbEntry(
  projectId: string,
  content: string,
  title?: string,
): Promise<{ kb_id: string; kb_version: number }> {
  return post(`/api/v1/project/${projectId}/kb`, { content, title });
}

export function getRoadmapProvenance(projectId: string): Promise<RoadmapProvenance> {
  return get(`/api/v1/project/${projectId}/roadmap/provenance`);
}

// ---- Daemon control plane (Phase F) ----

export function getDaemonControl(): Promise<DaemonControl> {
  return get("/api/v1/daemon/control");
}

export function setDaemonPaused(paused: boolean): Promise<DaemonControl> {
  return post("/api/v1/daemon/control", { paused });
}

export function setDaemonFocus(projectId: string | null): Promise<DaemonControl> {
  return post("/api/v1/daemon/control", projectId
    ? { focus_project_id: projectId }
    : { clear_focus: true });
}

// ---- Competitor board (Phase F2) ----

export function getCompetitors(projectId: string): Promise<CompetitorBoardData> {
  return get(`/api/v1/project/${projectId}/competitors`);
}

// ---- Knowledge Base browser (curated resources) ----

export interface KbResource {
  id: string;
  title: string;
  summary: string;
  body: string;
  type: string | null;
  stage: string[] | null;
  sector: string[] | null;
  score_dimensions: string[] | null;
  provider: string | null;
  url: string | null;
  language: string | null;
  last_verified: string | null;
}

export interface KbResourcesResponse {
  resources: KbResource[];
  count: number;
  taxonomy: unknown;
}

export function getKbResources(): Promise<KbResourcesResponse> {
  return get("/api/v1/kb/resources");
}

// Documents the founder has uploaded into a project's knowledge base (incl. PDFs
// dropped onto the companion). Distinct from the curated `KbResource` library.
export interface ProjectDocument {
  id: string;
  title: string | null;
  char_count: number;
  kb_version: number;
  created_at: string | null;
}

export function getProjectDocuments(
  projectId: string,
): Promise<{ project_id: string; documents: ProjectDocument[] }> {
  return get(`/api/v1/project/${projectId}/documents`);
}

// ---- Watch targets (what the daemon monitors) ----

export interface WatchTargets {
  feeds: { url: string; why?: string }[];
  legal_sources: { name?: string; url: string }[];
  keywords: string[];
  competitors: { name: string }[];
}

export function getWatchTargets(projectId: string): Promise<WatchTargets> {
  return get(`/api/v1/project/${projectId}/watch-targets`);
}

export function refreshWatchTargets(projectId: string): Promise<unknown> {
  return post(`/api/v1/project/${projectId}/watch-targets/refresh`);
}

// ---- Opportunity radar (Phase F3) ----

export function getOpportunities(projectId: string): Promise<{ opportunities: Opportunity[] }> {
  return get(`/api/v1/project/${projectId}/opportunities`);
}

export function dismissOpportunity(
  projectId: string,
  oid: string,
): Promise<{ opportunity_id: string; dismissed: boolean }> {
  return post(`/api/v1/project/${projectId}/opportunity/${oid}/dismiss`);
}

