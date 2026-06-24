/**
 * CompareDiagnostics — side-by-side comparison of the two latest diagnostics
 * (analysis §8 / §17). Wraps the existing `compareHistory()` endpoint which had
 * no UI. Shows per-score deltas plus resolved / new blockers.
 */
import { useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { compareHistory } from "../../api";
import { C, F, card, btn, scoreColor } from "../../theme";
import { IconWarn, IconCheck } from "../shared/icons";
import type { CompareResult } from "../../types";

const SCORE_LABELS: Record<string, string> = {
  market: "score_market",
  commercial_offer: "score_commercial_offer",
  innovation: "score_innovation",
  scalability: "score_scalability",
  green: "score_green",
};

function DeltaBadge({ delta }: { delta: number }) {
  const up = delta > 0.05, down = delta < -0.05;
  const color = up ? C.success : down ? C.error : C.muted;
  const arrow = up ? "↑" : down ? "↓" : "→";
  return (
    <span style={{ color, fontWeight: 700, fontSize: 13 }}>
      {arrow} {delta > 0 ? "+" : ""}{delta.toFixed(1)}
    </span>
  );
}

export function CompareDiagnostics() {
  const t = useT();
  const projectId = useStore((s) => s.projectId);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (!projectId) return;
    setBusy(true); setError(null);
    try {
      setResult(await compareHistory(projectId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "error");
    } finally { setBusy(false); }
  };

  return (
    <div style={card}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: result ? 14 : 0 }}>
        <h3 style={{ margin: 0, flex: 1, color: C.text, fontFamily: F.heading, fontSize: 16 }}>
          {t("compare_title")}
        </h3>
        <button onClick={() => { void run(); }} disabled={busy} className="mf-press" style={btn(false)}>
          {busy ? "…" : t("compare_run")}
        </button>
      </div>

      {error && <p style={{ color: C.error, fontSize: 12, margin: 0 }}>{error}</p>}

      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <p style={{ margin: 0, fontSize: 12, color: C.muted, fontFamily: F.body }}>
            {new Date(result.from.created_at).toLocaleDateString()} → {new Date(result.to.created_at).toLocaleDateString()}
            {result.to.maturity_stage && ` · ${result.to.maturity_stage}`}
          </p>

          {/* Score deltas */}
          <div>
            <p style={{ margin: "0 0 6px", fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: 1 }}>
              {t("compare_score_deltas")}
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {Object.entries(result.score_deltas).map(([name, d]) => (
                <div key={name} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
                  <span style={{ flex: 1, color: C.text, fontFamily: F.body }}>{t(SCORE_LABELS[name] ?? name)}</span>
                  <span style={{ color: scoreColor(d.from ?? 0) }}>{(d.from ?? 0).toFixed(1)}</span>
                  <span style={{ color: C.muted }}>→</span>
                  <span style={{ color: scoreColor(d.to ?? 0) }}>{(d.to ?? 0).toFixed(1)}</span>
                  <DeltaBadge delta={d.delta} />
                </div>
              ))}
            </div>
          </div>

          {/* Blockers resolved / new */}
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <p style={{ margin: "0 0 6px", fontSize: 12, color: C.success, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
                <IconCheck size={13} /> {t("compare_resolved")} ({result.blockers_resolved.length})
              </p>
              {result.blockers_resolved.map((b, i) => (
                <p key={i} style={{ margin: "0 0 4px", fontSize: 12, color: C.muted, fontFamily: F.body }}>• {b.description}</p>
              ))}
            </div>
            <div style={{ flex: 1, minWidth: 200 }}>
              <p style={{ margin: "0 0 6px", fontSize: 12, color: C.error, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
                <IconWarn size={13} /> {t("compare_new")} ({result.blockers_new.length})
              </p>
              {result.blockers_new.map((b, i) => (
                <p key={i} style={{ margin: "0 0 4px", fontSize: 12, color: C.muted, fontFamily: F.body }}>• {b.description}</p>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
