import { useEffect, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { getDiagnosticHistory } from "../../api";
import { C, STAGE_COLORS, card } from "../../theme";
import { IconWarn } from "../shared/icons";
import type { DiagnosticHistoryEntry } from "../../types";

function HistoryEntry({ entry }: { entry: DiagnosticHistoryEntry }) {
  const t = useT();
  const stageColor = STAGE_COLORS[entry.maturity_stage] ?? C.primary;
  const gap = entry.perception_gap === "yes" || entry.perception_gap === true;

  return (
    <div style={{
      borderLeft: `3px solid ${stageColor}`,
      paddingLeft: 14,
      marginBottom: 20,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
        <span style={{
          background: stageColor,
          color: "#fff",
          borderRadius: 12,
          padding: "2px 10px",
          fontSize: 12,
          fontWeight: 600,
        }}>
          {entry.maturity_stage}
        </span>
        {entry.confidence != null && (
          <span style={{ color: C.muted, fontSize: 12 }}>
            {Math.round(entry.confidence * 100)}% {t("confidence")}
          </span>
        )}
        <span style={{ color: C.muted, fontSize: 11, marginLeft: "auto" }}>
          {new Date(entry.created_at).toLocaleDateString()}
        </span>
      </div>

      {gap && entry.self_assessed && (
        <p style={{ color: C.error, fontSize: 12, margin: "0 0 4px", display: "flex", alignItems: "center", gap: 6 }}>
          <IconWarn size={13} /> {t("perception_gap")} — {t("perception_gap_self")}: {entry.self_assessed}
        </p>
      )}

      {Array.isArray(entry.evidence) && entry.evidence.length > 0 && (
        <ul style={{ margin: "4px 0 0", padding: "0 0 0 16px", color: C.muted, fontSize: 13 }}>
          {entry.evidence.map((e, i) => <li key={i}>{e}</li>)}
        </ul>
      )}
    </div>
  );
}

export function HistoryList() {
  const t = useT();
  const projectId = useStore((s) => s.projectId);
  const [history, setHistory] = useState<DiagnosticHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    getDiagnosticHistory(projectId)
      .then((r) => setHistory(r.history))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, [projectId]);

  return (
    <div style={card}>
      <p style={{ color: C.muted, fontSize: 12, margin: "0 0 16px", textTransform: "uppercase", letterSpacing: 1 }}>
        {t("diagnostic_history")}
      </p>
      {loading && <p style={{ color: C.muted }}>{t("running_diagnostic")}</p>}
      {!loading && history.length === 0 && (
        <p style={{ color: C.muted }}>{t("no_diagnostic_history")}</p>
      )}
      {history.map((entry, i) => <HistoryEntry key={i} entry={entry} />)}
    </div>
  );
}
