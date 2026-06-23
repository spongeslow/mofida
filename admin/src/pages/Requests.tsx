import { useEffect, useState } from "react";
import { getRequests, getTrace } from "../api";
import { C, F, mono } from "../theme";
import { usePoll, fmtTime } from "../usePoll";
import type { TraceResponse } from "../types";
import { PageHeader, TableCard, Pill, ErrorBanner, tableMono, theadRow, th, td, trBorder } from "../ui";

function statusColor(code: number): string {
  if (code < 300) return C.success;
  if (code < 500) return C.warning;
  return C.error;
}

function TraceDrawer({ requestId, onClose }: { requestId: string; onClose: () => void }) {
  const [trace, setTrace] = useState<TraceResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getTrace(requestId)
      .then((t) => { if (!cancelled) setTrace(t); })
      .catch((e) => { if (!cancelled) setErr(String(e)); });
    return () => { cancelled = true; };
  }, [requestId]);

  return (
    <>
      <div
        onClick={onClose}
        style={{ position: "fixed", inset: 0, background: "rgba(44,30,23,0.32)", backdropFilter: "blur(2px)", zIndex: 30 }}
      />
      <div
        style={{
          position: "fixed", top: 0, right: 0, bottom: 0, width: 580, background: C.bg,
          borderLeft: `1px solid ${C.border}`, padding: 24, overflowY: "auto", zIndex: 31,
          boxShadow: "-16px 0 48px rgba(44,30,23,0.22)", animation: "mf-slide .28s cubic-bezier(.22,1,.36,1) both",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
          <h3 style={{ margin: 0, fontFamily: F.heading, fontSize: 20, fontWeight: 700, color: C.text }}>Request trace</h3>
          <button onClick={onClose} style={closeBtn}>✕</button>
        </div>
        {err && <ErrorBanner>{err}</ErrorBanner>}
        {!trace && !err && <p style={{ color: C.muted }}>Loading…</p>}
        {trace?.request && (
          <div style={{ fontFamily: mono, fontSize: 12.5 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <Pill color={statusColor(trace.request.status_code)}>
                {trace.request.method} {trace.request.status_code}
              </Pill>
              <span style={{ color: C.muted }}>{trace.request.duration_ms} ms</span>
            </div>
            <div style={{ color: C.text, wordBreak: "break-all", marginTop: 4, fontWeight: 500 }}>{trace.request.path}</div>
            <div style={{ color: C.muted, marginTop: 4 }}>id: {trace.request.request_id}</div>

            <h4 style={{ margin: "22px 0 10px", fontFamily: F.body, fontSize: 13, fontWeight: 700, color: C.primary, letterSpacing: "0.04em", textTransform: "uppercase" }}>
              LLM calls · {trace.llm_calls.length}
            </h4>
            {trace.llm_calls.length === 0 && <p style={{ color: C.muted }}>No LLM calls in this request.</p>}
            {trace.llm_calls.map((c) => (
              <div key={c.id} style={{
                border: `1px solid ${C.border}`, borderRadius: 12, padding: 13, marginBottom: 11,
                background: C.surface,
              }}>
                <div style={{ color: C.accent, fontWeight: 600 }}>
                  {c.axis || "—"} · {c.model} · {c.duration_ms ?? "?"} ms
                  {" · "}in {c.tokens_in ?? "?"} / out {c.tokens_out ?? "?"}
                </div>
                <div style={{ color: C.muted, marginTop: 8, whiteSpace: "pre-wrap" }}>
                  <strong style={{ color: C.text }}>prompt:</strong> {c.prompt_preview}
                </div>
                {c.response_preview && (
                  <div style={{ color: C.muted, marginTop: 8, whiteSpace: "pre-wrap" }}>
                    <strong style={{ color: C.text }}>response:</strong> {c.response_preview}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      <style>{`@keyframes mf-slide { from { transform: translateX(24px); opacity: .6; } to { transform: translateX(0); opacity: 1; } }`}</style>
    </>
  );
}

export function Requests() {
  const [traceId, setTraceId] = useState<string | null>(null);
  const { data, error } = usePoll(() => getRequests(80), 4000);

  return (
    <div style={{ animation: "mf-fade .4s ease both" }}>
      <PageHeader
        eyebrow="HTTP traffic"
        title="Requests"
        right={data && <Pill color={C.primary}>{data.rows.length} recent</Pill>}
      />
      {error && <ErrorBanner>{error}</ErrorBanner>}
      <TableCard>
        <table style={tableMono}>
          <thead>
            <tr style={theadRow}>
              <th style={th}>Method</th><th style={th}>Path</th><th style={th}>Status</th>
              <th style={th}>Duration</th><th style={th}>Time</th><th style={th}></th>
            </tr>
          </thead>
          <tbody>
            {(data?.rows || []).map((r) => (
              <tr key={r.request_id + (r.created_at || "")} className="mf-row" style={trBorder}>
                <td style={{ ...td, fontWeight: 600, color: C.primary }}>{r.method}</td>
                <td style={{ ...td, maxWidth: 320, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                    title={r.path}>{r.path}</td>
                <td style={td}><Pill color={statusColor(r.status_code)}>{r.status_code}</Pill></td>
                <td style={td}>{r.duration_ms} ms</td>
                <td style={{ ...td, color: C.muted }}>{fmtTime(r.created_at)}</td>
                <td style={td}>
                  <button onClick={() => setTraceId(r.request_id)} style={traceBtn}>Trace →</button>
                </td>
              </tr>
            ))}
            {(data?.rows || []).length === 0 && (
              <tr style={trBorder}><td colSpan={6} style={{ ...td, color: C.muted, fontFamily: F.body }}>No requests yet.</td></tr>
            )}
          </tbody>
        </table>
      </TableCard>
      {traceId && <TraceDrawer requestId={traceId} onClose={() => setTraceId(null)} />}
    </div>
  );
}

const traceBtn: React.CSSProperties = {
  background: "transparent", color: C.accent, border: `1.5px solid ${C.border}`,
  borderRadius: 8, padding: "4px 12px", cursor: "pointer", fontSize: 12, fontWeight: 600,
  fontFamily: F.body,
};
const closeBtn: React.CSSProperties = {
  background: C.surface, color: C.muted, border: `1px solid ${C.border}`,
  borderRadius: 9, width: 34, height: 34, cursor: "pointer", fontSize: 14, lineHeight: 1,
};
