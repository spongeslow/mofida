import type React from "react";

// ── Typography ───────────────────────────────────────────────────
export const F = {
  heading: "'Playfair Display', Georgia, 'Times New Roman', serif",
  body:    "'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif",
} as const;

// ── Warm Autumn Palette ──────────────────────────────────────────
export const C = {
  bg:          "#F5EBDD",  // Cream Beige — main background
  surface:     "#EDE0CE",  // Warm Sand — cards, panels
  surfaceHigh: "#E3D3BE",  // Deeper Sand — inputs, nested surfaces
  border:      "#CBBAA8",  // Warm brown border
  text:        "#2C1E17",  // Dark Espresso — body text
  muted:       "#8B6E5A",  // Warm brown muted
  primary:     "#6F4E37",  // Coffee Brown — primary actions
  accent:      "#C96A2D",  // Fallen Leaves Orange — CTAs
  accentHover: "#D98A3A",  // Autumn Gold — hover states
  success:     "#2E7D32",  // Warm green
  warning:     "#C86A00",  // Amber-orange
  error:       "#B71C1C",  // Deep warm red
  info:        "#1565C0",  // Deep blue
} as const;

// ── Score / Stage Colors ─────────────────────────────────────────
export const SCORE_COLORS: Record<string, string> = {
  market:           "#1D4ED8",
  commercial_offer: "#059669",
  innovation:       "#6D28D9",
  scalability:      "#B45309",
  green:            "#15803D",
};

export const STAGE_COLORS: Record<string, string> = {
  Ideation:            "#5B21B6",
  "Market Validation": "#1D4ED8",
  Structuration:       "#0F766E",
  Fundraising:         "#B45309",
  "Launch Planning":   "#15803D",
  Growth:              "#059669",
};

// ── Semantic helpers ─────────────────────────────────────────────
// 5-tier score colour grammar (H5.3) — applied consistently across gauges,
// table cells, progress bars, and axis labels.
export function scoreColor(score: number): string {
  if (score >= 4.5) return "hsl(120, 65%, 36%)"; // deep green — excellent
  if (score >= 3.5) return "hsl(100, 55%, 42%)"; // green — good
  if (score >= 2.5) return "hsl(45, 85%, 42%)";  // yellow — needs work
  if (score >= 1.5) return "hsl(30, 85%, 48%)";  // amber — at risk
  return "hsl(0, 72%, 50%)";                       // red — critical
}

// ── Sector-adaptive accent (H5.3) ────────────────────────────────
// Sets the global --mf-accent CSS variable from the project's sector so the
// pulse rings, textures, and accent chrome pick up a sector-appropriate hue.
const SECTOR_ACCENTS: { match: RegExp; hex: string; rgb: string }[] = [
  { match: /agri|food|agricult|aliment/i, hex: "#3C8C3C", rgb: "60, 140, 60" },
  { match: /tech|software|saas|digital|numéri/i, hex: "#2D6FE0", rgb: "45, 111, 224" },
  { match: /health|sant|medic|médic/i, hex: "#1FA8B8", rgb: "31, 168, 184" },
  { match: /educ|edtech|formation/i, hex: "#7C4DD6", rgb: "124, 77, 214" },
  { match: /financ|fintech|bank|assur/i, hex: "#1493C7", rgb: "20, 147, 199" },
  { match: /energ|cleantech|solar|renouvel/i, hex: "#2FA36B", rgb: "47, 163, 107" },
  { match: /retail|commerce|market|vente/i, hex: "#C96A2D", rgb: "201, 106, 45" },
];

export function setAccent(sector: string | null | undefined): void {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  const found = sector ? SECTOR_ACCENTS.find((s) => s.match.test(sector)) : undefined;
  root.style.setProperty("--mf-accent", found ? found.hex : "#C96A2D");
  root.style.setProperty("--mf-accent-rgb", found ? found.rgb : "201, 106, 45");
}

export function severityColor(sev: string): string {
  if (sev === "critical") return C.error;
  if (sev === "warning")  return C.warning;
  return C.info;
}

export function severityIcon(sev: string): string {
  if (sev === "critical") return "🔴";
  if (sev === "warning")  return "🟡";
  return "🔵";
}

// ── Shared style objects ─────────────────────────────────────────
export const card: React.CSSProperties = {
  background:   C.surface,
  borderRadius: 16,
  padding:      22,
  border:       `1px solid ${C.border}`,
  boxShadow:    "0 2px 16px rgba(111,78,55,0.07), 0 1px 4px rgba(111,78,55,0.04)",
};

export const btn = (active = false): React.CSSProperties => ({
  background:   active ? C.primary : "transparent",
  color:        active ? C.bg : C.muted,
  border:       `1.5px solid ${active ? C.primary : C.border}`,
  borderRadius: 8,
  padding:      "6px 16px",
  cursor:       "pointer",
  fontSize:     13,
  fontFamily:   F.body,
  fontWeight:   active ? 600 : 400,
  transition:   "all 0.18s ease",
  whiteSpace:   "nowrap" as const,
});

export const inputStyle: React.CSSProperties = {
  background:   C.surfaceHigh,
  border:       `1.5px solid ${C.border}`,
  borderRadius: 9,
  color:        C.text,
  fontSize:     14,
  fontFamily:   F.body,
  padding:      "9px 13px",
  outline:      "none",
  transition:   "border-color 0.18s, box-shadow 0.18s",
};
