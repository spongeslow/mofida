/**
 * AxisRelevanceBar — a labelled horizontal bar for a 0..1 value. Reused for
 * concept activations (Concept Bottleneck layer) and per-axis embedding
 * relevance (axis-direction probe).
 */
import { C, F } from "../../theme";

interface Props {
  label: string;
  value: number;          // 0..1
  color?: string;
  highlight?: boolean;    // draw attention (e.g. the bottleneck concept)
  rightLabel?: string;    // optional text shown after the value (e.g. weight)
}

export function AxisRelevanceBar({ label, value, color, highlight, rightLabel }: Props) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  const barColor = color ?? C.accent;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: highlight ? "4px 6px" : "4px 0",
        borderRadius: 8,
        background: highlight ? "rgba(201,106,45,0.10)" : "transparent",
        border: highlight ? `1px solid ${C.accent}` : "1px solid transparent",
      }}
    >
      <span
        style={{
          flex: "0 0 130px",
          fontSize: 12,
          color: highlight ? C.text : C.muted,
          fontWeight: highlight ? 600 : 400,
          fontFamily: F.body,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
        title={label}
      >
        {label}
      </span>
      <div style={{ flex: 1, height: 7, borderRadius: 4, background: C.border, overflow: "hidden" }}>
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: barColor,
            borderRadius: 4,
            transition: "width 0.5s cubic-bezier(0.22,1,0.36,1)",
          }}
        />
      </div>
      <span style={{ flex: "0 0 auto", fontSize: 12, color: C.text, fontVariantNumeric: "tabular-nums", minWidth: 32, textAlign: "right" }}>
        {value.toFixed(2)}
      </span>
      {rightLabel && (
        <span style={{ flex: "0 0 auto", fontSize: 11, color: C.muted, minWidth: 38, textAlign: "right" }}>
          {rightLabel}
        </span>
      )}
    </div>
  );
}
