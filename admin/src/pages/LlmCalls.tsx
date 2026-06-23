import { Fragment, useState } from "react";
import { getLlmCalls } from "../api";
import { C, F } from "../theme";
import { usePoll, fmtTime } from "../usePoll";
import type { LlmCallRow } from "../types";
import { PageHeader, TableCard, Pill, ErrorBanner, tableMono, theadRow, th, td, trBorder } from "../ui";

export function LlmCalls() {
  const [open, setOpen] = useState<string | null>(null);
  const { data, error } = usePoll(() => getLlmCalls(60), 4000);

  return (
    <div style={{ animation: "mf-fade .4s ease both" }}>
      <PageHeader
        eyebrow="Model traffic"
        title="LLM Calls"
        right={data && <Pill color={C.primary}>{data.rows.length} recent</Pill>}
      />
      {error && <ErrorBanner>{error}</ErrorBanner>}
      <TableCard>
        <table style={tableMono}>
          <thead>
            <tr style={theadRow}>
              <th style={th}>Time</th><th style={th}>Axis</th><th style={th}>Model</th>
              <th style={th}>In</th><th style={th}>Out</th><th style={th}>Duration</th><th style={th}>Preview</th>
            </tr>
          </thead>
          <tbody>
            {(data?.rows || []).map((r: LlmCallRow) => (
              <Fragment key={r.id}>
                <tr onClick={() => setOpen(open === r.id ? null : r.id)}
                    className="mf-row"
                    style={{ ...trBorder, cursor: "pointer", background: open === r.id ? "rgba(111,78,55,0.05)" : undefined }}>
                  <td style={{ ...td, color: C.muted }}>{fmtTime(r.created_at)}</td>
                  <td style={td}>{r.axis ? <Pill color={C.accent}>{r.axis}</Pill> : <span style={{ color: C.muted }}>—</span>}</td>
                  <td style={{ ...td, fontWeight: 600, color: C.primary }}>{r.model}</td>
                  <td style={td}>{r.tokens_in ?? "—"}</td>
                  <td style={td}>{r.tokens_out ?? "—"}</td>
                  <td style={td}>{r.duration_ms ?? "—"} ms</td>
                  <td style={{ ...td, color: C.muted, maxWidth: 280, overflow: "hidden",
                               textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.prompt_preview}</td>
                </tr>
                {open === r.id && (
                  <tr style={trBorder}>
                    <td colSpan={7} style={{ padding: 0 }}>
                      <div style={{ background: C.surfaceHigh, padding: "14px 18px", borderLeft: `3px solid ${C.accent}` }}>
                        <div style={{ whiteSpace: "pre-wrap", color: C.muted, fontSize: 12.5 }}>
                          <strong style={{ color: C.text }}>prompt:</strong> {r.prompt_preview}
                        </div>
                        {r.response_preview && (
                          <div style={{ whiteSpace: "pre-wrap", color: C.muted, marginTop: 8, fontSize: 12.5 }}>
                            <strong style={{ color: C.text }}>response:</strong> {r.response_preview}
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
            {(data?.rows || []).length === 0 && (
              <tr style={trBorder}><td colSpan={7} style={{ ...td, color: C.muted, fontFamily: F.body }}>No LLM calls yet.</td></tr>
            )}
          </tbody>
        </table>
      </TableCard>
    </div>
  );
}
