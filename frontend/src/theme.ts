import type React from "react";

/* ═══════════════════════════════════════════════════════════════════
   MOUFIDA — Design System  ·  "Atelier Lumière"
   Warm-autumn brand, rebuilt as a token-driven system: a founder's
   atelier at golden hour. Paper & ink depth, editorial type, one
   disciplined accent. All legacy exports preserved & enriched.
   ═══════════════════════════════════════════════════════════════════ */

// ── Typography families ──────────────────────────────────────────
export const F = {
  heading: "'Playfair Display', Georgia, 'Times New Roman', serif",
  body:    "'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif",
  // Crafted tabular numerals for data moments (scores, counts, gauges).
  mono:    "'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif",
} as const;

// ── Warm Autumn Palette ──────────────────────────────────────────
// Brand anchors (text / primary / accent) are kept EXACT; the rest is a
// derived warm ramp that adds real elevation + ink depth.
export const C = {
  // Backgrounds & surfaces (low → high elevation)
  bg:          "#F4E9DA",  // Cream Beige — app canvas
  bgDeep:      "#ECDFCC",  // recessed wells / track grooves
  surface:     "#EFE3D3",  // Warm Sand — base cards, panels
  surfaceHigh: "#E3D3BE",  // Deeper Sand — inputs, nested surfaces
  paper:       "#FFFCF7",  // near-white warm paper — top elevation
  border:      "#CBBAA8",  // Warm brown border
  borderSoft:  "#DBCBB6",  // hairline divider
  // Ink ramp
  text:        "#2C1E17",  // Dark Espresso — body text
  ink:         "#241710",  // deepest ink — display headings
  muted:       "#8B6E5A",  // Warm brown muted
  faint:       "#A9947F",  // tertiary / placeholder
  // Brand actions
  primary:     "#6F4E37",  // Coffee Brown — primary actions
  primaryDeep: "#5A3D2B",  // pressed / hover-dark
  accent:      "#C96A2D",  // Fallen Leaves Orange — CTAs
  accentHover: "#D98A3A",  // Autumn Gold — hover states
  accentDeep:  "#A8521F",  // accent pressed
  // Status
  success:     "#2E7D32",  // Warm green
  warning:     "#C86A00",  // Amber-orange
  error:       "#B71C1C",  // Deep warm red
  info:        "#1565C0",  // Deep blue
} as const;

// ── Spacing scale (4px base) ─────────────────────────────────────
export const S = {
  xs:  4,
  sm:  8,
  md:  12,
  lg:  16,
  xl:  22,
  x2:  32,
  x3:  48,
  x4:  72,
} as const;

// ── Radius scale ─────────────────────────────────────────────────
export const R = {
  sm:   8,
  md:   12,
  lg:   16,
  xl:   22,
  pill: 999,
} as const;

// ── Elevation scale (layered warm shadows) ───────────────────────
export const E = {
  0: "none",
  1: "0 1px 2px rgba(58,38,24,0.06), 0 1px 3px rgba(58,38,24,0.05)",
  2: "0 2px 8px rgba(58,38,24,0.07), 0 6px 18px rgba(58,38,24,0.06)",
  3: "0 8px 24px rgba(58,38,24,0.10), 0 18px 44px rgba(58,38,24,0.08)",
  4: "0 16px 40px rgba(58,38,24,0.14), 0 30px 70px rgba(58,38,24,0.12)",
  inset: "inset 0 1px 0 rgba(255,255,255,0.6)",
} as const;

// ── Motion tokens ────────────────────────────────────────────────
export const M = {
  fast:   "0.16s",
  base:   "0.24s",
  slow:   "0.42s",
  // Editorial ease-out for entrances; gentle spring for interactions.
  ease:   "cubic-bezier(0.22, 1, 0.36, 1)",
  spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
} as const;

// ── Type scale (CSS preset objects) ──────────────────────────────
export const T = {
  display: {
    fontFamily: F.heading, fontWeight: 700, fontSize: 54,
    lineHeight: 1.04, letterSpacing: "-0.035em",
  } as React.CSSProperties,
  h1: {
    fontFamily: F.heading, fontWeight: 700, fontSize: 30,
    lineHeight: 1.15, letterSpacing: "-0.02em",
  } as React.CSSProperties,
  h2: {
    fontFamily: F.heading, fontWeight: 700, fontSize: 21,
    lineHeight: 1.3, letterSpacing: "-0.01em",
  } as React.CSSProperties,
  h3: {
    fontFamily: F.body, fontWeight: 700, fontSize: 16,
    lineHeight: 1.35, letterSpacing: "0",
  } as React.CSSProperties,
  eyebrow: {
    fontFamily: F.body, fontWeight: 700, fontSize: 11,
    textTransform: "uppercase", letterSpacing: "0.12em",
  } as React.CSSProperties,
  body: {
    fontFamily: F.body, fontWeight: 400, fontSize: 14,
    lineHeight: 1.6,
  } as React.CSSProperties,
  small: {
    fontFamily: F.body, fontWeight: 400, fontSize: 12.5,
    lineHeight: 1.5,
  } as React.CSSProperties,
  caption: {
    fontFamily: F.body, fontWeight: 500, fontSize: 11,
    lineHeight: 1.45, letterSpacing: "0.01em",
  } as React.CSSProperties,
  num: {
    fontFamily: F.heading, fontWeight: 700,
    fontVariantNumeric: "tabular-nums", letterSpacing: "-0.01em",
  } as React.CSSProperties,
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
// 5-tier score colour grammar — applied consistently across gauges,
// table cells, progress bars, and axis labels.
export function scoreColor(score: number): string {
  if (score >= 4.5) return "hsl(120, 65%, 36%)"; // deep green — excellent
  if (score >= 3.5) return "hsl(100, 55%, 42%)"; // green — good
  if (score >= 2.5) return "hsl(45, 85%, 42%)";  // yellow — needs work
  if (score >= 1.5) return "hsl(30, 85%, 48%)";  // amber — at risk
  return "hsl(0, 72%, 50%)";                       // red — critical
}

// ── Sector-adaptive accent ───────────────────────────────────────
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

// ── Shared style objects (enriched, backward-compatible) ─────────
export const card: React.CSSProperties = {
  background:   C.surface,
  borderRadius: R.lg,
  padding:      S.xl,
  border:       `1px solid ${C.border}`,
  boxShadow:    E[2],
};

// Elevated "paper" card — top of the elevation hierarchy.
export const cardRaised: React.CSSProperties = {
  background:   `linear-gradient(168deg, ${C.paper} 0%, ${C.surface} 100%)`,
  borderRadius: R.lg,
  padding:      S.xl,
  border:       `1px solid ${C.borderSoft}`,
  boxShadow:    E[3],
};

export const btn = (active = false): React.CSSProperties => ({
  background:   active ? C.primary : "transparent",
  color:        active ? C.paper : C.muted,
  border:       `1.5px solid ${active ? C.primary : C.border}`,
  borderRadius: R.sm,
  padding:      "7px 16px",
  cursor:       "pointer",
  fontSize:     13,
  fontFamily:   F.body,
  fontWeight:   active ? 600 : 500,
  transition:   `all ${M.base} ${M.ease}`,
  whiteSpace:   "nowrap" as const,
});

export const inputStyle: React.CSSProperties = {
  background:   C.paper,
  border:       `1.5px solid ${C.border}`,
  borderRadius: R.md,
  color:        C.text,
  fontSize:     14,
  fontFamily:   F.body,
  padding:      "10px 14px",
  outline:      "none",
  transition:   `border-color ${M.base}, box-shadow ${M.base}`,
};
