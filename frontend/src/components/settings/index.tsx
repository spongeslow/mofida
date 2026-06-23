import { useEffect } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { listTools } from "../../api";
import { ToolCard } from "./ToolCard";
import { C, F, card } from "../../theme";

function ToggleSwitch({ value, onChange }: { value: boolean; onChange: () => void }) {
  return (
    <button
      role="switch"
      aria-checked={value}
      onClick={onChange}
      style={{
        width: 40, height: 22, borderRadius: 11,
        background: value ? C.primary : C.border,
        border: "none", cursor: "pointer", position: "relative",
        transition: "background 0.2s", flexShrink: 0,
      }}
    >
      <span style={{
        position: "absolute", top: 3, left: value ? 21 : 3,
        width: 16, height: 16, borderRadius: "50%", background: "#fff",
        transition: "left 0.2s",
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
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ margin: 0, color: C.text, fontSize: 22, fontWeight: 700 }}>
          {t("settings_title")}
        </h2>
        <p style={{ color: C.muted, marginTop: 6, fontSize: 14 }}>
          {t("settings_subtitle")}
        </p>
        {enabledCount > 0 && (
          <div
            style={{
              display: "inline-block",
              marginTop: 4,
              padding: "3px 10px",
              borderRadius: 20,
              background: `${C.primary}22`,
              color: C.primary,
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            {enabledCount} {t("tools_enabled")}
          </div>
        )}
      </div>

      {/* Preferences */}
      <section style={{ marginBottom: 32 }}>
        <h3 style={{
          fontSize: 13, fontWeight: 600, textTransform: "uppercase",
          letterSpacing: "0.08em", color: C.muted, margin: "0 0 12px",
        }}>
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
              <h3
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: C.muted,
                  margin: "0 0 12px",
                }}
              >
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
              padding: "12px 16px",
              borderRadius: 8,
              background: C.surfaceHigh,
              border: `1px solid ${C.border}`,
              fontSize: 12,
              color: C.muted,
              lineHeight: 1.6,
            }}
          >
            🔒 {t("tools_privacy_note")}
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
