import { useStore } from "../../store";
import { useT } from "../../i18n";
import { C, F, card } from "../../theme";

const SCORE_LABELS: Record<string, string> = {
  market: "score_market",
  commercial_offer: "score_commercial_offer",
  innovation: "score_innovation",
  scalability: "score_scalability",
  green: "score_green",
};

export function RecommendationsCard() {
  const t               = useT();
  const recommendations = useStore((s) => s.recommendations);

  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div style={card}>
      <p style={{ color: C.muted, fontSize: 12, margin: "0 0 16px", textTransform: "uppercase", letterSpacing: 1 }}>
        {t("recommendations_title")}
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {recommendations.map((r, i) => {
          const high = r.priority === "high";
          const accent = high ? C.accent : C.muted;
          return (
            <div key={i} style={{
              display:      "flex",
              gap:           12,
              padding:      "12px 14px",
              borderRadius:  10,
              background:    C.surfaceHigh,
              borderLeft:    `3px solid ${accent}`,
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: 0.5, fontFamily: F.body }}>
                    {t(SCORE_LABELS[r.score_name] ?? r.score_name)}
                  </span>
                  <span style={{
                    fontSize: 10, fontWeight: 600,
                    color: high ? "#fff" : C.muted,
                    background: high ? C.accent : "transparent",
                    border: high ? "none" : `1px solid ${C.border}`,
                    borderRadius: 20, padding: "1px 8px",
                  }}>
                    {high ? t("recommendation_priority_high") : t("recommendation_priority_medium")}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: 14, color: C.text, lineHeight: 1.5, fontFamily: F.body }}>
                  {r.action}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
