import { useEffect, useRef, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { advanceRoadmap, getRoadmapActions, getRoadmapProvenance, regenerateRoadmap, setRoadmapAction } from "../../api";
import { C, F, btn, card } from "../../theme";
import { IconConfetti, IconWarn, IconTrendDown } from "../shared/icons";
import type { RoadmapAction, RoadmapHorizons, RoadmapProvenance } from "../../types";

// Maps composite score names → axis slugs they primarily relate to.
const SCORE_TO_AXES: Record<string, string[]> = {
  market:            ["market"],
  commercial_offer:  ["product"],
  innovation:        ["brand"],
  scalability:       ["business-model", "operations"],
  green:             ["legal"],
};

async function openUrl(url: string) {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("open_url", { url });
  } catch {
    window.open(url, "_blank", "noopener");
  }
}

/** Stable key for an action: horizon + a small hash of its text. */
function actionKey(horizon: string, text: string): string {
  let h = 5381;
  for (let i = 0; i < text.length; i++) h = ((h << 5) + h + text.charCodeAt(i)) | 0;
  return `${horizon}:${(h >>> 0).toString(36)}`;
}

function actionUrl(a: RoadmapAction): string | undefined {
  return a.source ?? a.resource?.url;
}

function ActionCard({
  action, done, onToggle,
}: {
  action: RoadmapAction;
  done: boolean;
  onToggle: (next: boolean) => void;
}) {
  const t = useT();
  const url = actionUrl(action);
  return (
    <div style={{
      background: C.bg,
      borderRadius: 8,
      padding: 12,
      marginBottom: 8,
      border: `1px solid ${done ? C.success : C.border}`,
      opacity: done ? 0.7 : 1,
      transition: "opacity 0.2s, border-color 0.2s",
    }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
        <input
          type="checkbox"
          checked={done}
          onChange={(e) => onToggle(e.target.checked)}
          title={done ? t("roadmap_done") : t("roadmap_mark_done")}
          style={{ accentColor: C.success, width: 15, height: 15, marginTop: 2, flexShrink: 0, cursor: "pointer" }}
        />
        <div style={{ flex: 1 }}>
          <p style={{
            margin: "0 0 4px", fontWeight: 600, fontSize: 14, color: C.text,
            textDecoration: done ? "line-through" : "none",
          }}>
            {action.action}
          </p>
          {action.rationale && (
            <p style={{ margin: "0 0 6px", color: C.muted, fontSize: 13, lineHeight: 1.4 }}>
              {action.rationale}
            </p>
          )}
          {url && (
            <button
              onClick={() => { void openUrl(url); }}
              style={{
                background: "none", border: "none", color: C.primary,
                cursor: "pointer", fontSize: 12, padding: 0, textDecoration: "underline",
              }}
            >
              → {action.resource?.title ?? t("source")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Column({
  title, horizon, actions, completed, onToggle,
}: {
  title: string;
  horizon: string;
  actions: RoadmapAction[];
  completed: Set<string>;
  onToggle: (key: string, action: RoadmapAction, horizon: string, next: boolean) => void;
}) {
  return (
    <div style={{ flex: 1, minWidth: 220 }}>
      <p style={{
        color: C.primary, fontSize: 12, fontWeight: 600,
        textTransform: "uppercase", letterSpacing: 1, margin: "0 0 12px",
      }}>
        {title}
      </p>
      {actions.length === 0
        ? <p style={{ color: C.muted, fontSize: 13 }}>—</p>
        : actions.map((a, i) => {
            const key = actionKey(horizon, a.action);
            return (
              <ActionCard
                key={i}
                action={a}
                done={completed.has(key)}
                onToggle={(next) => onToggle(key, a, horizon, next)}
              />
            );
          })
      }
    </div>
  );
}

export function RoadmapTimeline() {
  const t                    = useT();
  const roadmap              = useStore((s) => s.roadmap);
  const projectId            = useStore((s) => s.projectId);
  const roadmapStale         = useStore((s) => s.roadmapStale);
  const horizonCompleteNonce = useStore((s) => s.horizonCompleteNonce);
  const applyRoadmapUpdate   = useStore((s) => s.applyRoadmapUpdate);
  const scores               = useStore((s) => s.scores);

  const [completed, setCompleted]     = useState<Set<string>>(new Set());
  const [regenBusy, setRegenBusy]     = useState(false);
  const [advanceBusy, setAdvanceBusy] = useState(false);
  const [celebrate, setCelebrate]     = useState(false);
  const [provenance, setProvenance]   = useState<RoadmapProvenance | null>(null);
  const [showProv, setShowProv]       = useState(false);
  const [scoreDeltaAxes, setScoreDeltaAxes] = useState<string[]>([]);
  const prevNonceRef  = useRef(horizonCompleteNonce);
  const prevScoresRef = useRef<Record<string, number>>({});

  useEffect(() => {
    if (!projectId) return;
    getRoadmapActions(projectId)
      .then((r) => setCompleted(new Set(r.actions.filter((a) => a.completed).map((a) => a.action_key))))
      .catch(() => { /* checkboxes start unchecked */ });
    getRoadmapProvenance(projectId)
      .then(setProvenance)
      .catch(() => { /* optional */ });
  }, [projectId]);

  // Show celebration banner when horizon_complete fires
  useEffect(() => {
    if (horizonCompleteNonce > prevNonceRef.current) {
      prevNonceRef.current = horizonCompleteNonce;
      setCelebrate(true);
      const timer = setTimeout(() => setCelebrate(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [horizonCompleteNonce]);

  // Score-delta re-prioritisation: flag axes whose score dropped ≥1.0
  useEffect(() => {
    const prev = prevScoresRef.current;
    const droppedAxes: string[] = [];
    for (const [scoreName, axes] of Object.entries(SCORE_TO_AXES)) {
      const cur  = scores[scoreName] ?? null;
      const last = prev[scoreName]   ?? null;
      if (cur !== null && last !== null && last - cur >= 1.0) {
        droppedAxes.push(...axes);
      }
    }
    if (droppedAxes.length > 0) setScoreDeltaAxes(droppedAxes);
    // Update prev reference after every scores change
    prevScoresRef.current = { ...scores };
  }, [scores]);

  if (!roadmap) {
    return (
      <div style={card}>
        <p style={{ color: C.muted, margin: 0 }}>{t("roadmap_empty")}</p>
      </div>
    );
  }

  // Axis 10 nests the horizon buckets under `roadmap`; tolerate the flat shape too.
  const h: RoadmapHorizons = roadmap.roadmap ?? roadmap;

  let immediate: RoadmapAction[] = h.immediate ?? [];
  let short: RoadmapAction[]     = h.short_term ?? [];
  let medium: RoadmapAction[]    = h.medium_term ?? [];

  if (h.actions && h.actions.length > 0) {
    immediate = h.actions.filter((a) => a.horizon === "immediate");
    short     = h.actions.filter((a) => a.horizon === "short" || a.horizon === "short_term");
    medium    = h.actions.filter((a) => a.horizon === "medium" || a.horizon === "medium_term" || !a.horizon);
  }

  const toggle = (key: string, action: RoadmapAction, horizon: string, next: boolean) => {
    setCompleted((prev) => {
      const copy = new Set(prev);
      if (next) copy.add(key); else copy.delete(key);
      return copy;
    });
    if (projectId) {
      void setRoadmapAction(projectId, {
        action_key: key, action_text: action.action, horizon, completed: next,
      }).catch(() => { /* optimistic */ });
    }
  };

  // Detect whether the active (smallest) horizon is fully checked
  const horizonOrder: Array<{ horizon: string; actions: RoadmapAction[] }> = [
    { horizon: "immediate", actions: immediate },
    { horizon: "short_term", actions: short },
    { horizon: "medium_term", actions: medium },
  ];
  const activeHorizonEntry = horizonOrder.find((h) => h.actions.length > 0);
  const isHorizonDone = activeHorizonEntry != null && activeHorizonEntry.actions.length > 0 &&
    activeHorizonEntry.actions.every((a) => completed.has(actionKey(activeHorizonEntry.horizon, a.action)));

  const handleRegen = async () => {
    if (!projectId) return;
    if (!window.confirm(t("roadmap_regen_confirm"))) return;
    setRegenBusy(true);
    try {
      const res = await regenerateRoadmap(projectId);
      applyRoadmapUpdate({ roadmap: res.roadmap as Parameters<typeof applyRoadmapUpdate>[0]["roadmap"] });
    } catch (e) { console.warn("[regen]", e); }
    finally { setRegenBusy(false); }
  };

  const handleAdvance = async () => {
    if (!projectId || !activeHorizonEntry) return;
    setAdvanceBusy(true);
    try {
      const completedKeys = activeHorizonEntry.actions
        .map((a) => actionKey(activeHorizonEntry.horizon, a.action))
        .filter((k) => completed.has(k));
      const res = await advanceRoadmap(projectId, activeHorizonEntry.horizon, completedKeys);
      applyRoadmapUpdate({ roadmap: res.roadmap as Parameters<typeof applyRoadmapUpdate>[0]["roadmap"] });
    } catch (e) { console.warn("[advance]", e); }
    finally { setAdvanceBusy(false); }
  };

  return (
    <div style={card}>
      {/* Celebration banner */}
      {celebrate && (
        <div style={{
          background: `${C.success}18`, border: `1px solid ${C.success}40`,
          borderRadius: 10, padding: "10px 16px", marginBottom: 14,
          color: C.success, fontSize: 14, fontFamily: F.body, fontWeight: 600,
          display: "flex", alignItems: "center", gap: 8,
        }}>
          <IconConfetti size={16} /> {t("horizon_complete_celebrate")}
        </div>
      )}

      {/* Stale warning */}
      {roadmapStale && (
        <div style={{
          background: `${C.warning}18`, border: `1px solid ${C.warning}40`,
          borderRadius: 10, padding: "10px 16px", marginBottom: 14,
          color: C.warning, fontSize: 13, fontFamily: F.body,
          display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10,
        }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 7 }}><IconWarn size={14} /> {t("roadmap_stale_warning")}</span>
          <button
            onClick={() => { void handleRegen(); }}
            disabled={regenBusy}
            style={{ ...btn(true), padding: "4px 12px", fontSize: 12,
              background: C.warning, borderColor: C.warning, color: "#fff" }}
          >
            {regenBusy ? "…" : t("roadmap_regenerate")}
          </button>
        </div>
      )}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
        <p style={{ color: C.muted, fontSize: 12, margin: 0, textTransform: "uppercase", letterSpacing: 1, fontFamily: F.body }}>
          {t("roadmap_title")}
        </p>
        <div style={{ display: "flex", gap: 6 }}>
          {/* Advance button — show when active horizon is fully completed */}
          {isHorizonDone && (
            <button
              onClick={() => { void handleAdvance(); }}
              disabled={advanceBusy}
              style={{ ...btn(true), padding: "5px 12px", fontSize: 12 }}
            >
              {advanceBusy ? "…" : `${t("roadmap_advance")} →`}
            </button>
          )}
          {/* Regenerate button always available */}
          {!roadmapStale && (
            <button
              onClick={() => { void handleRegen(); }}
              disabled={regenBusy}
              style={{ ...btn(false), padding: "5px 12px", fontSize: 12 }}
            >
              {regenBusy ? "…" : "↺ " + t("roadmap_regenerate")}
            </button>
          )}
        </div>
      </div>

      {/* Score-delta warning */}
      {scoreDeltaAxes.length > 0 && (
        <div style={{
          background: `${C.error}10`, border: `1px solid ${C.error}30`,
          borderRadius: 10, padding: "10px 14px", marginBottom: 14,
          fontSize: 13, fontFamily: F.body, color: C.error,
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 7 }}>
            <IconTrendDown size={14} /> {t("score_delta_warning")} <strong>{scoreDeltaAxes.join(", ")}</strong> — {t("score_delta_review")}
          </span>
          <button
            onClick={() => setScoreDeltaAxes([])}
            style={{ background: "none", border: "none", color: C.muted, cursor: "pointer", fontSize: 16, padding: 0 }}
          >
            ✕
          </button>
        </div>
      )}

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <Column title={t("roadmap_immediate")} horizon="immediate"  actions={immediate} completed={completed} onToggle={toggle} />
        <Column title={t("roadmap_short")}     horizon="short_term" actions={short}     completed={completed} onToggle={toggle} />
        <Column title={t("roadmap_medium")}    horizon="medium_term" actions={medium}   completed={completed} onToggle={toggle} />
      </div>

      {/* Provenance panel */}
      {provenance && (
        <div style={{ marginTop: 16, borderTop: `1px solid ${C.border}`, paddingTop: 10 }}>
          <button
            onClick={() => setShowProv((v) => !v)}
            style={{
              background: "none", border: "none", color: C.muted, cursor: "pointer",
              fontSize: 12, fontFamily: F.body, padding: 0, display: "flex", alignItems: "center", gap: 4,
            }}
          >
            {showProv ? "▲" : "▼"} ⓘ {t("roadmap_provenance")}
          </button>
          {showProv && (
            <div style={{
              marginTop: 8, padding: "10px 14px",
              background: C.surfaceHigh, borderRadius: 8,
              display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 16px",
              fontSize: 12, fontFamily: F.body, color: C.muted,
            }}>
              <span style={{ fontWeight: 700 }}>{t("roadmap_provenance_version")}</span>
              <span>{provenance.roadmap_version ?? "—"}</span>
              <span style={{ fontWeight: 700 }}>{t("roadmap_provenance_kb")}</span>
              <span>{provenance.kb_version ?? "—"}</span>
              <span style={{ fontWeight: 700 }}>{t("roadmap_provenance_trigger")}</span>
              <span>{provenance.trigger ?? "—"}</span>
              <span style={{ fontWeight: 700 }}>{t("roadmap_provenance_generated")}</span>
              <span>{provenance.generated_at ? new Date(provenance.generated_at).toLocaleString() : "—"}</span>
              {provenance.sources.length > 0 && (
                <>
                  <span style={{ fontWeight: 700, alignSelf: "start" }}>{t("roadmap_provenance_sources")}</span>
                  <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    {provenance.sources.map((s, i) => (
                      <span key={i}>{s.source}</span>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
