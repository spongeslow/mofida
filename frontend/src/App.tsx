import { useEffect, useState } from "react";
import type React from "react";
import { useStore } from "./store";
import { useT } from "./i18n";
import { SSEConsumer } from "./sse/consumer";
import { Dashboard } from "./components/dashboard";
import { HUD } from "./components/hud";
import { MonParcours } from "./components/mon-parcours";
import { SettingsView } from "./components/settings";
import { PersonaGallery } from "./components/persona/PersonaGallery";
import { PitchSimulator } from "./components/pitch/PitchSimulator";
import { ScenarioPlannerPanel } from "./components/scenario/ScenarioPlannerPanel";
import { KnowledgeBase } from "./components/kb/KnowledgeBase";
import { PixelMoufida } from "./components/companion/PixelMoufida";
import { MoufidaCompanion } from "./components/companion";
import { IntakeWizard } from "./components/intake/IntakeWizard";
import { CreationFlow } from "./components/intake/CreationFlow";
import { ProjectsPage } from "./components/projects/ProjectsPage";
import { startWakeWordDetection } from "./voice/wakeword";
import { playChime } from "./sfx";
import {
  createProject, getDaemonControl, patchProfile, setDaemonPaused,
} from "./api";
import { C, F, T, S, R } from "./theme";

// Maps the app's voice state to the desktop pet's animation state.
const COMPANION_STATE_MAP: Record<string, string> = {
  idle:          "walk",
  listening:     "listening",
  transcribing:  "thinking",
  processing:    "thinking",
  speaking:      "speaking",
};

async function invokeTauri(cmd: string, args?: Record<string, unknown>): Promise<void> {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke(cmd, args);
  } catch {
    /* not running under Tauri (e.g. browser dev) — ignore */
  }
}

// ── Sidebar icon components ───────────────────────────────────────
function IconDashboard() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" fill="none"
      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="2" width="6" height="6" rx="1.5" />
      <rect x="10" y="2" width="6" height="6" rx="1.5" />
      <rect x="2" y="10" width="6" height="6" rx="1.5" />
      <rect x="10" y="10" width="6" height="6" rx="1.5" />
    </svg>
  );
}
function IconChat() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" fill="none"
      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 2h14a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H9l-4 3v-3H3a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Z" />
    </svg>
  );
}
function IconChart() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" fill="none"
      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="2,14 6,8 10,10 16,4" />
      <line x1="2" y1="16" x2="16" y2="16" />
    </svg>
  );
}
function IconGear() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round">
      <circle cx="9" cy="9" r="2.8" />
      <path d="M9 1.5v2M9 14.5v2M1.5 9h2M14.5 9h2M3.7 3.7l1.4 1.4M12.9 12.9l1.4 1.4M3.7 14.3l1.4-1.4M12.9 5.1l1.4-1.4" />
    </svg>
  );
}

function IconUsers() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6.5" cy="6" r="2.6" />
      <path d="M2 15c0-2.5 2-4 4.5-4S11 12.5 11 15" />
      <path d="M12 4.2a2.4 2.4 0 0 1 0 4.6M13 15c0-2.2-1-3.4-2.4-3.9" />
    </svg>
  );
}
function IconBriefcase() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="5.5" width="14" height="9.5" rx="1.5" />
      <path d="M6.5 5.5V4a1.5 1.5 0 0 1 1.5-1.5h2A1.5 1.5 0 0 1 11.5 4v1.5M2 9.5h14" />
    </svg>
  );
}
function IconBranch() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="5" cy="4" r="2" /><circle cx="5" cy="14" r="2" /><circle cx="13" cy="9" r="2" />
      <path d="M5 6v6M5 11c0-3 2-2 6-2" />
    </svg>
  );
}

function IconFolder() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 4.5h4.5l1.5 2H16v7a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1Z" />
    </svg>
  );
}

function IconBook() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 3.5h5a2 2 0 0 1 2 2V15a1.6 1.6 0 0 0-1.6-1.5H3Z" />
      <path d="M15 3.5h-5a2 2 0 0 0-2 2V15a1.6 1.6 0 0 1 1.6-1.5H15Z" />
    </svg>
  );
}

function IconSpark() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" fill="currentColor" aria-hidden="true">
      <path d="M9 1.2l1.5 4.1a3 3 0 0 0 1.8 1.8L16.8 9l-4.5 1.5a3 3 0 0 0-1.8 1.8L9 16.8l-1.5-4.5a3 3 0 0 0-1.8-1.8L1.2 9l4.5-1.5a3 3 0 0 0 1.8-1.8z" />
    </svg>
  );
}

function NavItem({ icon, label, active, onClick }: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button className={`mf-nav-item${active ? " active" : ""}`} onClick={onClick}>
      <span style={{ display: "flex", flexShrink: 0, opacity: active ? 1 : 0.78 }}>{icon}</span>
      <span style={{ flex: 1 }}>{label}</span>
    </button>
  );
}

function NavGroupLabel({ children }: { children: React.ReactNode }) {
  return <div className="mf-nav-group-label">{children}</div>;
}

function Divider() {
  return (
    <div style={{
      height: 1,
      background: `linear-gradient(90deg, transparent, ${C.border}, transparent)`,
      margin: "14px 4px",
      opacity: 0.7,
    }} />
  );
}

// ── Daemon status + pause/resume control (the character = switch) ──
function DaemonStatusControl() {
  const t = useT();
  const paused        = useStore((s) => s.daemonPaused);
  const alive         = useStore((s) => s.daemonAlive);
  const focusId       = useStore((s) => s.daemonFocusProjectId);
  const applyStatus   = useStore((s) => s.applyDaemonStatus);
  const [busy, setBusy] = useState(false);

  // Poll once on mount, then rely on `daemon_status` SSE for live updates.
  useEffect(() => {
    getDaemonControl().then(applyStatus).catch(() => {});
  }, [applyStatus]);

  const toggle = async () => {
    setBusy(true);
    try {
      const state = await setDaemonPaused(!paused);
      applyStatus(state);
    } catch (e) {
      console.warn("[daemon-pause]", e);
    } finally {
      setBusy(false);
    }
  };

  const offline = !alive;
  const label = offline ? t("daemon_offline")
    : paused ? t("daemon_paused")
    : t("daemon_watching");
  const dot = offline ? C.muted : paused ? C.warning : C.success;

  return (
    <div className="mf-status-pill" style={{ marginBottom: 8 }}>
      <span
        className={!offline && !paused ? "mf-live-dot" : undefined}
        style={{ width: 8, height: 8, borderRadius: "50%", background: dot, flexShrink: 0 }}
      />
      <span style={{ flex: 1, ...T.caption, color: C.muted }}>
        {label}
      </span>
      <button
        onClick={() => { void toggle(); }}
        disabled={busy || !focusId}
        title={!focusId ? t("daemon_focus") : paused ? t("daemon_resume") : t("daemon_pause")}
        style={{
          background: "none", border: "none", cursor: focusId ? "pointer" : "not-allowed",
          color: C.accent, fontSize: 14, padding: "2px 4px", lineHeight: 1,
          opacity: focusId ? 1 : 0.4,
        }}
      >
        {paused ? "▶" : "⏸"}
      </button>
    </div>
  );
}

// ── SSE real-time connection indicator ────────────────────────────
function SSEIndicator() {
  const t = useT();
  const connected = useStore((s) => s.sseConnected);
  return (
    <div className="mf-status-pill" style={{ marginBottom: 8 }}>
      <span
        className={connected ? "mf-live-dot" : undefined}
        style={{ width: 7, height: 7, borderRadius: "50%", background: connected ? C.success : C.muted, flexShrink: 0 }}
      />
      <span style={{ flex: 1, ...T.caption, color: C.muted }}>
        {connected ? t("sse_live") : t("sse_offline")}
      </span>
    </div>
  );
}

// ── Landing page ──────────────────────────────────────────────────
function LandingScreen({
  onNewIdea,
  onViewProjects,
}: {
  onNewIdea: (idea: string) => void;
  onViewProjects: () => void;
}) {
  const t = useT();
  const [ideaText, setIdeaText] = useState("");
  const [ideaMode, setIdeaMode] = useState(false);

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      height: "100%",
      padding: 40,
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Stage spotlight behind the mascot (global aurora drifts behind this) */}
      <div style={{
        position: "absolute", inset: 0,
        background: "radial-gradient(ellipse 58% 48% at 50% 42%, rgba(201,106,45,0.12) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      {/* Eyebrow */}
      <p style={{
        ...T.eyebrow, color: C.accent, margin: "0 0 4px", position: "relative", zIndex: 1,
      }}>
        {t("tagline_short")}
      </p>

      {/* Character — pixel-art hero on an animated glow pedestal */}
      <div className="mf-float" style={{ position: "relative", margin: "2px 0 2px", zIndex: 1 }}>
        <div className="mf-halo" style={{
          position: "absolute", left: "50%", bottom: -10,
          width: 220, height: 44, borderRadius: "50%",
          background: "radial-gradient(ellipse, rgba(201,106,45,0.32), transparent 70%)",
          filter: "blur(10px)", pointerEvents: "none",
        }} />
        <div style={{ filter: "drop-shadow(0 20px 40px rgba(58,38,24,0.34))" }}>
          <PixelMoufida state="idle" cssScale={2.3} showName />
        </div>
      </div>

      {/* Display wordmark + tagline */}
      <h1 className="mf-wordmark" style={{
        ...T.display, fontSize: 66, margin: "10px 0 8px", position: "relative", zIndex: 1,
      }}>
        Moufida
      </h1>
      <p style={{
        ...T.body, color: C.muted, fontSize: 16,
        margin: "0 0 32px", textAlign: "center", maxWidth: 380,
        position: "relative", zIndex: 1,
      }}>
        {t("tagline")}
      </p>

      {/* "Got any idea?" creation flow */}
      <div style={{
        width: "100%", maxWidth: 440, display: "flex", flexDirection: "column",
        gap: S.md, position: "relative", zIndex: 1,
      }}>
        {!ideaMode ? (
          <button
            className="mf-btn-primary mf-cta-glow"
            onClick={() => setIdeaMode(true)}
            style={{ fontSize: 16, padding: "16px 32px" }}
          >
            <IconSpark /> {t("creation_got_idea")}
          </button>
        ) : (
          <div className="mf-glass mf-anim-scale" style={{
            display: "flex", flexDirection: "column", gap: S.md,
            borderRadius: R.xl, padding: S.xl,
          }}>
            <p style={{ ...T.h3, margin: 0, color: C.primary, fontFamily: F.heading, fontSize: 16 }}>
              {t("creation_got_idea_question")}
            </p>
            <textarea
              className="mf-input"
              value={ideaText}
              onChange={(e) => setIdeaText(e.target.value)}
              placeholder={t("creation_idea_placeholder")}
              rows={4}
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && ideaText.trim()) {
                  onNewIdea(ideaText.trim());
                }
              }}
              style={{
                width: "100%", background: C.paper,
                border: `1.5px solid ${C.border}`,
                borderRadius: R.md, color: C.text, fontSize: 14.5,
                padding: "13px 16px", boxSizing: "border-box",
                fontFamily: F.body, resize: "vertical", outline: "none",
                lineHeight: 1.65,
              }}
            />
            <div style={{ display: "flex", gap: S.sm }}>
              <button
                className="mf-btn-primary"
                onClick={() => ideaText.trim() && onNewIdea(ideaText.trim())}
                disabled={!ideaText.trim()}
                style={{ flex: 1, opacity: ideaText.trim() ? 1 : 0.55 }}
              >
                {t("creation_build")} →
              </button>
              <button
                className="mf-icon-btn"
                onClick={() => { setIdeaMode(false); setIdeaText(""); }}
                aria-label="Cancel"
                style={{ width: 46, height: "auto", border: `1px solid ${C.border}` }}
              >
                ✕
              </button>
            </div>
            <p style={{ ...T.caption, margin: 0, color: C.muted }}>
              <kbd style={{
                fontFamily: F.body, fontSize: 10, fontWeight: 700, padding: "1px 6px",
                borderRadius: 5, background: C.bgDeep, border: `1px solid ${C.border}`, color: C.muted,
              }}>Ctrl + Enter</kbd> {t("creation_shortcut_hint")}
            </p>
          </div>
        )}

        <button onClick={onViewProjects} className="mf-btn-ghost" style={{ justifyContent: "center", padding: "11px 28px" }}>
          <IconFolder /> {t("nav_projects")}
        </button>
      </div>

      <p className="mf-chip" style={{ marginTop: 24, position: "relative", zIndex: 1, color: C.muted }}>
        <span className="mf-live-dot" style={{ width: 6, height: 6, background: C.accent, display: "inline-block" }} />
        {t("wake_prompt")}
      </p>
    </div>
  );
}

// ── Root App ──────────────────────────────────────────────────────
const LANGS: { code: "fr" | "en" | "ar"; key: string }[] = [
  { code: "fr", key: "lang_fr" },
  { code: "en", key: "lang_en" },
  { code: "ar", key: "lang_ar" },
];

export default function App() {
  const t = useT();

  const lang         = useStore((s) => s.lang);
  const view         = useStore((s) => s.view);
  const voiceState   = useStore((s) => s.voiceState);
  const projectId    = useStore((s) => s.projectId);
  const setLang      = useStore((s) => s.setLang);
  const setView      = useStore((s) => s.setView);
  const setProjectId = useStore((s) => s.setProjectId);
  const clearProject = useStore((s) => s.clearProject);
  const companionVisible  = useStore((s) => s.companionVisible);
  const requestDiagnostic = useStore((s) => s.requestDiagnostic);
  const requestVoice      = useStore((s) => s.requestVoice);
  const daemonPaused      = useStore((s) => s.daemonPaused);

  // Where to go after the intake wizard finishes: the creation/review flow for a
  // brand-new project, or straight to the dashboard for an existing one.
  const [afterIntake, setAfterIntake] = useState<"creation" | "dashboard">("creation");

  // Transient toast for companion-driven events (PDF drop ingestion, …).
  const [toast, setToast] = useState<{ kind: "ok" | "warn"; text: string } | null>(null);

  // Right-to-left layout for Arabic.
  useEffect(() => {
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = lang;
  }, [lang]);

  // Tauri window events
  useEffect(() => {
    let cleanup = () => {};
    import("@tauri-apps/api/event")
      .then(({ listen }) =>
        Promise.all([
          listen("start_diagnose", () => setView("hud")),
          listen("start_new",      () => setView("hud")),
          listen("settings",       () => setView("settings")),
        ]).then(([u1, u2, u3]) => {
          cleanup = () => { u1(); u2(); u3(); };
        })
      )
      .catch(() => {});
    return () => cleanup();
  }, [setView]);

  const companionPulse = useStore((s) => s.companionPulse);
  const pulseCompanion = useStore((s) => s.pulseCompanion);
  const bumpKbRefresh  = useStore((s) => s.bumpKbRefresh);

  // Knowledge-base ingestion from the companion window (drag-and-drop PDFs).
  // She reacts in her own window; here we mirror the mood, refresh the KB
  // browser, and surface a short toast.
  useEffect(() => {
    let cleanup = () => {};
    import("@tauri-apps/api/event")
      .then(({ listen }) =>
        Promise.all([
          listen<{ filename?: string; char_count?: number }>("kb_ingested", (ev) => {
            pulseCompanion("celebrating");
            bumpKbRefresh();
            const name = ev.payload?.filename ?? "document";
            setToast({ kind: "ok", text: t("kb_ingest_ok").replace("{file}", name) });
          }),
          listen<{ reason?: string; filename?: string }>("kb_ingest_error", (ev) => {
            pulseCompanion("worried");
            const reason = ev.payload?.reason ?? "";
            const key =
              reason === "no_project"             ? "kb_ingest_err_no_project" :
              reason.startsWith("unsupported")    ? "kb_ingest_err_type" :
              reason === "too_large"              ? "kb_ingest_err_size" :
              reason === "no_extractable_text"    ? "kb_ingest_err_empty" :
                                                    "kb_ingest_err_generic";
            setToast({ kind: "warn", text: t(key) });
          }),
        ]).then(([u1, u2]) => { cleanup = () => { u1(); u2(); }; })
      )
      .catch(() => {});
    return () => cleanup();
  }, [pulseCompanion, bumpKbRefresh, t]);

  // Auto-dismiss the toast.
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 4200);
    return () => clearTimeout(id);
  }, [toast]);

  // Sync voice state to the desktop companion window. When the daemon is paused
  // and Moufida is otherwise idle, she sleeps (paused watching = sleeping).
  useEffect(() => {
    const state = (daemonPaused && voiceState === "idle")
      ? "sleeping"
      : (COMPANION_STATE_MAP[voiceState] ?? "walk");
    import("@tauri-apps/api/event")
      .then(({ emitTo }) => emitTo("companion", "companion_state", state))
      .catch(() => {});
  }, [voiceState, daemonPaused]);

  // Forward transient companion pulses (celebrate / alert / worried …) to the
  // desktop pet, then restore the base state after the reaction plays.
  useEffect(() => {
    if (companionPulse.nonce === 0) return;
    if (companionVisible) playChime(companionPulse.state);
    let cancelled = false;
    const base = (daemonPaused && voiceState === "idle")
      ? "sleeping"
      : (COMPANION_STATE_MAP[voiceState] ?? "walk");
    import("@tauri-apps/api/event")
      .then(({ emitTo }) => {
        void emitTo("companion", "companion_state", companionPulse.state);
        setTimeout(() => {
          if (!cancelled) void emitTo("companion", "companion_state", base);
        }, companionPulse.state === "celebrating" ? 4200 : 3200);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companionPulse.nonce]);

  // Wake-word detection
  useEffect(() => {
    let stop = () => {};
    startWakeWordDetection(() => setView("hud"))
      .then((fn) => { stop = fn; })
      .catch(() => {});
    return () => stop();
  }, [setView]);

  // Global keyboard shortcuts: Ctrl+Shift+M (toggle window), D (diagnostic), V (voice)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!e.ctrlKey || !e.shiftKey) return;
      const k = e.key.toLowerCase();
      if (k === "m") {
        e.preventDefault();
        void invokeTauri("toggle_main_window");
      } else if (k === "d") {
        e.preventDefault();
        if (projectId) { setView("dashboard"); requestDiagnostic(false); }
      } else if (k === "v") {
        e.preventDefault();
        if (projectId) { setView("hud"); requestVoice(); }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [projectId, setView, requestDiagnostic, requestVoice]);

  // Companion double-click → quick diagnostic (emitted from the companion window)
  useEffect(() => {
    let cleanup = () => {};
    import("@tauri-apps/api/event")
      .then(({ listen }) =>
        listen("run_quick_diagnostic", () => {
          if (projectId) { setView("dashboard"); requestDiagnostic(true); }
        }).then((un) => { cleanup = un; })
      )
      .catch(() => {});
    return () => cleanup();
  }, [projectId, setView, requestDiagnostic]);

  // Reflect the companion-visibility preference into the desktop window.
  useEffect(() => {
    void invokeTauri("set_companion_visible", { visible: companionVisible });
  }, [companionVisible]);

  // Creation path: idea textarea → create project → store raw_idea → CreationFlow
  const handleNewIdeaProject = async (idea: string) => {
    try {
      const { project_id } = await createProject("cross-sector", lang);
      await patchProfile(project_id, { raw_idea: idea });
      setProjectId(project_id);
      setView("creation");
    } catch (e) {
      console.error("[new-idea-project]", e);
    }
  };

  // Open an existing project → straight to its dashboard (no forced intake).
  const handleOpenProject = (id: string) => {
    setProjectId(id);
    setView("dashboard");
  };

  // Open + immediately (re-)run a full diagnostic.
  const handleDiagnoseProject = (id: string) => {
    setProjectId(id);
    setView("dashboard");
    requestDiagnostic(false);
  };

  // Explicit "update profile" → adaptive intake, then back to the dashboard.
  const handleUpdateProfile = (id: string) => {
    setProjectId(id);
    setAfterIntake("dashboard");
    setView("intake");
  };

  const handleIntakeComplete = () => {
    setView(afterIntake === "dashboard" ? "dashboard" : "creation");
  };

  const handleCreationComplete = () => {
    setView("dashboard");
  };

  const voiceLabel =
    voiceState === "listening"   ? t("listening")  :
    voiceState === "speaking"    ? t("speaking")   :
    voiceState !== "idle"        ? "…"             : null;

  return (
    <div className="mf-grain" style={{
      display: "flex",
      height: "100vh",
      overflow: "hidden",
      background: C.bg,
      fontFamily: F.body,
      color: C.text,
      position: "relative",
    }}>
      <SSEConsumer projectId={projectId} />

      {/* Living aurora — slow warm light blooms drifting behind everything */}
      <div className="mf-aurora" aria-hidden="true">
        <span className="orb-1" />
        <span className="orb-2" />
        <span className="orb-3" />
      </div>

      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className="mf-scroll" style={{
        width:        236,
        flexShrink:   0,
        background:   "linear-gradient(185deg, rgba(255,252,247,0.82) 0%, rgba(239,227,211,0.78) 45%, rgba(236,223,204,0.74) 100%)",
        backdropFilter: "blur(18px) saturate(1.25)",
        WebkitBackdropFilter: "blur(18px) saturate(1.25)",
        borderRight:  `1px solid ${C.borderSoft}`,
        display:      "flex",
        flexDirection:"column",
        padding:      "22px 16px 18px",
        boxShadow:    "1px 0 0 rgba(255,255,255,0.5) inset, 4px 0 30px rgba(58,38,24,0.07)",
        overflowY:    "auto",
        position:     "relative",
        zIndex:       2,
      }}>

        {/* Brand nameplate — monogram tile + animated wordmark */}
        <div style={{ display: "flex", alignItems: "center", gap: 11, padding: "2px 8px 18px" }}>
          <div style={{
            width: 40, height: 40, borderRadius: 13, flexShrink: 0,
            background: "linear-gradient(140deg, #D98A3A 0%, #C96A2D 55%, #A8521F 100%)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "#FFF7EE", fontFamily: F.heading, fontSize: 22, fontWeight: 700,
            boxShadow: "0 6px 16px rgba(201,106,45,0.40), inset 0 1px 0 rgba(255,255,255,0.3)",
          }}>
            M
          </div>
          <div style={{ minWidth: 0 }}>
            <h1 className="mf-wordmark" style={{ ...T.h2, margin: 0, fontSize: 21 }}>
              Moufida
            </h1>
            <p style={{ ...T.caption, margin: "1px 0 0", color: C.muted, letterSpacing: "0.04em" }}>
              {t("tagline_short")}
            </p>
          </div>
        </div>

        {/* Navigation — grouped; hidden during intake and creation flows */}
        {projectId && view !== "intake" && view !== "creation" && (
          <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <NavGroupLabel>{t("nav_group_workspace")}</NavGroupLabel>
            <NavItem icon={<IconFolder />}    label={t("nav_projects")}
              active={view === "projects"}  onClick={() => setView("projects")} />
            <NavItem icon={<IconDashboard />} label={t("nav_dashboard")}
              active={view === "dashboard"} onClick={() => setView("dashboard")} />
            <NavItem icon={<IconChat />}      label={t("nav_hud")}
              active={view === "hud"}       onClick={() => setView("hud")} />

            <NavGroupLabel>{t("nav_group_build")}</NavGroupLabel>
            <NavItem icon={<IconUsers />}     label={t("nav_personas")}
              active={view === "personas"}  onClick={() => setView("personas")} />
            <NavItem icon={<IconBriefcase />} label={t("nav_pitch")}
              active={view === "pitch"}     onClick={() => setView("pitch")} />
            <NavItem icon={<IconBranch />}    label={t("nav_scenarios")}
              active={view === "scenarios"} onClick={() => setView("scenarios")} />

            <NavGroupLabel>{t("nav_group_knowledge")}</NavGroupLabel>
            <NavItem icon={<IconBook />}      label={t("nav_kb")}
              active={view === "kb"}        onClick={() => setView("kb")} />
            <NavItem icon={<IconChart />}     label={t("history")}
              active={view === "parcours"}  onClick={() => setView("parcours")} />

            <NavGroupLabel>{t("nav_group_system")}</NavGroupLabel>
            <NavItem icon={<IconGear />}      label={t("nav_settings")}
              active={view === "settings"}  onClick={() => setView("settings")} />
          </nav>
        )}

        {/* Push bottom section down */}
        <div style={{ flex: 1 }} />

        {/* Daemon status + pause/resume (24/7 watcher = the character switch) */}
        {projectId && view !== "intake" && view !== "creation" && <DaemonStatusControl />}

        {/* Real-time connection indicator (Phase 3.3) */}
        {projectId && view !== "intake" && view !== "creation" && <SSEIndicator />}

        {/* Voice state indicator */}
        {voiceLabel && (
          <div className="mf-status-pill" style={{
            marginBottom: 8,
            background: `rgba(var(--mf-accent-rgb), 0.12)`,
            borderColor: `rgba(var(--mf-accent-rgb), 0.32)`,
          }}>
            <span className="mf-voice-pulse" style={{
              width: 8, height: 8, borderRadius: "50%",
              background: C.accent, flexShrink: 0, display: "block",
            }} />
            <span style={{ ...T.caption, color: C.accent, fontWeight: 600 }}>
              {voiceLabel}
            </span>
          </div>
        )}

        <Divider />

        {/* Language selector (FR / EN / AR) */}
        <div className="mf-segment">
          {LANGS.map((l) => (
            <button
              key={l.code}
              className={`mf-segment-btn${lang === l.code ? " active" : ""}`}
              onClick={() => setLang(l.code)}
            >
              {t(l.key)}
            </button>
          ))}
        </div>
      </aside>

      {/* ── Main content area ────────────────────────────────── */}
      <main style={{
        flex:          1,
        display:       "flex",
        flexDirection: "column",
        overflow:      "hidden",
        position:      "relative",
        zIndex:        1,
      }}>
        {view === "projects" ? (
          <div
            key="projects"
            className="mf-view-enter mf-scroll mf-textured"
            style={{ flex: 1, overflowY: "auto", padding: "32px 40px 120px" }}
          >
            <div style={{ maxWidth: 1100, margin: "0 auto" }}>
              <ProjectsPage
                onOpen={handleOpenProject}
                onDiagnose={handleDiagnoseProject}
                onUpdateProfile={handleUpdateProfile}
                onNewProject={clearProject}
              />
            </div>
          </div>
        ) : !projectId ? (
          <LandingScreen
            onNewIdea={(idea) => { void handleNewIdeaProject(idea); }}
            onViewProjects={() => setView("projects")}
          />
        ) : view === "intake" ? (
          <IntakeWizard
            onComplete={handleIntakeComplete}
            mode={afterIntake === "dashboard" ? "update" : "create"}
          />
        ) : view === "creation" ? (
          <CreationFlow onComplete={handleCreationComplete} />
        ) : (
          <div
            key={view}
            className="mf-view-enter mf-scroll mf-textured"
            style={{ flex: 1, overflowY: "auto", padding: "32px 40px 120px" }}
          >
            <div style={{ maxWidth: 1200, margin: "0 auto" }}>
              {view === "dashboard" && <Dashboard />}
              {view === "hud"       && <HUD />}
              {view === "parcours"  && <MonParcours />}
              {view === "settings"  && <SettingsView />}
              {view === "personas"  && projectId && <PersonaGallery projectId={projectId} />}
              {view === "pitch"     && projectId && <PitchSimulator projectId={projectId} />}
              {view === "scenarios" && projectId && (
                <ScenarioPlannerPanel projectId={projectId} onClose={() => setView("dashboard")} />
              )}
              {view === "kb"        && <KnowledgeBase />}
            </div>
          </div>
        )}
      </main>

      {/* Persistent reactive pixel companion (Phase 2.1) */}
      {projectId && companionVisible && view !== "intake" && view !== "creation" && (
        <MoufidaCompanion
          onClick={() => setView("hud")}
          theme={
            view === "pitch"     ? "blue"   :
            view === "scenarios" ? "purple" :
            view === "parcours"  ? "green"  : "default"
          }
        />
      )}

      {/* Companion-driven toast (PDF ingestion feedback) */}
      {toast && (
        <div
          className="mf-toast"
          role="status"
          style={{
            position: "fixed", bottom: 28, left: "50%", transform: "translateX(-50%)",
            zIndex: 10000, maxWidth: 440, padding: "12px 18px", borderRadius: R.md,
            fontSize: 13, fontWeight: 600, fontFamily: F.body, color: "#FFF7EE",
            display: "flex", alignItems: "center", gap: 9,
            background: toast.kind === "ok"
              ? "linear-gradient(135deg, #3a9a3f, #2E7D32)"
              : "linear-gradient(135deg, #d97f1a, #C86A00)",
            boxShadow: "0 12px 34px rgba(58,38,24,0.30), inset 0 1px 0 rgba(255,255,255,0.2)",
          }}
        >
          <span style={{
            width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
            background: "rgba(255,255,255,0.9)",
          }} />
          {toast.text}
        </div>
      )}

    </div>
  );
}
