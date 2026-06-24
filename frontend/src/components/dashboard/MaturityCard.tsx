import { useStore } from "../../store";
import { useT } from "../../i18n";
import { C, STAGE_COLORS, card } from "../../theme";
import { IconWarn } from "../shared/icons";

// Ordered maturity ladder — drives the "level" progression track (Phase 5).
const STAGE_ORDER = [
  "Ideation", "Market Validation", "Structuration",
  "Fundraising", "Launch Planning", "Growth",
];

function StageLadder({ current }: { current: string }) {
  const t = useT();
  const idx = STAGE_ORDER.indexOf(current);
  const next = idx >= 0 && idx < STAGE_ORDER.length - 1 ? STAGE_ORDER[idx + 1] : null;
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", gap: 4, marginBottom: 6 }}>
        {STAGE_ORDER.map((stage, i) => {
          const reached = idx >= 0 && i <= idx;
          const isCurrent = i === idx;
          return (
            <div key={stage} title={stage} style={{
              flex: 1, height: 7, borderRadius: 4,
              background: reached ? (STAGE_COLORS[current] ?? C.primary) : C.border,
              opacity: reached ? (isCurrent ? 1 : 0.55) : 1,
              transition: "background 0.4s ease, opacity 0.4s ease",
            }} />
          );
        })}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: C.muted }}>
        <span>{idx >= 0 ? `${idx + 1} / ${STAGE_ORDER.length}` : "—"}</span>
        {next && <span>{t("maturity_next")}: <strong style={{ color: C.text }}>{next}</strong></span>}
      </div>
    </div>
  );
}

export function MaturityCard() {
  const t = useT();
  const maturityStage     = useStore((s) => s.maturityStage);
  const selfAssessedStage = useStore((s) => s.selfAssessedStage);
  const perceptionGap     = useStore((s) => s.perceptionGap);
  const confidence        = useStore((s) => s.confidence);
  const evidence          = useStore((s) => s.evidence);

  if (!maturityStage) {
    return (
      <div style={card}>
        <p style={{ color: C.muted, margin: 0 }}>{t("no_diagnostic")}</p>
      </div>
    );
  }

  const stageColor = STAGE_COLORS[maturityStage] ?? C.primary;

  return (
    <div style={card}>
      <p style={{ color: C.muted, fontSize: 12, margin: "0 0 8px", textTransform: "uppercase", letterSpacing: 1 }}>
        {t("maturity_stage")}
      </p>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <span style={{
          background: stageColor,
          color: "#fff",
          borderRadius: 20,
          padding: "4px 14px",
          fontSize: 14,
          fontWeight: 600,
        }}>
          {maturityStage}
        </span>
        {confidence > 0 && (
          <span style={{ color: C.muted, fontSize: 13 }}>
            {Math.round(confidence * 100)}% {t("confidence")}
          </span>
        )}
      </div>

      <StageLadder current={maturityStage} />

      {perceptionGap && selfAssessedStage && (
        <div style={{
          background: `${C.error}14`,
          border: `1px solid ${C.error}50`,
          borderRadius: 10,
          padding: "8px 12px",
          fontSize: 13,
          marginBottom: 12,
          color: C.error,
          display: "flex", alignItems: "center", gap: 7,
        }}>
          <IconWarn size={14} /> <span>{t("perception_gap")} — {t("perception_gap_self")}: <strong>{selfAssessedStage}</strong></span>
        </div>
      )}

      {evidence.length > 0 && (
        <>
          <p style={{ color: C.muted, fontSize: 12, margin: "0 0 4px", textTransform: "uppercase", letterSpacing: 1 }}>
            {t("evidence")}
          </p>
          <ul style={{ margin: 0, padding: "0 0 0 18px", color: C.muted, fontSize: 13, lineHeight: 1.6 }}>
            {evidence.map((item, i) => <li key={i}>{item}</li>)}
          </ul>
        </>
      )}
    </div>
  );
}
