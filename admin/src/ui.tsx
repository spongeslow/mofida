import type React from "react";
import { C, F, card, mono } from "./theme";

/** Section heading with eyebrow + serif title, mirroring the landing page rhythm. */
export function PageHeader({
  eyebrow, title, right,
}: { eyebrow: string; title: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, marginBottom: 18 }}>
      <div>
        <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: C.accent, marginBottom: 6 }}>
          {eyebrow}
        </div>
        <h2 style={{ fontFamily: F.heading, fontWeight: 700, fontSize: 26, color: C.text, margin: 0, letterSpacing: "-0.015em" }}>
          {title}
        </h2>
      </div>
      {right && <div style={{ display: "flex", alignItems: "center", gap: 10 }}>{right}</div>}
    </div>
  );
}

/** Soft warm card surface. */
export function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return <div style={{ ...card, ...style }}>{children}</div>;
}

/** Card that wraps a full-bleed table (no inner padding, clipped corners). */
export function TableCard({ children }: { children: React.ReactNode }) {
  return <div style={{ ...card, overflow: "hidden" }}>{children}</div>;
}

/** Status / category pill. */
export function Pill({ color, children }: { color: string; children: React.ReactNode }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6, padding: "3px 10px", borderRadius: 999,
      fontSize: 11.5, fontWeight: 600, color, background: `${color}16`, border: `1px solid ${color}33`,
      fontFamily: F.body, whiteSpace: "nowrap",
    }}>
      {children}
    </span>
  );
}

/** Small filter / action button. */
export function ChipButton({
  active, onClick, children,
}: { active?: boolean; onClick?: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? C.primary : "transparent",
        color: active ? C.bg : C.muted,
        border: `1.5px solid ${active ? C.primary : C.border}`,
        borderRadius: 9, padding: "5px 13px", cursor: "pointer",
        fontSize: 12.5, fontWeight: active ? 600 : 500, fontFamily: F.body,
        transition: "all .16s ease", whiteSpace: "nowrap",
      }}
      onMouseEnter={(e) => { if (!active) { e.currentTarget.style.borderColor = C.accent; e.currentTarget.style.color = C.primary; } }}
      onMouseLeave={(e) => { if (!active) { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.muted; } }}
    >
      {children}
    </button>
  );
}

export function ErrorBanner({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      color: C.error, background: `${C.error}10`, border: `1px solid ${C.error}33`,
      borderRadius: 12, padding: "12px 16px", fontSize: 13.5, fontWeight: 500,
    }}>
      {children}
    </div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return <div style={{ color: C.muted, fontSize: 14, padding: "8px 2px" }}>{label}</div>;
}

// ── Shared table primitives ──────────────────────────────────────
export const table: React.CSSProperties = {
  width: "100%", borderCollapse: "collapse", fontSize: 13, fontFamily: F.body,
};
export const tableMono: React.CSSProperties = {
  ...table, fontSize: 12.5, fontFamily: mono,
};
export const theadRow: React.CSSProperties = {
  textAlign: "left", background: C.surfaceHigh,
};
export const th: React.CSSProperties = {
  padding: "11px 14px", fontWeight: 600, fontSize: 11, letterSpacing: "0.06em",
  textTransform: "uppercase", color: C.muted, borderBottom: `1px solid ${C.border}`,
};
export const td: React.CSSProperties = { padding: "11px 14px", color: C.text };
export const trBorder: React.CSSProperties = { borderTop: `1px solid ${C.border}88` };
