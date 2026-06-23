export interface ServiceHealth {
  status?: string;
  latency_ms?: number;
  error?: string;
  loaded_models?: string[];
  collection_count?: number;
  total_vectors?: number;
  alive?: boolean;
  paused?: boolean;
  focus_project_id?: string | null;
  last_beat?: string | null;
  last_beat_age_s?: number;
}

export interface KbCollection {
  doc_count: number;
  sample_titles: string[];
}

export interface HealthResponse {
  services: Record<string, ServiceHealth>;
  kb: { collections: Record<string, KbCollection>; total_vectors: number; error?: string };
}

export interface ApiRequestRow {
  request_id: string;
  method: string;
  path: string;
  status_code: number;
  duration_ms: number;
  project_id: string | null;
  created_at: string | null;
}

export interface LlmCallRow {
  id: string;
  request_id: string | null;
  axis: string | null;
  model: string;
  prompt_preview: string;
  response_preview: string | null;
  duration_ms: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
  created_at: string | null;
}

export interface DaemonActivityRow {
  id: string;
  project_id: string | null;
  watcher: string;
  activity: string;
  detail: Record<string, unknown>;
  created_at: string | null;
}

export interface LogEntry {
  ts: string;
  level: string;
  logger: string;
  message: string;
}

export interface TraceResponse {
  request: ApiRequestRow | null;
  llm_calls: LlmCallRow[];
}
