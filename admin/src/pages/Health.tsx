import { getHealth } from "../api";
import { C, F, statusColor } from "../theme";
import { usePoll, fmtTime } from "../usePoll";
import type { ServiceHealth } from "../types";
import { PageHeader, TableCard, Pill, ErrorBanner, Loading, tableMono, theadRow, th, td, trBorder } from "../ui";

function MetaRow({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: 12.5, color: C.muted, lineHeight: 1.7 }}>{children}</div>;
}

function ServiceCard({ name, h }: { name: string; h: ServiceHealth }) {
  const status = h.status || (h.alive !== undefined ? (h.alive ? "alive" : "down") : "unknown");
  const color = statusColor(status);
  return (
    <div
      style={{
        background: C.surface, border: `1px solid ${C.border}`, borderRadius: 16,
        padding: "16px 18px", minWidth: 220, flex: "1 1 220px",
        boxShadow: "0 2px 16px rgba(111,78,55,0.07)",
        borderTop: `3px solid ${color}`,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
        <span style={{ fontWeight: 700, fontSize: 14.5, textTransform: "capitalize", color: C.text }}>{name}</span>
        <Pill color={color}>
          <span style={{ width: 7, height: 7, borderRadius: "50%", background: color, display: "inline-block" }} />
          {status}
        </Pill>
      </div>
      <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 2 }}>
        {h.latency_ms !== undefined && <MetaRow>latency: <strong style={{ color: C.text }}>{h.latency_ms} ms</strong></MetaRow>}
        {h.loaded_models && <MetaRow>models: {h.loaded_models.join(", ") || "none"}</MetaRow>}
        {h.collection_count !== undefined && <MetaRow>collections: {h.collection_count} · vectors: {h.total_vectors}</MetaRow>}
        {h.paused !== undefined && <MetaRow>paused: {String(h.paused)}</MetaRow>}
        {h.last_beat && <MetaRow>last beat: {fmtTime(h.last_beat)} ({h.last_beat_age_s}s ago)</MetaRow>}
        {h.focus_project_id && <MetaRow>focus: {h.focus_project_id.slice(0, 8)}…</MetaRow>}
        {h.error && <div style={{ color: C.error, fontSize: 12.5, marginTop: 2 }}>{h.error}</div>}
      </div>
    </div>
  );
}

export function Health() {
  const { data, error } = usePoll(getHealth, 5000);
  if (error) return <ErrorBanner>Failed to load health: {error}</ErrorBanner>;
  if (!data) return <Loading />;

  const kb = data.kb?.collections || {};
  const services = Object.entries(data.services);
  const healthy = services.filter(([, h]) => {
    const s = h.status || (h.alive ? "alive" : "down");
    return s === "ok" || s === "alive";
  }).length;

  return (
    <div style={{ animation: "mf-fade .4s ease both" }}>
      <PageHeader
        eyebrow="System status"
        title="Service Health"
        right={<Pill color={healthy === services.length ? C.success : C.warning}>{healthy}/{services.length} healthy</Pill>}
      />

      <div style={{ display: "flex", flexWrap: "wrap", gap: 14 }}>
        {services.map(([name, h]) => <ServiceCard key={name} name={name} h={h} />)}
      </div>

      <div style={{ marginTop: 30 }}>
        <PageHeader
          eyebrow="Vector store"
          title="Knowledge Base"
          right={<Pill color={C.primary}>{data.kb?.total_vectors ?? 0} vectors</Pill>}
        />
        <TableCard>
          <table style={tableMono}>
            <thead>
              <tr style={theadRow}>
                <th style={th}>Collection</th>
                <th style={th}>Docs</th>
                <th style={th}>Sample titles</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(kb).map(([name, c]) => (
                <tr key={name} className="mf-row" style={trBorder}>
                  <td style={{ ...td, fontWeight: 600, color: C.primary }}>{name}</td>
                  <td style={td}>{c.doc_count}</td>
                  <td style={{ ...td, color: C.muted }}>{c.sample_titles.join(" · ") || "—"}</td>
                </tr>
              ))}
              {Object.keys(kb).length === 0 && (
                <tr style={trBorder}>
                  <td style={{ ...td, color: C.muted, fontFamily: F.body }} colSpan={3}>
                    No collections — run KB ingest.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </TableCard>
      </div>
    </div>
  );
}
