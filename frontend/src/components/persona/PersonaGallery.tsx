/**
 * PersonaGallery — entry card for the Customer Persona Simulator (H3).
 * Lists generated personas; clicking one opens PersonaChat. The character
 * stands beside the gallery in the "pointing_left" pose.
 */
import { useEffect, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { generatePersonas, getPersonas } from "../../api";
import { C, F, card, btn } from "../../theme";
import type { Persona } from "../../types";
import { PixelMoufida } from "../companion/PixelMoufida";
import { PersonaChat } from "./PersonaChat";

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
    <div style={card}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <h3 style={{ margin: 0, flex: 1, color: C.text, fontFamily: F.heading, fontSize: 16 }}>
          {t("persona_title")}
        </h3>
        <button onClick={regenerate} disabled={busy} className="mf-press" style={btn(false)}>
          {busy ? t("persona_generating") : (personas.length ? t("persona_regenerate") : t("persona_generate"))}
        </button>
      </div>

      {error && <p style={{ color: C.error, fontSize: 12 }}>{error}</p>}

      {personas.length === 0 ? (
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <PixelMoufida state="pointing_left" cssScale={0.6} />
          <p style={{ color: C.muted, fontSize: 13, lineHeight: 1.5, margin: 0 }}>
            {loading ? t("persona_loading") : t("persona_empty")}
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {personas.map((p) => (
            <button key={p.id} onClick={() => setSelected(p)} className="mf-press mf-card-hover"
              style={{
                flex: "1 1 200px", minWidth: 200, textAlign: "left", cursor: "pointer",
                background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 12, padding: 14,
              }}>
              <div style={{ fontSize: 22 }}>👤</div>
              <div style={{ fontWeight: 700, color: C.text, marginTop: 4 }}>{p.name}</div>
              <div style={{ fontSize: 12, color: C.muted }}>{p.archetype}</div>
              {p.region && <div style={{ fontSize: 11.5, color: C.muted }}>{p.region}</div>}
              {p.top_objection && (
                <div style={{ marginTop: 8, fontSize: 12, color: C.text }}>
                  <span style={{ color: C.muted }}>{t("persona_top_concern")}: </span>
                  “{p.top_objection}”
                </div>
              )}
              <div style={{ marginTop: 10, color: C.accent, fontSize: 12.5, fontWeight: 600 }}>
                💬 {t("persona_talk")}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
