/**
 * PitchSimulator — entry card + full-screen pitch session (H1).
 * The 2D character takes the investor "skeptic" pose and reacts to answer
 * quality. Every investor question shows its EvidenceTrace.
 */
import { useEffect, useRef, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { pitchStart, pitchRespond, pitchEnd } from "../../api";
import { C, F, card, btn } from "../../theme";
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

  // ── Entry card ──────────────────────────────────────────────────
  if (phase === "idle") {
    return (
      <div style={card} className="mf-card-hover">
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ flexShrink: 0 }}><PixelMoufida state="skeptic" cssScale={0.6} theme="blue" /></div>
          <div style={{ flex: 1 }}>
            <h3 style={{ margin: 0, color: C.text, fontFamily: F.heading, fontSize: 17 }}>
              {t("pitch_title")}
            </h3>
            <p style={{ margin: "4px 0 0", color: C.muted, fontSize: 12.5, lineHeight: 1.5 }}>
              {t("pitch_subtitle")}
            </p>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 14 }}>
          {PROFILES.map((p) => (
            <button key={p} onClick={() => setProfile(p)} style={btn(profile === p)} className="mf-press">
              {t(`pitch_profile_${p}`)}
            </button>
          ))}
        </div>
        <button onClick={start} disabled={busy} className="mf-press"
          style={{ ...btn(true), marginTop: 14 }}>
          {busy ? t("pitch_starting") : t("pitch_start")}
        </button>
        {error && <p style={{ color: C.error, fontSize: 12, marginTop: 8 }}>{error}</p>}
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
        <header style={{
          display: "flex", alignItems: "center", gap: 12, padding: "14px 20px",
          borderBottom: `1px solid ${C.border}`, background: C.surface,
        }}>
          <button onClick={phase === "report" ? reset : finish} className="mf-press" style={btn(false)}>
            {phase === "report" ? `← ${t("pitch_close")}` : `← ${t("pitch_end")}`}
          </button>
          <span style={{ fontWeight: 700, color: C.text, fontFamily: F.heading }}>
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
