/**
 * ScenarioPlannerPanel — slide-in "What-If" pivot planner (H2).
 * Define up to 3 scenarios of parameter overrides, project their effect on all
 * nine axes (RAG-grounded, with confidence + sources), compare side by side,
 * and adopt one (patches the profile + re-runs the diagnostic).
 */
import type React from "react";
import { useEffect, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { adoptScenario, projectScenario } from "../../api";
import { C, T, card, btn, scoreColor } from "../../theme";
import type { AxisProjection, Confidence, ScenarioProjection } from "../../types";
import { EvidenceTrace } from "../shared/EvidenceTrace";
import { PixelMoufida } from "../companion/PixelMoufida";
import { PageHeader } from "../shared/PageHeader";
import { IconBranch } from "../shared/icons";

interface Draft {
  label: string;
  params: { key: string; value: string }[];
  projection: ScenarioProjection | null;
  loading: boolean;
}

const CONF_COLOR: Record<Confidence, string> = {
  high: "hsl(120,55%,40%)", medium: "hsl(45,85%,42%)", low: "hsl(0,72%,52%)",
};

function emptyDraft(i: number): Draft {
  return { label: String.fromCharCode(65 + i), params: [{ key: "", value: "" }], projection: null, loading: false };
}

// Persist scenario drafts per project so the planner isn't lost on navigation (Phase 6).
function draftsKey(pid: string): string { return `moufida.scenarios.${pid}`; }
function loadDrafts(pid: string): Draft[] {
  try {
    const raw = localStorage.getItem(draftsKey(pid));
    if (raw) {
      const v = JSON.parse(raw) as Draft[];
      if (Array.isArray(v) && v.length > 0) return v.map((d) => ({ ...d, loading: false }));
    }
  } catch { /* ignore */ }
  return [emptyDraft(0)];
}

function deltaCell(p: AxisProjection) {
  const up = p.delta > 0.05, down = p.delta < -0.05;
  const arrow = up ? "▲" : down ? "▼" : "─";
  const color = up ? "hsl(120,55%,38%)" : down ? "hsl(0,72%,52%)" : C.muted;
  return { arrow, color };
}

export function ScenarioPlannerPanel({ projectId, onClose }: { projectId: string; onClose: () => void }) {
  const t = useT();
  const lang = useStore((s) => s.lang);
  const requestDiagnostic = useStore((s) => s.requestDiagnostic);
  const [drafts, setDrafts] = useState<Draft[]>(() => loadDrafts(projectId));
  const [sel, setSel] = useState<{ label: string; axis: string } | null>(null);
  const [adopting, setAdopting] = useState<string | null>(null);

  useEffect(() => {
    try { localStorage.setItem(draftsKey(projectId), JSON.stringify(drafts)); } catch { /* ignore */ }
  }, [drafts, projectId]);

  const update = (i: number, patch: Partial<Draft>) =>
    setDrafts((d) => d.map((x, j) => (j === i ? { ...x, ...patch } : x)));

  const setParam = (i: number, j: number, field: "key" | "value", val: string) =>
    setDrafts((d) => d.map((x, k) => k === i
      ? { ...x, params: x.params.map((p, l) => (l === j ? { ...p, [field]: val } : p)) } : x));

  const addParam = (i: number) =>
    setDrafts((d) => d.map((x, j) => (j === i ? { ...x, params: [...x.params, { key: "", value: "" }] } : x)));

  const project = async (i: number) => {
    const draft = drafts[i];
    const overrides: Record<string, string> = {};
    draft.params.forEach((p) => { if (p.key.trim() && p.value.trim()) overrides[p.key.trim()] = p.value.trim(); });
    if (Object.keys(overrides).length === 0) return;
    update(i, { loading: true });
    try {
      const proj = await projectScenario(projectId, draft.label, overrides, lang);
      update(i, { projection: proj, loading: false });
    } catch {
      update(i, { loading: false });
    }
  };

  const adopt = async (label: string) => {
    setAdopting(label);
    try {
      await adoptScenario(projectId, label);
      requestDiagnostic(false);
      onClose();
    } finally { setAdopting(null); }
  };

  const projected = drafts.filter((d) => d.projection);
  const axes = Array.from(new Set(projected.flatMap((d) => Object.keys(d.projection!.axis_projections))));
  const bestDraft = projected.reduce<Draft | null>(
    (best, d) => (!best || d.projection!.overall_delta > best.projection!.overall_delta ? d : best), null);

  const selProjection = sel ? drafts.find((d) => d.label === sel.label)?.projection : null;
  const selAxis = sel && selProjection ? selProjection.axis_projections[sel.axis] : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18, minHeight: "calc(100vh - 180px)" }}>
      <PageHeader
        title={t("scenario_title")}
        subtitle={t("scenario_subtitle")}
        icon={<IconBranch size={22} />}
      />

      <div className="mf-planner-grid" style={{ flex: 1 }}>
        {/* ── Editors column ─────────────────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {drafts.map((d, i) => (
            <div key={i} style={{
              background: `linear-gradient(168deg, ${C.paper} 0%, ${C.surface} 100%)`,
              border: `1px solid ${C.borderSoft}`, borderRadius: 16, padding: 16,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                <span style={{ ...T.eyebrow, color: C.muted }}>{t("scenario_label")}</span>
                <input value={d.label} onChange={(e) => update(i, { label: e.target.value })}
                  className="mf-input"
                  style={{ width: 56, background: C.paper, border: `1.5px solid ${C.border}`,
                           borderRadius: 8, color: C.text, padding: "4px 8px", fontSize: 13, fontWeight: 700, textAlign: "center" }} />
                {d.projection && (
                  <span style={{
                    marginInlineStart: "auto", fontSize: 12.5, fontWeight: 700,
                    padding: "2px 10px", borderRadius: 999,
                    background: d.projection.overall_delta >= 0 ? "hsl(120,55%,38%)18" : "hsl(0,72%,52%)18",
                    color: d.projection.overall_delta >= 0 ? "hsl(120,55%,34%)" : "hsl(0,72%,48%)",
                  }}>
                    Δ {d.projection.overall_delta >= 0 ? "+" : ""}{d.projection.overall_delta}
                  </span>
                )}
              </div>
              {d.params.map((p, j) => (
                <div key={j} style={{ display: "flex", gap: 6, marginBottom: 6 }}>
                  <input value={p.key} onChange={(e) => setParam(i, j, "key", e.target.value)}
                    className="mf-input" placeholder={t("scenario_param")} style={paramInput} />
                  <input value={p.value} onChange={(e) => setParam(i, j, "value", e.target.value)}
                    className="mf-input" placeholder={t("scenario_value")} style={paramInput} />
                </div>
              ))}
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button onClick={() => addParam(i)} className="mf-press" style={{ ...btn(false), fontSize: 12 }}>
                  + {t("scenario_add_param")}
                </button>
                <button onClick={() => project(i)} disabled={d.loading} className="mf-btn-accent"
                  style={{ fontSize: 12.5, padding: "8px 16px" }}>
                  {d.loading ? t("scenario_projecting") : `▶ ${t("scenario_project")}`}
                </button>
              </div>
            </div>
          ))}
          {drafts.length < 3 && (
            <button onClick={() => setDrafts((d) => [...d, emptyDraft(d.length)])} className="mf-btn-ghost"
              style={{ alignSelf: "flex-start" }}>+ {t("scenario_add")}</button>
          )}
        </div>

        {/* ── Results column ─────────────────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {projected.length === 0 ? (
            <div style={{ ...card, display: "flex", flexDirection: "column", alignItems: "center",
              justifyContent: "center", textAlign: "center", gap: 14, minHeight: 280 }}>
              <div className="mf-float" style={{ filter: "drop-shadow(0 12px 24px rgba(58,38,24,0.24))" }}>
                <PixelMoufida state="idle" cssScale={0.75} theme="purple" />
              </div>
              <p style={{ ...T.small, color: C.muted, margin: 0, maxWidth: 280, lineHeight: 1.6 }}>
                {t("scenario_run_hint")}
              </p>
            </div>
          ) : (
            <div style={{ ...card }}>
              <h3 style={{ ...T.h3, color: C.ink, margin: "0 0 12px" }}>{t("scenario_results")}</h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
                <thead>
                  <tr style={{ color: C.muted, textAlign: "start" }}>
                    <th style={cellTh}>{t("axis")}</th>
                    {projected.map((d) => <th key={d.label} style={{ ...cellTh, textAlign: "center" }}>{d.label}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {axes.map((axis) => (
                    <tr key={axis} style={{ borderTop: `1px solid ${C.borderSoft}` }}>
                      <td style={{ ...cellTd, color: C.text }}>{t(`axis_${axis.replace(/-/g, "_")}`)}</td>
                      {projected.map((d) => {
                        const p = d.projection!.axis_projections[axis];
                        if (!p) return <td key={d.label} style={{ ...cellTd, textAlign: "center" }}>—</td>;
                        const dc = deltaCell(p);
                        const active = sel?.label === d.label && sel?.axis === axis;
                        return (
                          <td key={d.label} onClick={() => setSel({ label: d.label, axis })}
                            style={{ ...cellTd, textAlign: "center", cursor: "pointer", borderRadius: 8,
                              background: active ? "rgba(var(--mf-accent-rgb),0.12)" : "transparent" }}>
                            <span style={{ color: scoreColor(p.projected_score), fontWeight: 700 }}>{p.projected_score}</span>{" "}
                            <span style={{ color: dc.color }}>{dc.arrow}</span>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Reasoning panel */}
              {selAxis && (
                <div className="mf-anim-fade" style={{ marginTop: 14, background: C.surfaceHigh,
                  border: `1px solid ${C.borderSoft}`, borderRadius: 12, padding: 14 }}>
                  <div style={{ fontSize: 13, color: C.text, fontWeight: 700, marginBottom: 4 }}>
                    {t(`axis_${sel!.axis.replace(/-/g, "_")}`)} — {sel!.label}
                  </div>
                  <div style={{ fontSize: 12, marginBottom: 6 }}>
                    <span style={{ color: C.muted }}>{t("scenario_confidence")}: </span>
                    <span style={{ color: CONF_COLOR[selAxis.confidence], fontWeight: 700 }}>{selAxis.confidence}</span>
                  </div>
                  <p style={{ margin: 0, fontSize: 12.5, color: C.muted, lineHeight: 1.55 }}>{selAxis.reasoning}</p>
                  {selAxis.sources.length > 0 && <EvidenceTrace refs={selAxis.sources} />}
                </div>
              )}

              {/* Adopt */}
              {bestDraft && (
                <div style={{ marginTop: 16, paddingTop: 16, borderTop: `1px solid ${C.borderSoft}`,
                  display: "flex", alignItems: "center", gap: 12 }}>
                  <PixelMoufida state={bestDraft.projection!.overall_delta > 0.5 ? "presenting" : "idle"} cssScale={0.5} theme="purple" />
                  <div style={{ flex: 1, fontSize: 12.5, color: C.muted, lineHeight: 1.5 }}>
                    {bestDraft.projection!.overall_delta > 0.5
                      ? `${t("scenario_best")} ${bestDraft.label}.`
                      : t("scenario_no_clear_win")}
                  </div>
                  <button onClick={() => adopt(bestDraft.label)} disabled={adopting !== null} className="mf-btn-accent">
                    {adopting ? "…" : `${t("scenario_adopt")} ${bestDraft.label} →`}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const paramInput: React.CSSProperties = {
  flex: 1, background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 6,
  color: C.text, padding: "5px 8px", fontSize: 12.5, outline: "none",
};
const cellTh: React.CSSProperties = { padding: "6px 8px", fontWeight: 500 };
const cellTd: React.CSSProperties = { padding: "6px 8px" };
