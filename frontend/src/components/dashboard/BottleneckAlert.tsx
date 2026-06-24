/**
 * BottleneckAlert — highlights the single concept most holding an axis score
 * back, with the projected score if it were improved (Concept Bottleneck layer).
 */
import { useT } from "../../i18n";
import { C, F, scoreColor } from "../../theme";
import { IconBolt } from "../shared/icons";
import type { ConceptBottleneck } from "../../types";

export function BottleneckAlert({
  bottleneck,
  cbmScore,
}: {
  bottleneck: ConceptBottleneck;
  cbmScore: number | null;
}) {
  const t = useT();
  const label = bottleneck.label ?? bottleneck.concept_id.replace(/_/g, " ");
  const target = bottleneck.score_if_fixed;
  const from = cbmScore ?? null;
  const gain = from !== null ? target - from : null;

  return (
    <div
      style={{
        marginTop: 12,
        padding: "10px 12px",
        borderRadius: 10,
        background: "rgba(201,106,45,0.10)",
        border: `1px solid ${C.accent}`,
        display: "flex",
        flexDirection: "column",
        gap: 4,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ display: "inline-flex", color: C.accent }}><IconBolt size={14} /></span>
        <span style={{ fontSize: 13, fontWeight: 700, color: C.text, fontFamily: F.body }}>
          {t("concept_bottleneck")}: {label}
        </span>
      </div>
      <p style={{ margin: 0, fontSize: 12.5, color: C.muted, lineHeight: 1.5 }}>
        {t("concept_improve_hint")}{" "}
        <strong style={{ color: C.text }}>{(bottleneck.current).toFixed(2)} → 0.80</strong>{" "}
        {from !== null && (
          <>
            {t("concept_would_lift")}{" "}
            <strong style={{ color: scoreColor(from) }}>{from.toFixed(1)}</strong>
            {" → "}
            <strong style={{ color: scoreColor(target) }}>{target.toFixed(1)}</strong>
            {gain !== null && gain > 0 && (
              <span style={{ color: C.success, fontWeight: 600 }}> (+{gain.toFixed(1)})</span>
            )}
          </>
        )}
      </p>
    </div>
  );
}
