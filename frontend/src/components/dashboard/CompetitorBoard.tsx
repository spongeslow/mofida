/**
 * CompetitorBoard — "You vs each competitor" comparison built from the
 * daemon-fed competitors table. Live-refreshes on `competitor_update` SSE
 * (the consumer bumps `competitorNonce`).
 */
import { useEffect, useState } from "react";
import type React from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { getCompetitors } from "../../api";
import { C, F, card } from "../../theme";
import type { Competitor, CompetitorBoardData } from "../../types";

function priceSummary(c: Competitor): string {
  const tiers = c.pricing?.tiers ?? [];
  if (tiers.length === 0) return "—";
  return tiers
    .slice(0, 3)
    .map((t) => [t.name, t.price].filter(Boolean).join(": "))
    .filter(Boolean)
    .join(" · ") || "—";
}

function fundingSummary(c: Competitor): string {
  const f = c.funding ?? {};
  return [f.stage, f.amount].filter(Boolean).join(" · ") || "—";
}

function SwotCard({ c }: { c: Competitor }) {
  const t = useT();
  const groups: Array<[string, string[] | undefined]> = [
    ["competitor_swot_strengths", c.swot?.strengths],
    ["competitor_swot_weaknesses", c.swot?.weaknesses],
    ["competitor_swot_opportunities", c.swot?.opportunities],
    ["competitor_swot_threats", c.swot?.threats],
  ];
  if (groups.every(([, v]) => !v || v.length === 0)) return null;
  return (
    <div style={{ ...card, padding: "12px 16px" }}>
      <p style={{ margin: "0 0 8px", fontSize: 13, fontWeight: 700, color: C.text, fontFamily: F.body }}>
        {c.name}
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        {groups.map(([key, vals]) => (
          <div key={key}>
            <p style={{ margin: "0 0 2px", fontSize: 10, textTransform: "uppercase",
              letterSpacing: 0.5, color: C.muted, fontWeight: 700 }}>
              {t(key)}
            </p>
            <ul style={{ margin: 0, paddingInlineStart: 16, fontSize: 11, color: C.text, lineHeight: 1.5 }}>
              {(vals ?? []).slice(0, 3).map((v, i) => <li key={i}>{v}</li>)}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

interface Props {
  projectId: string;
}

export function CompetitorBoard({ projectId }: Props) {
  const t = useT();
  const competitorNonce = useStore((s) => s.competitorNonce);
  const [data, setData] = useState<CompetitorBoardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getCompetitors(projectId)
      .then((d) => { if (!cancelled) setData(d); })
      .catch(() => { if (!cancelled) setData(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [projectId, competitorNonce]);

  const competitors = data?.competitors ?? [];
  if (!loading && competitors.length === 0) return null;

  const th: React.CSSProperties = {
    textAlign: "left", padding: "8px 12px", fontSize: 11, color: C.muted,
    fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5,
    borderBottom: `1px solid ${C.border}`,
  };
  const td: React.CSSProperties = {
    padding: "10px 12px", fontSize: 12, color: C.text, verticalAlign: "top",
    borderBottom: `1px solid ${C.border}`,
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <span style={{ fontSize: 12, color: C.muted, fontFamily: F.body,
        textTransform: "uppercase", letterSpacing: 1 }}>
        {t("competitor_board_title")} {loading && "…"}
      </span>

      <div style={{ ...card, padding: 0, overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", width: "100%", minWidth: 520 }}>
          <thead>
            <tr>
              <th style={th}>{t("competitor_dimension")}</th>
              <th style={{ ...th, color: C.accent }}>
                {data?.you?.name ?? t("competitor_you")}
              </th>
              {competitors.map((c) => (
                <th key={c.id} style={th}>{c.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={td}>{t("competitor_positioning")}</td>
              <td style={td}>{data?.you?.positioning || "—"}</td>
              {competitors.map((c) => <td key={c.id} style={td}>{c.positioning || "—"}</td>)}
            </tr>
            <tr>
              <td style={td}>{t("competitor_pricing")}</td>
              <td style={td}>—</td>
              {competitors.map((c) => <td key={c.id} style={td}>{priceSummary(c)}</td>)}
            </tr>
            <tr>
              <td style={td}>{t("competitor_funding")}</td>
              <td style={td}>—</td>
              {competitors.map((c) => <td key={c.id} style={td}>{fundingSummary(c)}</td>)}
            </tr>
          </tbody>
        </table>
      </div>

      {/* SWOT cards per competitor */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {competitors.map((c) => <SwotCard key={c.id} c={c} />)}
      </div>
    </div>
  );
}
