import { useEffect, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { getRoadmapActions } from "../../api";
import { C, F, card } from "../../theme";
import type { RoadmapActionStatus } from "../../types";

const HORIZON_KEYS: Record<string, string> = {
  immediate:   "roadmap_immediate",
  short_term:  "roadmap_short",
  medium_term: "roadmap_medium",
};

export function CompletedActions() {
  const t         = useT();
  const projectId = useStore((s) => s.projectId);
  const [actions, setActions] = useState<RoadmapActionStatus[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    getRoadmapActions(projectId)
      .then((r) => setActions(r.actions.filter((a) => a.completed)))
      .catch(() => setActions([]))
      .finally(() => setLoading(false));
  }, [projectId]);

  return (
    <div style={card}>
      <p style={{ color: C.muted, fontSize: 12, margin: "0 0 16px", textTransform: "uppercase", letterSpacing: 1, fontFamily: F.body }}>
        {t("completed_actions_title")}
      </p>

      {loading && <p style={{ color: C.muted, fontSize: 13 }}>…</p>}

      {!loading && actions.length === 0 && (
        <p style={{ color: C.muted, fontSize: 13 }}>{t("completed_actions_empty")}</p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {actions.map((a) => (
          <div key={a.action_key} style={{
            display: "flex", alignItems: "flex-start", gap: 10,
            padding: "10px 12px", borderRadius: 8, background: C.surfaceHigh,
            borderLeft: `3px solid ${C.success}`,
          }}>
            <span style={{ color: C.success, fontSize: 14, flexShrink: 0, marginTop: 1 }}>✓</span>
            <div style={{ flex: 1 }}>
              <p style={{ margin: 0, fontSize: 14, color: C.text, fontFamily: F.body }}>
                {a.action_text ?? a.action_key}
              </p>
              <div style={{ display: "flex", gap: 10, marginTop: 3 }}>
                {a.horizon && (
                  <span style={{ fontSize: 11, color: C.muted, fontFamily: F.body }}>
                    {t(HORIZON_KEYS[a.horizon] ?? a.horizon)}
                  </span>
                )}
                <span style={{ fontSize: 11, color: C.muted, fontFamily: F.body }}>
                  {new Date(a.completed_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
