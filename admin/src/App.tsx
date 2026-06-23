import { useEffect, useState } from "react";
import { getHealth, getToken, setToken } from "./api";
import { C, F } from "./theme";
import { Health } from "./pages/Health";
import { Requests } from "./pages/Requests";
import { LlmCalls } from "./pages/LlmCalls";
import { DaemonActivity } from "./pages/DaemonActivity";
import { Logs } from "./pages/Logs";

type Tab = "health" | "requests" | "llm" | "daemon" | "logs";
const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "health", label: "Health", icon: "❤" },
  { id: "requests", label: "Requests", icon: "⇄" },
  { id: "llm", label: "LLM Calls", icon: "✦" },
  { id: "daemon", label: "Daemon", icon: "◷" },
  { id: "logs", label: "Logs", icon: "≣" },
];

/** Moufida mark — coffee-bean "M" in the warm brand gradient. */
function Logo({ size = 34 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden role="img">
      <defs>
        <linearGradient id="mf-logo" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop stopColor="#C96A2D" />
          <stop offset="1" stopColor="#6F4E37" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="11" fill="url(#mf-logo)" />
      <path
        d="M10 28V13.5c0-.6.73-.9 1.15-.46L20 22l8.85-8.96c.42-.43 1.15-.13 1.15.47V28"
        stroke="#F5EBDD" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round"
      />
      <circle cx="20" cy="29" r="1.9" fill="#F5EBDD" />
    </svg>
  );
}

export function App() {
  const [tab, setTab] = useState<Tab>("health");
  const [connected, setConnected] = useState<boolean | null>(null);
  const [tokenInput, setTokenInput] = useState(getToken());
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    let alive = true;
    const ping = () =>
      getHealth().then(() => alive && setConnected(true)).catch(() => alive && setConnected(false));
    void ping();
    const t = setInterval(ping, 10000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  const saveToken = () => { setToken(tokenInput.trim()); window.location.reload(); };

  const statusHue = connected === null ? C.warning : connected ? C.success : C.error;
  const statusLabel = connected === null ? "Connecting…" : connected ? "Connected" : "Disconnected";

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          display: "flex", alignItems: "center", gap: 16, padding: "16px 28px",
          borderBottom: `1px solid ${C.border}`,
          background: "rgba(245,235,221,0.82)",
          backdropFilter: "blur(10px)",
          position: "sticky", top: 0, zIndex: 20,
        }}
      >
        <Logo />
        <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.1 }}>
          <span style={{ fontFamily: F.heading, fontSize: 21, fontWeight: 700, color: C.text, letterSpacing: "-0.01em" }}>
            Moufida <span style={{ color: C.accent }}>Admin</span>
          </span>
          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: C.muted, marginTop: 2 }}>
            Observability
          </span>
        </div>

        {/* Connection pill */}
        <span
          style={{
            display: "inline-flex", alignItems: "center", gap: 7, marginLeft: 8,
            padding: "5px 12px", borderRadius: 999, fontSize: 12.5, fontWeight: 600,
            color: statusHue, background: `${statusHue}14`, border: `1px solid ${statusHue}33`,
          }}
        >
          <span style={{ position: "relative", display: "inline-flex", width: 8, height: 8 }}>
            <span style={{
              position: "absolute", inset: 0, borderRadius: "50%", background: statusHue,
              opacity: 0.45, animation: connected ? "mf-ping 1.8s ease-out infinite" : "none",
            }} />
            <span style={{ position: "relative", width: 8, height: 8, borderRadius: "50%", background: statusHue }} />
          </span>
          {statusLabel}
        </span>

        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          <input
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && saveToken()}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="ADMIN_TOKEN (if set)"
            type="password"
            style={{
              background: C.surfaceHigh,
              border: `1.5px solid ${focused ? C.accent : C.border}`,
              boxShadow: focused ? `0 0 0 4px ${C.accent}22` : "none",
              borderRadius: 10, color: C.text, padding: "8px 13px", fontSize: 13,
              width: 210, outline: "none", fontFamily: F.body, transition: "border-color .18s, box-shadow .18s",
            }}
          />
          <button
            onClick={saveToken}
            style={{
              background: C.accent, color: "#fff", border: "none", borderRadius: 10,
              padding: "9px 18px", cursor: "pointer", fontSize: 13, fontWeight: 600,
              fontFamily: F.body, boxShadow: "0 6px 20px rgba(201,106,45,0.35)",
              transition: "transform .15s, background .15s",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = C.accentHover; e.currentTarget.style.transform = "translateY(-1px)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = C.accent; e.currentTarget.style.transform = "translateY(0)"; }}
          >
            Connect
          </button>
        </div>
      </header>

      {/* Segmented tab control */}
      <nav style={{ display: "flex", justifyContent: "center", padding: "18px 28px 0" }}>
        <div
          style={{
            display: "inline-flex", gap: 4, padding: 5, borderRadius: 14,
            background: C.surface, border: `1px solid ${C.border}`,
            boxShadow: "0 2px 16px rgba(111,78,55,0.07)",
          }}
        >
          {TABS.map((t) => {
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                style={{
                  display: "inline-flex", alignItems: "center", gap: 8,
                  background: active ? C.primary : "transparent",
                  color: active ? C.bg : C.muted,
                  border: "none", borderRadius: 10, padding: "9px 20px", cursor: "pointer",
                  fontSize: 13.5, fontWeight: active ? 600 : 500, fontFamily: F.body,
                  boxShadow: active ? "0 4px 14px rgba(111,78,55,0.28)" : "none",
                  transition: "all .18s ease",
                }}
                onMouseEnter={(e) => { if (!active) e.currentTarget.style.color = C.primary; }}
                onMouseLeave={(e) => { if (!active) e.currentTarget.style.color = C.muted; }}
              >
                <span style={{ fontSize: 13, opacity: active ? 1 : 0.7 }}>{t.icon}</span>
                {t.label}
              </button>
            );
          })}
        </div>
      </nav>

      <main style={{ flex: 1, padding: "26px 28px 40px", maxWidth: 1240, width: "100%", margin: "0 auto", overflowY: "auto" }}>
        {tab === "health" && <Health />}
        {tab === "requests" && <Requests />}
        {tab === "llm" && <LlmCalls />}
        {tab === "daemon" && <DaemonActivity />}
        {tab === "logs" && <Logs />}
      </main>

      <style>{`
        @keyframes mf-ping { 0% { transform: scale(1); opacity: .45; } 70%,100% { transform: scale(2.4); opacity: 0; } }
        @keyframes mf-fade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        tr.mf-row { transition: background .14s ease; }
        tr.mf-row:hover { background: rgba(111,78,55,0.05); }
      `}</style>
    </div>
  );
}
