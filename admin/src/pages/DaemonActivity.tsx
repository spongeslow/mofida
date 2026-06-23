import { getDaemonActivity } from "../api";
import { C, F } from "../theme";
import { usePoll, fmtTime } from "../usePoll";
import { PageHeader, TableCard, Pill, ErrorBanner, tableMono, theadRow, th, td, trBorder } from "../ui";

export function DaemonActivity() {
  const { data, error } = usePoll(() => getDaemonActivity(120), 5000);

  return (
    <div style={{ animation: "mf-fade .4s ease both" }}>
      <PageHeader
        eyebrow="Background workers"
        title="Daemon Activity"
        right={data && <Pill color={C.primary}>{data.rows.length} events</Pill>}
      />
      {error && <ErrorBanner>{error}</ErrorBanner>}
      <TableCard>
        <table style={tableMono}>
          <thead>
            <tr style={theadRow}>
              <th style={th}>Time</th><th style={th}>Watcher</th><th style={th}>Activity</th><th style={th}>Detail</th>
            </tr>
          </thead>
          <tbody>
            {(data?.rows || []).map((r) => (
              <tr key={r.id} className="mf-row" style={trBorder}>
                <td style={{ ...td, color: C.muted }}>{fmtTime(r.created_at)}</td>
                <td style={td}><Pill color={C.accent}>{r.watcher}</Pill></td>
                <td style={{ ...td, fontWeight: 600, color: C.primary }}>{r.activity}</td>
                <td style={{ ...td, color: C.muted, maxWidth: 420, overflow: "hidden",
                             textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                    title={JSON.stringify(r.detail)}>
                  {JSON.stringify(r.detail)}
                </td>
              </tr>
            ))}
            {(data?.rows || []).length === 0 && (
              <tr style={trBorder}><td colSpan={4} style={{ ...td, color: C.muted, fontFamily: F.body }}>No daemon activity yet.</td></tr>
            )}
          </tbody>
        </table>
      </TableCard>
    </div>
  );
}
