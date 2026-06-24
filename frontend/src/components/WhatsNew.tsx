/**
 * WhatsNew — "What's new?" summary card.
 * Calls GET /project/{id}/whats-new and renders the LLM digest + event list.
 */
import { useEffect, useState } from "react";
import { useT } from "../i18n";
import { getWhatsNew } from "../api";
import { C, F, card, btn } from "../theme";
import type { WhatsNewResult } from "../types";
import { SeverityDot, IconSparkle } from "./shared/icons";

interface Props {
  projectId: string;
  lang: string;
}

export function WhatsNew({ projectId, lang }: Props) {
  const t = useT();
  const [result, setResult]   = useState<WhatsNewResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [since, setSince]     = useState<string | undefined>(undefined);

  const load = (sinceTs?: string) => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    getWhatsNew(projectId, sinceTs, lang)
      .then((r) => {
        setResult(r);
        setSince(new Date().toISOString());
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [projectId, lang]);

  if (!result && !loading && !error) return null;

  return (
    <div style={{ ...card, padding: "16px 20px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <span style={{
          fontSize: 12, color: C.muted, fontFamily: F.body,
          textTransform: "uppercase", letterSpacing: 1, fontWeight: 700,
        }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 7, color: C.accent }}>
            <IconSparkle size={14} /> {t("whats_new_title")}
          </span>
        </span>
        <button
          onClick={() => load(since)}
          disabled={loading}
          style={{ ...btn(false), padding: "4px 10px", fontSize: 11 }}
        >
          {loading ? "…" : t("whats_new_refresh")}
        </button>
      </div>

      {error && (
        <p style={{ color: C.error, fontSize: 13, margin: 0, fontFamily: F.body }}>{error}</p>
      )}

      {loading && !result && (
        <p style={{ color: C.muted, fontSize: 13, margin: 0, fontFamily: F.body }}>
          {t("whats_new_loading")}
        </p>
      )}

      {result && (
        <>
          {/* LLM summary paragraph */}
          {result.summary && (
            <p style={{
              color: C.text, fontSize: 13, fontFamily: F.body, lineHeight: 1.6,
              margin: "0 0 12px", padding: "10px 14px",
              background: `${C.accent}0C`, borderRadius: 10,
              borderLeft: `3px solid ${C.accent}`,
            }}>
              {result.summary}
            </p>
          )}

          {/* Recent events list */}
          {result.events.length === 0 ? (
            <p style={{ color: C.muted, fontSize: 13, margin: 0, fontFamily: F.body }}>
              {t("whats_new_no_events")}
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {result.events.map((ev) => (
                <div key={ev.id} style={{
                  display: "flex", alignItems: "flex-start", gap: 8,
                  padding: "6px 0",
                  borderBottom: `1px solid ${C.border}`,
                }}>
                  <span style={{ flexShrink: 0, marginTop: 3 }}>
                    <SeverityDot sev={ev.severity} size={8} />
                  </span>
                  <div style={{ flex: 1 }}>
                    <span style={{ fontSize: 13, color: C.text, fontFamily: F.body, lineHeight: 1.4 }}>
                      {ev.summary}
                    </span>
                    {ev.axes_affected.length > 0 && (
                      <span style={{ marginLeft: 6, fontSize: 11, color: C.muted, fontFamily: F.body }}>
                        ({ev.axes_affected.join(", ")})
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: 11, color: C.muted, fontFamily: F.body, flexShrink: 0 }}>
                    {new Date(ev.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
