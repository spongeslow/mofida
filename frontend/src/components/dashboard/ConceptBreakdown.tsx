/**
 * ConceptBreakdown — the Concept Bottleneck layer (Phase H, paper 1).
 *
 * For each diagnostic axis, decomposes the score into named micro-concepts
 * (LLM-scored 0..1), shows the linear-head composite score, and surfaces the
 * bottleneck concept. Seeded from the diagnostic result (store.conceptScores)
 * and refreshed from the API when the daemon re-runs an axis (conceptNonce).
 */
import { useEffect, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { getConceptScores } from "../../api";
import { C, F, card, scoreColor } from "../../theme";
import { IconBolt } from "../shared/icons";
import type { ConceptScore } from "../../types";
import { AxisRelevanceBar } from "../shared/AxisRelevanceBar";
import { BottleneckAlert } from "./BottleneckAlert";

const AXIS_ORDER = [
  "ideation", "market", "product", "brand",
  "business-model", "legal", "operations", "marketing", "sales",
];

function AxisConceptRow({ axis, data }: { axis: string; data: ConceptScore }) {
  const t = useT();
  const [open, setOpen] = useState(false);

  const axisLabel = t(`axis_${axis.replace(/-/g, "_")}`);
  const cbm = data.cbm_score;
  const concepts = Object.entries(data.concepts).sort((a, b) => b[1] - a[1]);
  const bottleneckId = data.bottleneck?.concept_id;

  return (
    <div style={{ borderTop: `1px solid ${C.border}`, padding: "10px 0" }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          display: "flex", alignItems: "center", gap: 10, width: "100%",
          background: "transparent", border: "none", cursor: "pointer",
          padding: 0, textAlign: "left", fontFamily: F.body,
        }}
      >
        <span style={{ color: C.muted, fontSize: 12, width: 14 }}>{open ? "▾" : "▸"}</span>
        <span style={{ flex: 1, fontSize: 14, fontWeight: 600, color: C.text }}>{axisLabel}</span>

        {data.bottleneck && (
          <span
            style={{
              fontSize: 11, color: C.accent, background: "rgba(201,106,45,0.12)",
              borderRadius: 6, padding: "2px 8px", whiteSpace: "nowrap",
            }}
            title={t("concept_bottleneck")}
          >
            <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}><IconBolt size={12} /> {data.bottleneck.label ?? data.bottleneck.concept_id.replace(/_/g, " ")}</span>
          </span>
        )}

        <span
          style={{
            fontSize: 10, color: C.muted, border: `1px solid ${C.border}`,
            borderRadius: 6, padding: "1px 6px", whiteSpace: "nowrap",
          }}
          title={data.calibrated ? t("concept_calibrated_hint") : t("concept_prior_hint")}
        >
          {data.calibrated ? t("concept_calibrated") : t("concept_prior")}
        </span>

        {cbm !== null && (
          <span style={{ fontSize: 20, fontWeight: 700, color: scoreColor(cbm), minWidth: 54, textAlign: "right" }}>
            {cbm.toFixed(1)}
            <span style={{ fontSize: 11, color: C.muted, fontWeight: 400 }}> /5</span>
          </span>
        )}
      </button>

      {open && (
        <div style={{ marginTop: 10, paddingLeft: 24 }}>
          {data.actual_score !== null && data.actual_score !== undefined && (
            <p style={{ margin: "0 0 8px", fontSize: 11.5, color: C.muted }}>
              {t("concept_axis_score")}: <strong style={{ color: scoreColor(data.actual_score) }}>
                {data.actual_score.toFixed(1)}
              </strong> /5
            </p>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {concepts.map(([id, value]) => (
              <AxisRelevanceBar
                key={id}
                label={data.labels[id] ?? id.replace(/_/g, " ")}
                value={value}
                color={scoreColor(value * 5)}
                highlight={id === bottleneckId}
              />
            ))}
          </div>
          {data.bottleneck && <BottleneckAlert bottleneck={data.bottleneck} cbmScore={cbm} />}
        </div>
      )}
    </div>
  );
}

export function ConceptBreakdown() {
  const t             = useT();
  const projectId     = useStore((s) => s.projectId);
  const conceptScores = useStore((s) => s.conceptScores);
  const conceptNonce  = useStore((s) => s.conceptNonce);
  const setConceptScores = useStore((s) => s.setConceptScores);

  // Refresh from the API when the daemon re-runs an axis (SSE bumps conceptNonce).
  useEffect(() => {
    if (!projectId || conceptNonce === 0) return;
    let cancelled = false;
    void getConceptScores(projectId)
      .then((resp) => {
        if (cancelled) return;
        const byAxis: Record<string, ConceptScore> = {};
        for (const row of resp.axes) {
          if (row.axis) byAxis[row.axis] = row;
        }
        if (Object.keys(byAxis).length > 0) setConceptScores(byAxis);
      })
      .catch(() => {/* best-effort */});
    return () => { cancelled = true; };
  }, [projectId, conceptNonce, setConceptScores]);

  const axes = AXIS_ORDER.filter((a) => conceptScores[a]);
  if (axes.length === 0) return null;

  return (
    <div style={card}>
      <div style={{ marginBottom: 6 }}>
        <h3 style={{ margin: 0, color: C.text, fontSize: 16, fontFamily: F.heading }}>
          {t("concept_breakdown_title")}
        </h3>
        <p style={{ margin: "4px 0 0", color: C.muted, fontSize: 12.5, lineHeight: 1.5 }}>
          {t("concept_breakdown_subtitle")}
        </p>
      </div>
      {axes.map((axis) => (
        <AxisConceptRow key={axis} axis={axis} data={conceptScores[axis]} />
      ))}
    </div>
  );
}
