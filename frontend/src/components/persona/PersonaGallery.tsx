/**
 * PersonaGallery — entry card for the Customer Persona Simulator (H3).
 * Lists generated personas; clicking one opens PersonaChat. The character
 * stands beside the gallery in the "pointing_left" pose.
 */
import { useEffect, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { generatePersonas, getPersonas } from "../../api";
import { C, T, card } from "../../theme";
import type { Persona } from "../../types";
import { PixelMoufida } from "../companion/PixelMoufida";
import { PersonaChat } from "./PersonaChat";
import { PageHeader } from "../shared/PageHeader";
import { IconUser, IconChat } from "../shared/icons";

function PersonaCard({ p, onClick, i }: { p: Persona; onClick: () => void; i: number }) {
  const t = useT();
  return (
    <button onClick={onClick} className="mf-press mf-card-hover mf-anim-card"
      style={{
        textAlign: "start", cursor: "pointer", display: "flex", flexDirection: "column",
        height: "100%",
        background: `linear-gradient(168deg, ${C.paper} 0%, ${C.surface} 100%)`,
        border: `1px solid ${C.borderSoft}`, borderRadius: 16, padding: 18,
        ["--i" as string]: i,
      }}>
      <div style={{ display: "flex", alignItems: "center", gap: 11, marginBottom: 12 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 13, flexShrink: 0,
          display: "flex", alignItems: "center", justifyContent: "center",
          background: "linear-gradient(140deg, rgba(var(--mf-accent-rgb),0.18), rgba(111,78,55,0.10))",
          border: `1px solid ${C.borderSoft}`, color: C.accent,
        }}><IconUser size={22} /></div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: C.text, lineHeight: 1.2 }}>{p.name}</div>
          <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>
            {p.archetype}{p.age_range ? ` · ${p.age_range}` : ""}
          </div>
        </div>
      </div>

      {(p.region || p.budget_range) && (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
          {p.region && <span className="mf-chip" style={{ fontSize: 10.5 }}>{p.region}</span>}
          {p.budget_range && (
            <span className="mf-chip" style={{ fontSize: 10.5, color: C.primary }}>
              {t("persona_budget")}: {p.budget_range}
            </span>
          )}
        </div>
      )}

      {p.goal && (
        <p style={{ ...T.small, margin: "0 0 8px", color: C.text, lineHeight: 1.5 }}>
          <span style={{ color: C.muted }}>{t("persona_goal")}: </span>{p.goal}
        </p>
      )}

      {p.top_objection && (
        <div style={{
          fontSize: 12, color: C.text, lineHeight: 1.5, padding: "8px 11px",
          background: `rgba(var(--mf-accent-rgb), 0.07)`, borderRadius: 10,
          borderInlineStart: `2px solid ${C.accent}`, marginBottom: 10,
        }}>
          <span style={{ color: C.muted }}>{t("persona_top_concern")}: </span>“{p.top_objection}”
        </div>
      )}

      {p.buying_triggers && p.buying_triggers.length > 0 && (
        <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginBottom: 10 }}>
          {p.buying_triggers.slice(0, 3).map((tr, i) => (
            <span key={i} style={{
              fontSize: 10, color: C.muted, border: `1px solid ${C.border}`,
              borderRadius: 6, padding: "2px 7px",
            }}>{tr}</span>
          ))}
        </div>
      )}

      <div style={{ marginTop: "auto", paddingTop: 4, color: C.accent, fontSize: 12.5, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
        <IconChat size={14} /> {t("persona_talk")}
      </div>
    </button>
  );
}

export function PersonaGallery({ projectId }: { projectId: string }) {
  const t = useT();
  const lang = useStore((s) => s.lang);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selected, setSelected] = useState<Persona | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getPersonas(projectId)
      .then((r) => { if (!cancelled) setPersonas(r.personas); })
      .catch(() => {/* none yet */})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [projectId]);

  const regenerate = async () => {
    setBusy(true); setError(null);
    try {
      const r = await generatePersonas(projectId, lang);
      setPersonas(r.personas);
    } catch (e) {
      setError(e instanceof Error ? e.message : "error");
    } finally { setBusy(false); }
  };

  if (selected) {
    return (
      <div style={card}>
        <PersonaChat projectId={projectId} persona={selected} onBack={() => setSelected(null)} />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18, minHeight: "calc(100vh - 180px)" }}>
      <PageHeader
        title={t("persona_title")}
        icon={<IconUser size={22} />}
        actions={
          <button onClick={regenerate} disabled={busy} className="mf-btn-accent">
            {busy ? t("persona_generating") : (personas.length ? t("persona_regenerate") : t("persona_generate"))}
          </button>
        }
      />

      {error && <p style={{ color: C.error, fontSize: 12, margin: 0 }}>{error}</p>}

      <div className="mf-aside-grid" style={{ flex: 1 }}>
        {/* Context aside — mascot points at her cast of customers */}
        <aside className="mf-glass" style={{
          borderRadius: 20, padding: "26px 22px", display: "flex", flexDirection: "column",
          alignItems: "center", textAlign: "center", gap: 12,
        }}>
          <div className="mf-float" style={{ filter: "drop-shadow(0 14px 28px rgba(58,38,24,0.26))" }}>
            <PixelMoufida state="pointing_left" cssScale={0.95} />
          </div>
          <h3 style={{ ...T.h2, margin: "4px 0 0", color: C.ink, fontSize: 19 }}>
            {t("persona_intro_title")}
          </h3>
          <p style={{ ...T.small, margin: 0, color: C.muted, lineHeight: 1.6 }}>
            {t("persona_intro_desc")}
          </p>
          <div style={{ flex: 1 }} />
          {personas.length > 0 && (
            <span className="mf-chip" style={{ color: C.primary }}>
              {personas.length} {t("persona_count")}
            </span>
          )}
        </aside>

        {/* Cast */}
        {personas.length === 0 ? (
          <div style={{ ...card, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", minHeight: 220 }}>
            <p style={{ color: C.muted, fontSize: 13.5, lineHeight: 1.6, margin: 0, maxWidth: 320 }}>
              {loading ? t("persona_loading") : t("persona_empty")}
            </p>
          </div>
        ) : (
          <div className="mf-fill-grid">
            {personas.map((p, i) => (
              <PersonaCard key={p.id} p={p} i={i} onClick={() => setSelected(p)} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
