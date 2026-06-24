/**
 * PitchSimulator — entry card + full-screen pitch session (H1).
 * The 2D character takes the investor "skeptic" pose and reacts to answer
 * quality. Every investor question shows its EvidenceTrace.
 */
import { useEffect, useRef, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { pitchStart, pitchRespond, pitchEnd } from "../../api";
import { C, F, T, btn } from "../../theme";
import { IconTrend, IconHandshake, IconShield, IconTarget, IconChat, IconChart } from "../shared/icons";
import type { InvestorProfile, PitchReadiness, PitchTurn } from "../../types";
import { PixelMoufida } from "../companion/PixelMoufida";
import type { CharacterState } from "../../pixelArt/moufida";
import { EvidenceTrace } from "../shared/EvidenceTrace";
import { PitchReadinessReport } from "./PitchReadinessReport";

type CharState = CharacterState;

const PROFILES: InvestorProfile[] = ["seed_vc", "angel", "impact_fund", "strategic"];

export function PitchSimulator({ projectId }: { projectId: string }) {
  const t = useT();
  const lang = useStore((s) => s.lang);

  const [phase, setPhase] = useState<"idle" | "session" | "report">("idle");
  const [profile, setProfile] = useState<InvestorProfile>("seed_vc");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<PitchTurn[]>([]);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [charState, setCharState] = useState<CharState>("skeptic");
  const [report, setReport] = useState<PitchReadiness | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  const start = async () => {
    setBusy(true); setError(null); setCharState("thinking");
    try {
      const r = await pitchStart(projectId, profile, lang);
      setSessionId(r.session_id);
      setTurns([{ role: "investor", text: r.opening_question, reasoning: r.reasoning, trace: r.trace }]);
      setPhase("session");
      setCharState("skeptic");
    } catch (e) {
      setError(e instanceof Error ? e.message : "error");
      setCharState("skeptic");
    } finally { setBusy(false); }
  };

  const send = async () => {
    if (!sessionId || !answer.trim()) return;
    const myAnswer = answer.trim();
    setTurns((prev) => [...prev, { role: "founder", text: myAnswer }]);
    setAnswer(""); setBusy(true); setCharState("thinking");
    try {
      const r = await pitchRespond(projectId, sessionId, myAnswer, lang);
      setTurns((prev) => [...prev, {
        role: "investor", text: r.follow_up_question, reasoning: r.reasoning,
        trace: r.trace, answer_quality: r.answer_quality,
      }]);
      // Character reacts to how the answer landed.
      if (r.answer_quality === "strong") { setCharState("celebrating"); setTimeout(() => setCharState("skeptic"), 1600); }
      else { setCharState("skeptic"); }
    } catch (e) {
      setError(e instanceof Error ? e.message : "error");
      setCharState("skeptic");
    } finally { setBusy(false); }
  };

  const finish = async () => {
    if (!sessionId) return;
    setBusy(true); setCharState("thinking");
    try {
      const r = await pitchEnd(projectId, sessionId, lang);
      setReport(r);
      setPhase("report");
      setCharState("presenting");
    } catch (e) {
      setError(e instanceof Error ? e.message : "error");
    } finally { setBusy(false); }
  };

  const reset = () => {
    setPhase("idle"); setSessionId(null); setTurns([]); setReport(null); setError(null);
  };

  // ── Entry stage ─────────────────────────────────────────────────
  if (phase === "idle") {
    const PROFILE_ICON: Record<InvestorProfile, React.ReactNode> = {
      seed_vc:     <IconTrend size={18} />,
      angel:       <IconHandshake size={18} />,
      impact_fund: <IconShield size={18} />,
      strategic:   <IconTarget size={18} />,
    };
    const HOW = [
      { icon: <IconTarget size={16} />, text: t("pitch_how_1") },
      { icon: <IconChat size={16} />,   text: t("pitch_how_2") },
      { icon: <IconChart size={16} />,  text: t("pitch_how_3") },
    ];
    return (
      <div style={{
        minHeight: "calc(100vh - 180px)", display: "flex", flexDirection: "column",
        justifyContent: "center", gap: 18,
      }}>
        <div className="mf-glass" style={{ borderRadius: 24, padding: "32px 34px", maxWidth: 800, width: "100%", margin: "0 auto" }}>
          {/* Header */}
          <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 24 }}>
            <div className="mf-float" style={{ flexShrink: 0, filter: "drop-shadow(0 14px 28px rgba(58,38,24,0.28))" }}>
              <PixelMoufida state="skeptic" cssScale={0.85} theme="blue" />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ ...T.eyebrow, color: C.accent, margin: "0 0 5px" }}>{t("tagline_short")}</p>
              <h3 style={{ ...T.h1, margin: 0, color: C.ink, fontSize: 27 }}>{t("pitch_title")}</h3>
              <p style={{ ...T.body, margin: "7px 0 0", color: C.muted, maxWidth: 460 }}>
                {t("pitch_subtitle")}
              </p>
            </div>
          </div>

          {/* Investor selection */}
          <p style={{ ...T.eyebrow, color: C.muted, margin: "0 0 12px" }}>{t("pitch_choose")}</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 22 }}>
            {PROFILES.map((p) => {
              const active = profile === p;
              return (
                <button key={p} onClick={() => setProfile(p)} className="mf-press"
                  style={{
                    textAlign: "start", cursor: "pointer", display: "flex", gap: 12, alignItems: "flex-start",
                    padding: "13px 15px", borderRadius: 14,
                    background: active ? "rgba(var(--mf-accent-rgb),0.10)" : C.surface,
                    border: `1.5px solid ${active ? C.accent : C.borderSoft}`,
                    boxShadow: active ? "0 4px 14px rgba(201,106,45,0.16)" : "none",
                    transition: "all 0.2s var(--mf-ease)",
                  }}>
                  <span style={{
                    width: 36, height: 36, borderRadius: 11, flexShrink: 0,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    background: active ? "linear-gradient(140deg, #D98A3A, #C96A2D)" : C.surfaceHigh,
                    color: active ? "#FFF7EE" : C.muted,
                    boxShadow: active ? "0 3px 10px rgba(201,106,45,0.3)" : "none",
                    transition: "all 0.2s var(--mf-ease)",
                  }}>{PROFILE_ICON[p]}</span>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 700, fontSize: 13.5, color: C.text }}>{t(`pitch_profile_${p}`)}</div>
                    <div style={{ ...T.caption, color: C.muted, marginTop: 2, fontWeight: 400, lineHeight: 1.4 }}>
                      {t(`pitch_profile_${p}_desc`)}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          <button onClick={start} disabled={busy} className="mf-btn-accent mf-cta-glow"
            style={{ width: "100%", padding: "14px 24px", fontSize: 15 }}>
            {busy ? t("pitch_starting") : t("pitch_start")}
          </button>
          {error && <p style={{ color: C.error, fontSize: 12, marginTop: 10 }}>{error}</p>}
        </div>

        {/* How it works */}
        <div style={{ display: "flex", gap: 12, maxWidth: 800, width: "100%", margin: "0 auto", flexWrap: "wrap" }}>
          {HOW.map((s, i) => (
            <div key={i} className="mf-anim-card" style={{
              ["--i" as string]: i,
              flex: "1 1 200px", display: "flex", alignItems: "center", gap: 11,
              padding: "13px 16px", borderRadius: 14,
              background: "rgba(255,252,247,0.55)", border: `1px solid ${C.borderSoft}`,
            }}>
              <span style={{
                width: 32, height: 32, borderRadius: 10, flexShrink: 0,
                display: "flex", alignItems: "center", justifyContent: "center",
                background: "rgba(var(--mf-accent-rgb),0.12)", color: C.accent,
              }}>{s.icon}</span>
              <span style={{ ...T.small, color: C.text, lineHeight: 1.4 }}>{s.text}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Full-screen overlay (session / report) ──────────────────────
  return (
    <div className="mf-overlay-backdrop" style={{
      position: "fixed", inset: 0, background: "rgba(44,30,23,0.55)", zIndex: 1000,
      display: "flex", justifyContent: "center", padding: "3vh 16px", overflowY: "auto",
    }}>
      <div className="mf-overlay-panel" style={{
        background: C.bg, borderRadius: 18, width: "min(860px, 100%)", maxHeight: "94vh",
        display: "flex", flexDirection: "column", overflow: "hidden",
        boxShadow: "0 24px 80px rgba(0,0,0,0.4)",
      }}>
        <header className="mf-glass" style={{
          display: "flex", alignItems: "center", gap: 12, padding: "14px 20px",
          borderRadius: 0, boxShadow: "none", borderBottom: `1px solid ${C.border}`,
        }}>
          <button onClick={phase === "report" ? reset : finish} className="mf-btn-ghost">
            ← {phase === "report" ? t("pitch_close") : t("pitch_end")}
          </button>
          <span style={{ ...T.h3, color: C.ink, fontFamily: F.heading }}>
            {t("pitch_session")} — {t(`pitch_profile_${profile}`)}
          </span>
        </header>

        <div ref={scrollRef} className="mf-scroll" style={{ flex: 1, padding: 20 }}>
          {phase === "report" && report ? (
            <PitchReadinessReport report={report} onClose={reset} />
          ) : (
            <>
              <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
                <PixelMoufida state={charState} cssScale={1.0} theme="blue" />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {turns.map((turn, i) => (
                  <div key={i} className="mf-anim-row" style={{
                    alignSelf: turn.role === "founder" ? "flex-end" : "flex-start",
                    maxWidth: "85%",
                    background: turn.role === "founder" ? C.primary : C.surface,
                    color: turn.role === "founder" ? C.bg : C.text,
                    border: `1px solid ${C.border}`, borderRadius: 14, padding: "10px 14px",
                  }}>
                    <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5 }}>{turn.text}</p>
                    {turn.role === "investor" && turn.trace && turn.trace.length > 0 && (
                      <EvidenceTrace refs={turn.trace} />
                    )}
                  </div>
                ))}
                {busy && <p style={{ color: C.muted, fontSize: 12, alignSelf: "flex-start" }}>…</p>}
              </div>
            </>
          )}
        </div>

        {phase === "session" && (
          <div style={{ borderTop: `1px solid ${C.border}`, padding: 14, background: C.surface }}>
            {error && <p style={{ color: C.error, fontSize: 12, margin: "0 0 8px" }}>{error}</p>}
            <div style={{ display: "flex", gap: 8 }}>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) void send(); }}
                placeholder={t("pitch_answer_placeholder")}
                rows={2}
                className="mf-input"
                style={{
                  flex: 1, resize: "none", background: C.surfaceHigh, border: `1.5px solid ${C.border}`,
                  borderRadius: 10, color: C.text, fontSize: 14, padding: "10px 12px",
                  fontFamily: F.body, outline: "none",
                }}
              />
              <button onClick={send} disabled={busy || !answer.trim()} className="mf-press"
                style={{ ...btn(true), alignSelf: "stretch", paddingInline: 18 }}>
                {t("send")} →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
