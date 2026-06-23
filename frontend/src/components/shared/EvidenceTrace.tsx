/**
 * EvidenceTrace — the shared grounding-contract component for H1–H3.
 * Renders a collapsible source chain with colour-coded badges by source kind,
 * so every generated claim can be traced to an axis field, KB doc, competitor
 * snapshot, opportunity, or daemon signal.
 */
import { useState } from "react";
import { useT } from "../../i18n";
import { C, F } from "../../theme";
import type { EvidenceKind, EvidenceRef } from "../../types";

const KIND_COLOR: Record<EvidenceKind, string> = {
  axis: "#1D4ED8",
  kb: "#6D28D9",
  competitor: "#C96A2D",
  daemon: "#15803D",
  opportunity: "#B45309",
  profile: "#0F766E",
};

function badge(kind: EvidenceKind | undefined) {
  const color = KIND_COLOR[kind ?? "axis"] ?? C.muted;
  return {
    fontSize: 10,
    fontWeight: 700,
    color: "#fff",
    background: color,
    borderRadius: 5,
    padding: "1px 6px",
    textTransform: "uppercase" as const,
    letterSpacing: 0.4,
  };
}

export function EvidenceTrace({ refs, defaultOpen = false }: { refs: EvidenceRef[]; defaultOpen?: boolean }) {
  const t = useT();
  const [open, setOpen] = useState(defaultOpen);
  if (!refs || refs.length === 0) return null;

  return (
    <div style={{ marginTop: 6 }}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="mf-press"
        style={{
          background: "transparent", border: "none", cursor: "pointer",
          color: C.muted, fontSize: 11.5, fontFamily: F.body, padding: 0,
          display: "flex", alignItems: "center", gap: 5,
        }}
      >
        <span>{open ? "▾" : "▸"}</span>
        {t("evidence_trace")} ({refs.length})
      </button>
      {open && (
        <div style={{
          marginTop: 6, display: "flex", flexDirection: "column", gap: 5,
          borderLeft: `2px solid ${C.border}`, paddingLeft: 10,
        }}>
          {refs.map((r, i) => (
            <div key={i} style={{ fontSize: 11.5, color: C.muted, display: "flex", alignItems: "baseline", gap: 6, flexWrap: "wrap" }}>
              <span style={badge(r.kind)}>{r.kind ?? "axis"}</span>
              <span style={{ color: C.text, fontWeight: 600 }}>{r.label}</span>
              {r.doc && <span>· {r.doc}{r.section ? ` ${r.section}` : ""}</span>}
              {r.field && <span>· {r.field}{r.value !== undefined ? `: ${r.value}` : ""}</span>}
              {r.detail && <span>· {r.detail}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
