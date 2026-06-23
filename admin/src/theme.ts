import type React from "react";

// ── Typography ───────────────────────────────────────────────────
// Mirrors the desktop app (frontend/src/theme.ts) and landing page so the
// admin panel feels like a natural extension of the Moufida product.
export const F = {
  heading: "'Playfair Display', Georgia, 'Times New Roman', serif",
  body: "'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif",
} as const;

export const mono =
  "'JetBrains Mono', 'SFMono-Regular', ui-monospace, Menlo, monospace";

// ── Warm Autumn Palette ──────────────────────────────────────────
export const C = {
  bg: "#F5EBDD", // Cream Beige — main background
  surface: "#EDE0CE", // Warm Sand — cards, panels
  surfaceHigh: "#E3D3BE", // Deeper Sand — inputs, nested surfaces
  border: "#CBBAA8", // Warm brown border
  text: "#2C1E17", // Dark Espresso — body text
  muted: "#8B6E5A", // Warm brown muted
  primary: "#6F4E37", // Coffee Brown — primary actions
  primaryDark: "#5A3D2B",
  accent: "#C96A2D", // Fallen Leaves Orange — CTAs
  accentHover: "#D98A3A", // Autumn Gold — hover states
  success: "#2E7D32", // Warm green
  warning: "#C86A00", // Amber-orange
  error: "#B71C1C", // Deep warm red
  info: "#1565C0", // Deep blue

  // Espresso console — for the live log terminal (on-brand dark surface).
  console: "#241712",
  consoleHigh: "#30201A",

  // ── Back-compat semantic aliases (used across the pages) ──
  ok: "#2E7D32",
  warn: "#C86A00",
  err: "#B71C1C",
  debug: "#9C8472",
} as const;

export function statusColor(status: string): string {
  if (status === "ok" || status === "alive") return C.success;
  if (status === "down" || status === "error") return C.error;
  return C.warning;
}

export function levelColor(level: string): string {
  switch (level) {
    case "ERROR":
    case "CRITICAL":
      return "#F0846F"; // warm red — readable on espresso
    case "WARNING":
      return "#E3A33A"; // autumn gold
    case "DEBUG":
      return "#A98C78";
    default:
      return "#E9DCCB"; // cream
  }
}

// ── Shared style objects ─────────────────────────────────────────
export const card: React.CSSProperties = {
  background: C.surface,
  borderRadius: 16,
  border: `1px solid ${C.border}`,
  boxShadow: "0 2px 16px rgba(111,78,55,0.07), 0 1px 4px rgba(111,78,55,0.04)",
};

export const sectionTitle: React.CSSProperties = {
  fontFamily: F.heading,
  fontWeight: 700,
  fontSize: 19,
  color: C.text,
  letterSpacing: "-0.01em",
  margin: 0,
};

export const eyebrow: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  fontSize: 10.5,
  fontWeight: 700,
  letterSpacing: "0.12em",
  textTransform: "uppercase",
  color: C.muted,
};
