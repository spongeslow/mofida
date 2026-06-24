/**
 * PageHeader — the consistent editorial header for every top-level screen.
 * Eyebrow (kicker) + Playfair title + optional subtitle, with an optional
 * actions slot and badge. Gives all views a single typographic rhythm.
 */
import type React from "react";
import { useT } from "../../i18n";
import { C, T } from "../../theme";

interface Props {
  title: string;
  subtitle?: string;
  /** Small uppercase kicker above the title; defaults to the brand tag. */
  eyebrow?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  icon?: React.ReactNode;
}

export function PageHeader({ title, subtitle, eyebrow, badge, actions, icon }: Props) {
  const t = useT();
  return (
    <header style={{
      display: "flex", alignItems: "flex-end", gap: 14, flexWrap: "wrap", marginBottom: 4,
    }}>
      {icon && (
        <div style={{
          width: 46, height: 46, borderRadius: 14, flexShrink: 0,
          display: "flex", alignItems: "center", justifyContent: "center",
          background: "linear-gradient(140deg, rgba(var(--mf-accent-rgb),0.16), rgba(111,78,55,0.10))",
          border: `1px solid ${C.borderSoft}`, color: C.accent,
        }}>
          {icon}
        </div>
      )}
      <div style={{ flex: 1, minWidth: 220 }}>
        <p style={{ ...T.eyebrow, color: C.accent, margin: "0 0 4px" }}>
          {eyebrow ?? t("tagline_short")}
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <h2 style={{ ...T.h1, margin: 0, color: C.ink }}>{title}</h2>
          {badge}
        </div>
        {subtitle && (
          <p style={{ ...T.small, margin: "6px 0 0", color: C.muted, maxWidth: 620 }}>{subtitle}</p>
        )}
      </div>
      {actions && <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>{actions}</div>}
    </header>
  );
}
