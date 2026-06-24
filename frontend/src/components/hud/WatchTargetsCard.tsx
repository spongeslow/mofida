/**
 * WatchTargetsCard — surfaces what the always-on daemon monitors for the
 * project (analysis §17). Wraps the previously UI-less GET/POST watch-targets
 * endpoints. Refreshes via SSE `watch_targets_updated`.
 */
import { useEffect, useState } from "react";
import type React from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { getWatchTargets, refreshWatchTargets } from "../../api";
import type { WatchTargets } from "../../api";
import { C, F, card, btn } from "../../theme";
import { IconEye } from "../shared/icons";

async function openUrl(url: string) {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("open_url", { url });
  } catch { window.open(url, "_blank", "noopener"); }
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p style={{ margin: "0 0 6px", fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: 1 }}>
        {title}
      </p>
      {children}
    </div>
  );
}

export function WatchTargetsCard() {
  const t = useT();
  const projectId = useStore((s) => s.projectId);
  const [data, setData] = useState<WatchTargets | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    if (!projectId) return;
    getWatchTargets(projectId).then(setData).catch(() => setData(null));
  };

  // Reload on mount and whenever the daemon re-derives targets (SSE nonce).
  useEffect(load, [projectId]);

  const refresh = async () => {
    if (!projectId) return;
    setBusy(true);
    try { await refreshWatchTargets(projectId); setTimeout(load, 800); }
    catch { /* best-effort */ }
    finally { setBusy(false); }
  };

  const empty = data &&
    data.feeds.length === 0 && data.legal_sources.length === 0 &&
    data.keywords.length === 0 && data.competitors.length === 0;

  const linkStyle = { color: C.accent, textDecoration: "none", cursor: "pointer", fontSize: 12.5 } as const;

  return (
    <div style={card}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
        <h3 style={{ margin: 0, flex: 1, color: C.text, fontFamily: F.heading, fontSize: 16, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: C.accent }}><IconEye size={17} /></span> {t("watch_title")}
        </h3>
        <button onClick={() => { void refresh(); }} disabled={busy} className="mf-press" style={btn(false)}>
          {busy ? "…" : t("watch_refresh")}
        </button>
      </div>
      <p style={{ margin: "0 0 14px", fontSize: 12, color: C.muted, fontFamily: F.body }}>{t("watch_subtitle")}</p>

      {empty && <p style={{ color: C.muted, fontSize: 13 }}>{t("watch_empty")}</p>}

      {data && !empty && (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {data.feeds.length > 0 && (
            <Section title={t("watch_feeds")}>
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                {data.feeds.map((f, i) => (
                  <a key={i} href={f.url} style={linkStyle}
                    onClick={(e) => { e.preventDefault(); void openUrl(f.url); }}>{f.url}</a>
                ))}
              </div>
            </Section>
          )}
          {data.legal_sources.length > 0 && (
            <Section title={t("watch_legal")}>
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                {data.legal_sources.map((l, i) => (
                  <a key={i} href={l.url} style={linkStyle}
                    onClick={(e) => { e.preventDefault(); void openUrl(l.url); }}>{l.name || l.url}</a>
                ))}
              </div>
            </Section>
          )}
          {data.keywords.length > 0 && (
            <Section title={t("watch_keywords")}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {data.keywords.map((k, i) => (
                  <span key={i} style={{
                    fontSize: 12, background: `${C.accent}14`, color: C.accent,
                    borderRadius: 20, padding: "3px 10px",
                  }}>{k}</span>
                ))}
              </div>
            </Section>
          )}
          {data.competitors.length > 0 && (
            <Section title={t("watch_competitors")}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {data.competitors.map((comp, i) => (
                  <span key={i} style={{
                    fontSize: 12, background: C.surfaceHigh, color: C.text,
                    borderRadius: 20, padding: "3px 10px", border: `1px solid ${C.border}`,
                  }}>{comp.name}</span>
                ))}
              </div>
            </Section>
          )}
        </div>
      )}
    </div>
  );
}
