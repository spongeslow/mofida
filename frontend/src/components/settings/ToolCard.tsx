import { useState } from "react";
import type { ToolConfigField, ToolState } from "../../types";
import {
  connectTool, disconnectTool, getToolConnection, saveTool, testTool, syncTool,
} from "../../api";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { C, card, btn } from "../../theme";

interface Props {
  tool: ToolState;
}

async function openExternal(url: string) {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("open_url", { url });
  } catch {
    window.open(url, "_blank", "noopener,noreferrer");
  }
}

// Composio-managed tools are bidirectional with no credential fields — auth is
// handled by a hosted OAuth popup instead of a config form.
function isComposioTool(tool: ToolState): boolean {
  return tool.direction === "bidirectional"
    && Object.keys(tool.config_schema?.properties ?? {}).length === 0;
}

const DOMAIN_ICONS: Record<string, string> = {
  communication: "💬",
  documentation: "📄",
  finance: "📊",
  marketing: "📈",
  development: "⚙️",
};

const DIRECTION_LABEL: Record<string, string> = {
  push: "→ sortant",
  pull: "← entrant",
  bidirectional: "↔ bidirectionnel",
};

const DIRECTION_LABEL_EN: Record<string, string> = {
  push: "→ outgoing",
  pull: "← incoming",
  bidirectional: "↔ bidirectional",
};

export function ToolCard({ tool }: Props) {
  const t = useT();
  const lang = useStore((s) => s.lang);
  const updateTool = useStore((s) => s.updateTool);

  const [expanded, setExpanded] = useState(false);
  const [localConfig, setLocalConfig] = useState<Record<string, unknown>>(
    () => ({ ...tool.config })
  );
  const [enabled, setEnabled] = useState(tool.enabled);
  const [testStatus, setTestStatus] = useState<"idle" | "loading" | "ok" | "error">("idle");
  const [testMsg, setTestMsg] = useState("");
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const icon = DOMAIN_ICONS[tool.domain] ?? "🔌";
  const dirLabel = lang === "en" ? DIRECTION_LABEL_EN[tool.direction] : DIRECTION_LABEL[tool.direction];
  const composio = isComposioTool(tool);

  const schema = tool.config_schema;
  const fields = Object.entries(schema.properties ?? {}) as [string, ToolConfigField][];
  const required = schema.required ?? [];

  function handleToggle() {
    const next = !enabled;
    setEnabled(next);
    if (next && !expanded) setExpanded(true);
  }

  function handleFieldChange(key: string, value: unknown) {
    setLocalConfig((prev) => ({ ...prev, [key]: value }));
  }

  async function handleTest() {
    setTestStatus("loading");
    setTestMsg("");
    try {
      const result = await testTool(tool.slug, localConfig);
      setTestStatus(result.ok ? "ok" : "error");
      setTestMsg(result.message);
    } catch (e) {
      setTestStatus("error");
      setTestMsg(String(e));
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      await saveTool(tool.slug, enabled, localConfig);
      updateTool(tool.slug, { enabled, config: localConfig });
      setTestStatus("idle");
    } catch (e) {
      console.error("[tools] save failed", e);
    } finally {
      setSaving(false);
    }
  }

  async function handleSync() {
    setSyncing(true);
    try {
      const result = await syncTool(tool.slug);
      if (!result.synced && result.message) {
        setTestMsg(result.message);
        setTestStatus("error");
      } else {
        setTestStatus("ok");
        setTestMsg(t("tools_sync_done"));
      }
    } catch (e) {
      setTestStatus("error");
      setTestMsg(String(e));
    } finally {
      setSyncing(false);
    }
  }

  const statusColor = tool.last_error ? C.error : tool.last_sync_at ? C.success : C.muted;
  const statusLabel = tool.last_error
    ? t("tools_error")
    : tool.last_sync_at
    ? t("tools_synced")
    : t("tools_never_synced");

  return (
    <div
      style={{
        ...card,
        borderLeft: `3px solid ${enabled ? C.primary : C.border}`,
        transition: "border-color 0.2s",
      }}
    >
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 22 }}>{icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: C.text }}>{tool.label}</div>
          <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>
            {tool.domain} · {dirLabel}
          </div>
        </div>

        {/* Status dot */}
        <span
          title={statusLabel}
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: statusColor,
            display: "inline-block",
            marginRight: 4,
          }}
        />

        {/* Toggle — hidden for Composio tools (connect/disconnect manage state) */}
        {!composio && <ToggleSwitch value={enabled} onChange={handleToggle} />}

        {/* Expand/collapse */}
        <button
          onClick={() => setExpanded((v) => !v)}
          style={{
            background: "none",
            border: "none",
            color: C.muted,
            cursor: "pointer",
            fontSize: 16,
            padding: "0 4px",
          }}
        >
          {expanded ? "▲" : "▼"}
        </button>
      </div>

      {/* Expanded config form */}
      {expanded && composio && (
        <div style={{ marginTop: 16, borderTop: `1px solid ${C.border}`, paddingTop: 16 }}>
          <ComposioConnect tool={tool} />
        </div>
      )}

      {expanded && !composio && (
        <div style={{ marginTop: 16, borderTop: `1px solid ${C.border}`, paddingTop: 16 }}>
          {fields.map(([key, field]) => (
            <ConfigField
              key={key}
              fieldKey={key}
              field={field}
              value={localConfig[key]}
              required={required.includes(key)}
              onChange={(v) => handleFieldChange(key, v)}
            />
          ))}

          {/* Test result banner */}
          {testStatus !== "idle" && testMsg && (
            <div
              style={{
                margin:       "12px 0",
                padding:      "9px 13px",
                borderRadius:  9,
                background:   testStatus === "ok" ? `${C.success}18` : `${C.error}18`,
                border:       `1px solid ${testStatus === "ok" ? C.success : C.error}40`,
                color:        testStatus === "ok" ? C.success : C.error,
                fontSize:      13,
              }}
            >
              {testStatus === "loading" ? t("tools_testing") : testMsg}
            </div>
          )}

          {/* Last error */}
          {tool.last_error && (
            <div style={{ fontSize: 12, color: C.error, marginBottom: 8 }}>
              {t("tools_last_error")}: {tool.last_error}
            </div>
          )}

          {/* Last sync time */}
          {tool.last_sync_at && (
            <div style={{ fontSize: 12, color: C.muted, marginBottom: 8 }}>
              {t("tools_last_sync")}: {new Date(tool.last_sync_at).toLocaleString()}
            </div>
          )}

          {/* Action buttons */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 }}>
            <button
              onClick={() => { void handleTest(); }}
              disabled={testStatus === "loading"}
              style={{ ...btn(false), color: C.info, borderColor: C.info }}
            >
              {testStatus === "loading" ? t("tools_testing") : t("tools_test")}
            </button>

            <button
              onClick={() => { void handleSave(); }}
              disabled={saving}
              style={{ ...btn(true) }}
            >
              {saving ? t("tools_saving") : t("tools_save")}
            </button>

            {tool.direction !== "pull" && tool.enabled && (
              <button
                onClick={() => { void handleSync(); }}
                disabled={syncing}
                style={{ ...btn(false), color: C.warning, borderColor: C.warning }}
              >
                {syncing ? t("tools_syncing") : t("tools_sync_now")}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ---- Composio managed-OAuth connect flow ----

function ComposioConnect({ tool }: { tool: ToolState }) {
  const t = useT();
  const updateTool = useStore((s) => s.updateTool);
  const connected = tool.enabled && Boolean((tool.config as { connected?: boolean })?.connected);

  const [phase, setPhase] = useState<"idle" | "connecting" | "error">("idle");
  const [msg, setMsg] = useState("");

  async function pollUntilConnected(slug: string, attempts = 40): Promise<boolean> {
    for (let i = 0; i < attempts; i++) {
      await new Promise((r) => setTimeout(r, 3000));
      try {
        const res = await getToolConnection(slug);
        if (res.connected) return true;
      } catch { /* keep polling */ }
    }
    return false;
  }

  async function handleConnect() {
    setPhase("connecting");
    setMsg("");
    try {
      const { redirect_url } = await connectTool(tool.slug);
      await openExternal(redirect_url);
      const ok = await pollUntilConnected(tool.slug);
      if (ok) {
        updateTool(tool.slug, { enabled: true, config: { ...tool.config, connected: true } });
        setPhase("idle");
      } else {
        setPhase("error");
        setMsg(t("tool_connect_timeout"));
      }
    } catch (e) {
      setPhase("error");
      setMsg(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleDisconnect() {
    try {
      await disconnectTool(tool.slug);
      updateTool(tool.slug, { enabled: false, config: { ...tool.config, connected: false } });
    } catch (e) {
      setPhase("error");
      setMsg(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div>
      <p style={{ fontSize: 12, color: C.muted, margin: "0 0 12px", lineHeight: 1.5 }}>
        {t("tool_oauth_hint")}
      </p>

      {connected ? (
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            background: `${C.success}18`, color: C.success,
            borderRadius: 20, padding: "4px 12px", fontSize: 13, fontWeight: 600,
          }}>
            ● {t("tool_connected")}
          </span>
          <button onClick={() => { void handleDisconnect(); }}
            style={{ ...btn(false), color: C.error, borderColor: C.error }}>
            {t("tool_disconnect")}
          </button>
        </div>
      ) : (
        <button
          onClick={() => { void handleConnect(); }}
          disabled={phase === "connecting"}
          style={{ ...btn(true) }}
        >
          {phase === "connecting" ? t("tool_connecting") : t("tool_connect")}
        </button>
      )}

      {phase === "error" && msg && (
        <div style={{
          marginTop: 12, padding: "9px 13px", borderRadius: 9,
          background: `${C.error}18`, border: `1px solid ${C.error}40`,
          color: C.error, fontSize: 13,
        }}>
          {msg}
        </div>
      )}
    </div>
  );
}

// ---- Sub-components ----

interface ToggleProps {
  value: boolean;
  onChange: () => void;
}

function ToggleSwitch({ value, onChange }: ToggleProps) {
  return (
    <button
      role="switch"
      aria-checked={value}
      onClick={onChange}
      style={{
        width: 40,
        height: 22,
        borderRadius: 11,
        background: value ? C.primary : C.border,
        border: "none",
        cursor: "pointer",
        position: "relative",
        transition: "background 0.2s",
        flexShrink: 0,
      }}
    >
      <span
        style={{
          position: "absolute",
          top: 3,
          left: value ? 21 : 3,
          width: 16,
          height: 16,
          borderRadius: "50%",
          background: "#fff",
          transition: "left 0.2s",
        }}
      />
    </button>
  );
}

interface FieldProps {
  fieldKey: string;
  field: ToolConfigField;
  value: unknown;
  required: boolean;
  onChange: (v: unknown) => void;
}

function ConfigField({ field, value, required, onChange }: FieldProps) {
  const inputStyle: React.CSSProperties = {
    width:        "100%",
    background:   C.surfaceHigh,
    border:       `1.5px solid ${C.border}`,
    borderRadius: 9,
    padding:      "8px 12px",
    color:        C.text,
    fontSize:     13,
    fontFamily:   "'Plus Jakarta Sans', system-ui, sans-serif",
    boxSizing:    "border-box",
    marginTop:     4,
    outline:      "none",
    transition:   "border-color 0.18s, box-shadow 0.18s",
  };

  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ fontSize: 13, color: C.muted, display: "block" }}>
        {field.title}
        {required && <span style={{ color: C.error, marginLeft: 3 }}>*</span>}
      </label>
      {field.description && (
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 2, marginTop: 1 }}>
          {field.description}
        </div>
      )}

      {field.type === "boolean" ? (
        <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 6, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={value !== undefined ? Boolean(value) : Boolean(field.default)}
            onChange={(e) => onChange(e.target.checked)}
            style={{ accentColor: C.primary, width: 15, height: 15 }}
          />
          <span style={{ fontSize: 13, color: C.text }}>
            {value !== undefined ? (value ? "Oui / Yes" : "Non / No") : String(field.default ?? false)}
          </span>
        </label>
      ) : field.format === "textarea" ? (
        <textarea
          value={String(value ?? "")}
          onChange={(e) => onChange(e.target.value)}
          placeholder={`Entrez ${field.title.toLowerCase()}…`}
          rows={6}
          style={{ ...inputStyle, resize: "vertical", lineHeight: 1.4 }}
        />
      ) : (
        <input
          type={field.format === "password" ? "password" : "text"}
          value={String(value ?? "")}
          onChange={(e) => onChange(e.target.value)}
          placeholder={String(field.default ?? "")}
          style={inputStyle}
        />
      )}
    </div>
  );
}
