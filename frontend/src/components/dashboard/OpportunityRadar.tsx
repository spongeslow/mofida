/**
 * OpportunityRadar — funding/grant cards sorted by deadline, with urgency
 * colouring when the apply-by date is within 14 days. Live-refreshes on
 * `opportunity_new` SSE (the consumer bumps `opportunityNonce`).
 */
import { useEffect, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { dismissOpportunity, getOpportunities } from "../../api";
import { C, F, card, btn } from "../../theme";
import type { Opportunity } from "../../types";

async function openUrl(url: string) {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("open_url", { url });
  } catch {
    window.open(url, "_blank", "noopener,noreferrer");
  }
}

function daysUntil(deadline: string | null): number | null {
  if (!deadline) return null;
  const ms = new Date(deadline).getTime() - Date.now();
  return Math.ceil(ms / (1000 * 60 * 60 * 24));
}

function OpportunityCard({ o, onDismiss }: { o: Opportunity; onDismiss: (id: string) => void }) {
  const t = useT();
  const [busy, setBusy] = useState(false);
  const days = daysUntil(o.deadline);
  const urgent = days !== null && days <= 14;
  const accent = urgent ? C.error : C.accent;

  const handleDismiss = async () => {
    setBusy(true);
    try { onDismiss(o.id); } finally { setBusy(false); }
  };

  return (
    <div style={{ ...card, padding: "14px 18px", borderLeft: `3px solid ${accent}` }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          <p style={{ margin: "0 0 4px", fontSize: 13, fontWeight: 700, color: C.text, fontFamily: F.body }}>
            {o.title}
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5,
              color: C.muted, fontWeight: 700 }}>
              {o.source}
            </span>
            {o.deadline && (
              <span style={{ fontSize: 11, color: accent, fontWeight: 600 }}>
                {t("opportunity_deadline")}: {new Date(o.deadline).toLocaleDateString()}
                {days !== null && days >= 0 && ` (${days}j)`}
              </span>
            )}
            <span style={{ fontSize: 10, color: C.muted }}>
              {t("opportunity_match")}: {Math.round(o.match_score * 100)}%
            </span>
          </div>
          {o.match_reason && (
            <p style={{ margin: "6px 0 0", fontSize: 12, color: C.muted, fontFamily: F.body, lineHeight: 1.5 }}>
              {o.match_reason}
            </p>
          )}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, flexShrink: 0 }}>
          {o.url && (
            <button onClick={() => { void openUrl(o.url as string); }}
              style={{ ...btn(true), padding: "5px 12px", fontSize: 12 }}>
              {t("opportunity_apply")} ↗
            </button>
          )}
          <button onClick={() => { void handleDismiss(); }} disabled={busy}
            style={{ ...btn(false), padding: "5px 12px", fontSize: 12 }}>
            {t("opportunity_dismiss")}
          </button>
        </div>
      </div>
    </div>
  );
}

interface Props {
  projectId: string;
}

export function OpportunityRadar({ projectId }: Props) {
  const t = useT();
  const opportunityNonce = useStore((s) => s.opportunityNonce);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getOpportunities(projectId)
      .then((r) => { if (!cancelled) setOpportunities(r.opportunities); })
      .catch(() => { if (!cancelled) setOpportunities([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [projectId, opportunityNonce]);

  const handleDismiss = (id: string) => {
    setOpportunities((prev) => prev.filter((o) => o.id !== id));
    void dismissOpportunity(projectId, id).catch(() => {});
  };

  if (!loading && opportunities.length === 0) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <span style={{ fontSize: 12, color: C.muted, fontFamily: F.body,
        textTransform: "uppercase", letterSpacing: 1 }}>
        {t("opportunity_radar_title")} {loading && "…"}
      </span>
      {opportunities.map((o) => (
        <OpportunityCard key={o.id} o={o} onDismiss={handleDismiss} />
      ))}
    </div>
  );
}
