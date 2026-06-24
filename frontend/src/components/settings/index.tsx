import { useEffect } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { listTools } from "../../api";
import { ToolCard } from "./ToolCard";
import { C, F, card } from "../../theme";
import { PageHeader } from "../shared/PageHeader";
import { IconLock } from "../shared/icons";

function ToggleSwitch({ value, onChange }: { value: boolean; onChange: () => void }) {
  return (
    <button
      role="switch"
      aria-checked={value}
      onClick={onChange}
      style={{
        width: 44, height: 24, borderRadius: 12,
        background: value ? "linear-gradient(135deg, #D98A3A, #C96A2D)" : C.border,
        border: "none", cursor: "pointer", position: "relative",
        transition: "background 0.24s var(--mf-ease)", flexShrink: 0,
        boxShadow: value ? "0 2px 8px rgba(201,106,45,0.35), inset 0 1px 0 rgba(255,255,255,0.2)" : "inset 0 1px 2px rgba(58,38,24,0.12)",
      }}
    >
      <span style={{
        position: "absolute", top: 3, left: value ? 23 : 3,
        width: 18, height: 18, borderRadius: "50%", background: "#fff",
        transition: "left 0.24s var(--mf-spring)",
        boxShadow: "0 2px 5px rgba(58,38,24,0.28)",
      }} />
    </button>
  );
}

export function SettingsView() {
  const t = useT();
  const tools = useStore((s) => s.tools);
  const toolsLoading = useStore((s) => s.toolsLoading);
  const setTools = useStore((s) => s.setTools);
  const setToolsLoading = useStore((s) => s.setToolsLoading);
  const companionVisible = useStore((s) => s.companionVisible);
  const setCompanionVisible = useStore((s) => s.setCompanionVisible);

  useEffect(() => {
    let cancelled = false;
    setToolsLoading(true);
    listTools()
      .then(({ tools }) => {
        if (!cancelled) setTools(tools);
      })
      .catch((err) => console.error("[settings] listTools failed", err))
      .finally(() => { if (!cancelled) setToolsLoading(false); });
    return () => { cancelled = true; };
  }, [setTools, setToolsLoading]);

  const enabledCount = tools.filter((t) => t.enabled).length;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <PageHeader
          title={t("settings_title")}
          subtitle={t("settings_subtitle")}
          badge={enabledCount > 0 ? (
            <span className="mf-chip" style={{ color: C.primary }}>
              {enabledCount} {t("tools_enabled")}
            </span>
          ) : undefined}
        />
      </div>

      {/* Preferences */}
      <section style={{ marginBottom: 32 }}>
        <h3 className="mf-section-title" style={{ marginBottom: 12 }}>
          {t("settings_preferences")}
        </h3>
        <div style={{ ...card, display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, fontSize: 14, color: C.text, fontFamily: F.body }}>
              {t("companion_show")}
            </div>
            <div style={{ fontSize: 12, color: C.muted, marginTop: 2, fontFamily: F.body }}>
              {t("companion_show_desc")}
            </div>
          </div>
          <ToggleSwitch value={companionVisible} onChange={() => setCompanionVisible(!companionVisible)} />
        </div>
      </section>

      {toolsLoading ? (
        <div style={{ color: C.muted, fontSize: 14 }}>{t("tools_loading")}</div>
      ) : tools.length === 0 ? (
        <div style={{ color: C.muted, fontSize: 14 }}>{t("tools_unavailable")}</div>
      ) : (
        <>
          {/* Group by domain */}
          {groupByDomain(tools).map(([domain, domainTools]) => (
            <section key={domain} style={{ marginBottom: 32 }}>
              <h3 className="mf-section-title" style={{ marginBottom: 12 }}>
                {t(`tools_domain_${domain}`) ?? domain}
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {domainTools.map((tool) => (
                  <ToolCard key={tool.slug} tool={tool} />
                ))}
              </div>
            </section>
          ))}

          {/* Privacy note */}
          <div
            style={{
              marginTop: 16,
              display: "flex", alignItems: "flex-start", gap: 9,
              padding: "13px 16px",
              borderRadius: 12,
              background: C.surfaceHigh,
              border: `1px solid ${C.border}`,
              fontSize: 12,
              color: C.muted,
              lineHeight: 1.6,
            }}
          >
            <span style={{ color: C.primary, flexShrink: 0, marginTop: 1 }}><IconLock size={15} /></span>
            {t("tools_privacy_note")}
          </div>
        </>
      )}
    </div>
  );
}

const DOMAIN_ORDER = ["communication", "documentation", "finance", "marketing", "development"];

function groupByDomain(tools: ReturnType<typeof useStore.getState>["tools"]) {
  const map = new Map<string, typeof tools>();
  for (const tool of tools) {
    const group = map.get(tool.domain) ?? [];
    group.push(tool);
    map.set(tool.domain, group);
  }
  return DOMAIN_ORDER
    .filter((d) => map.has(d))
    .map((d) => [d, map.get(d)!] as [string, typeof tools]);
}
