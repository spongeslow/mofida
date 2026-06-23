/**
 * PitchReadinessReport — end-of-session readiness summary (H1).
 * Ring gauge + per-axis readiness + hardest questions + prep actions + the
 * evidence the investor used.
 */
import { useT } from "../../i18n";
import { C, F, card } from "../../theme";
import type { PitchReadiness } from "../../types";
import { EvidenceTrace } from "../shared/EvidenceTrace";

function readinessColor(v: number): string {
  if (v >= 70) return "hsl(120,60%,40%)";
  if (v >= 45) return "hsl(45,85%,42%)";
  return "hsl(0,72%,52%)";
}

function Ring({ value }: { value: number }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const off = circ * (1 - Math.max(0, Math.min(100, value)) / 100);
  const color = readinessColor(value);
  return (
    <svg width={128} height={128} viewBox="0 0 128 128">
      <circle cx="64" cy="64" r={r} fill="none" stroke={C.border} strokeWidth="12" />
      <circle
        cx="64" cy="64" r={r} fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
        strokeDasharray={circ} strokeDashoffset={off} transform="rotate(-90 64 64)"
        style={{ transition: "stroke-dashoffset 0.9s cubic-bezier(0.22,1,0.36,1)" }}
      />
      <text x="64" y="60" textAnchor="middle" fontSize="30" fontWeight="700" fill={color}>
        {Math.round(value)}
      </text>
      <text x="64" y="80" textAnchor="middle" fontSize="11" fill={C.muted}>/ 100</text>
    </svg>
  );
}

export function PitchReadinessReport({
  report, onClose, onPushActions,
}: {
  report: PitchReadiness;
  onClose: () => void;
  onPushActions?: (actions: string[]) => void;
}) {
  const t = useT();
  const axes = Object.entries(report.per_axis_readiness || {});

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ ...card, display: "flex", alignItems: "center", gap: 24 }} className="mf-anim-scale">
        <Ring value={report.overall_readiness} />
        <div>
          <h2 style={{ margin: 0, color: C.text, fontFamily: F.heading, fontSize: 20 }}>
            {t("pitch_readiness_title")}
          </h2>
          <p style={{ margin: "6px 0 0", color: C.muted, fontSize: 13, lineHeight: 1.5 }}>
            {t("pitch_readiness_subtitle")}
          </p>
        </div>
      </div>

      {axes.length > 0 && (
        <div style={card}>
          <h3 style={{ margin: "0 0 12px", fontSize: 15, color: C.text }}>{t("pitch_per_axis")}</h3>
          {axes.map(([axis, r]) => (
            <div key={axis} style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                <span style={{ color: C.text, fontWeight: 600 }}>{axis}</span>
                <span style={{ color: readinessColor(r.score) }}>{Math.round(r.score)}/100</span>
              </div>
              <div style={{ height: 6, borderRadius: 3, background: C.border }}>
                <div style={{ width: `${r.score}%`, height: "100%", borderRadius: 3,
                              background: readinessColor(r.score), transition: "width 0.6s ease" }} />
              </div>
              {r.gaps?.length > 0 && (
                <ul style={{ margin: "6px 0 0", paddingLeft: 18, color: C.muted, fontSize: 12 }}>
                  {r.gaps.map((g, i) => <li key={i}>{g}</li>)}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      {report.hardest_questions?.length > 0 && (
        <div style={card}>
          <h3 style={{ margin: "0 0 10px", fontSize: 15, color: C.text }}>{t("pitch_hardest")}</h3>
          <ol style={{ margin: 0, paddingLeft: 20, color: C.text, fontSize: 13, lineHeight: 1.7 }}>
            {report.hardest_questions.map((q, i) => <li key={i}>{q}</li>)}
          </ol>
        </div>
      )}

      {report.recommended_actions?.length > 0 && (
        <div style={card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
            <h3 style={{ margin: 0, fontSize: 15, color: C.text }}>{t("pitch_prep")}</h3>
            {onPushActions && (
              <button className="mf-press" onClick={() => onPushActions(report.recommended_actions)}
                style={{ background: C.accent, color: "#fff", border: "none", borderRadius: 8,
                         padding: "6px 12px", cursor: "pointer", fontSize: 12.5 }}>
                {t("pitch_push_roadmap")}
              </button>
            )}
          </div>
          <ul style={{ margin: 0, paddingLeft: 20, color: C.text, fontSize: 13, lineHeight: 1.7 }}>
            {report.recommended_actions.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}

      {report.evidence_used?.length > 0 && (
        <div style={card}>
          <h3 style={{ margin: "0 0 6px", fontSize: 15, color: C.text }}>{t("pitch_evidence_index")}</h3>
          <EvidenceTrace refs={report.evidence_used} defaultOpen />
        </div>
      )}

      <button className="mf-press" onClick={onClose}
        style={{ alignSelf: "flex-start", background: "transparent", color: C.primary,
                 border: `1.5px solid ${C.border}`, borderRadius: 10, padding: "10px 20px",
                 cursor: "pointer", fontSize: 14 }}>
        {t("pitch_close")}
      </button>
    </div>
  );
}
