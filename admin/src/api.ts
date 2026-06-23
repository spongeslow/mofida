import type {
  ApiRequestRow, DaemonActivityRow, HealthResponse, LlmCallRow, TraceResponse,
} from "./types";

const BASE =
  (import.meta as { env?: Record<string, string> }).env?.VITE_API_BASE ||
  "http://localhost:8001";

const TOKEN_KEY = "moufida_admin_token";

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) || "";
}
export function setToken(t: string): void {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function get<T>(path: string): Promise<T> {
  const token = getToken();
  const resp = await fetch(`${BASE}/api/admin${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json() as Promise<T>;
}

export const getHealth = () => get<HealthResponse>("/health");
export const getRequests = (limit = 60, pathPrefix?: string) =>
  get<{ rows: ApiRequestRow[]; count: number }>(
    `/requests?limit=${limit}${pathPrefix ? `&path_prefix=${encodeURIComponent(pathPrefix)}` : ""}`,
  );
export const getTrace = (requestId: string) => get<TraceResponse>(`/trace/${requestId}`);
export const getLlmCalls = (limit = 40, axis?: string) =>
  get<{ rows: LlmCallRow[]; count: number }>(
    `/llm?limit=${limit}${axis ? `&axis=${encodeURIComponent(axis)}` : ""}`,
  );
export const getDaemonActivity = (limit = 100, watcher?: string) =>
  get<{ rows: DaemonActivityRow[]; count: number }>(
    `/daemon/activity?limit=${limit}${watcher ? `&watcher=${encodeURIComponent(watcher)}` : ""}`,
  );

/** SSE URL for the live log stream (token passed as query param). */
export function logStreamUrl(): string {
  const token = getToken();
  return `${BASE}/api/admin/logs/stream${token ? `?token=${encodeURIComponent(token)}` : ""}`;
}
