import { useEffect, useRef, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { debateAxis } from "../../api";

// Animate a number from its previous value to the new one (Phase 5).
function useCountUp(target: number, ms = 650): number {
  const [val, setVal] = useState(target);
  const fromRef = useRef(target);
  useEffect(() => {
    const from = fromRef.current;
    if (from === target) return;
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / ms);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(from + (target - from) * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
      else fromRef.current = target;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);
  return val;
}
import { C, SCORE_COLORS, scoreColor, card, btn } from "../../theme";
import type { BreakdownComponent, ScoreExplanation } from "../../types";

// Inline debate chat: argue a score with Moufida (analysis §3 / §17).
function DebatePanel({ scoreName }: { scoreName: string }) {
  const t = useT();
  const projectId = useStore((s) => s.projectId);
  const lang = useStore((s) => s.lang);
  const applyScoreUpdate = useStore((s) => s.applyScoreUpdate);
  const pulseCompanion = useStore((s) => s.pulseCompanion);
  const [msgs, setMsgs] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [locked, setLocked] = useState(false);

  const send = async () => {
    if (!projectId || !input.trim() || busy || locked) return;
    const msg = input.trim();
    const history = msgs.map((m) => ({ role: m.role, content: m.content }));
    setMsgs((p) => [...p, { role: "user", content: msg }]);
    setInput(""); setBusy(true);
    try {
      const r = await debateAxis(projectId, scoreName, msg, lang, history);
      setMsgs((p) => [...p, { role: "assistant", content: r.reply }]);
      if (r.score_changed && r.new_score != null) {
        applyScoreUpdate({ score_name: scoreName, score: r.new_score });
        pulseCompanion("surprised");
      }
      if (r.locked) setLocked(true);
    } catch {
      setMsgs((p) => [...p, { role: "assistant", content: "⚠︎" }]);
    } finally { setBusy(false); }
  };

  return (
    <div style={{ marginTop: 10, borderTop: `1px solid ${C.border}`, paddingTop: 10 }}>
      {msgs.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 8, maxHeight: 180, overflowY: "auto" }}>
          {msgs.map((m, i) => (
            <div key={i} className="mf-anim-row" style={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start", maxWidth: "88%",
              background: m.role === "user" ? C.primary : C.surfaceHigh,
              color: m.role === "user" ? C.bg : C.text,
              borderRadius: 12, padding: "7px 11px", fontSize: 12.5, lineHeight: 1.5,
            }}>{m.content}</div>
          ))}
        </div>
      )}
      {locked ? (
        <p style={{ margin: 0, fontSize: 12, color: C.muted }}>🔒 {t("debate_locked")}</p>
      ) : (
        <div style={{ display: "flex", gap: 6 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") void send(); }}
            placeholder={t("debate_placeholder")}
            className="mf-input"
            style={{ flex: 1, background: C.surfaceHigh, border: `1.5px solid ${C.border}`,
              borderRadius: 9, color: C.text, fontSize: 12.5, padding: "7px 10px", outline: "none" }}
          />
          <button onClick={() => { void send(); }} disabled={busy || !input.trim()} className="mf-press" style={btn(true)}>
            {busy ? "…" : t("debate_send")}
          </button>
        </div>
      )}
    </div>
  );
}

const SCORE_LABELS: Record<string, string> = {
  market: "score_market",
  commercial_offer: "score_commercial_offer",
  innovation: "score_innovation",
  scalability: "score_scalability",
  green: "score_green",
};

const SCORE_ORDER = ["market", "commercial_offer", "innovation", "scalability", "green"];

function Gauge({ name, score, breakdown, justification }: {
  name: string;
  score: number;
  breakdown: ScoreExplanation | undefined;
  justification: string | undefined;
}) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [debateOpen, setDebateOpen] = useState(false);
  const color  = scoreColor(score);
  const accent = SCORE_COLORS[name] ?? C.primary;
  const components: BreakdownComponent[] = breakdown?.components ?? [];
  const animated = useCountUp(score);

  return (
    <div style={{ ...card, minWidth: 180, flex: 1 }}>
      <p style={{ color: C.muted, fontSize: 11, margin: "0 0 6px", textTransform: "uppercase", letterSpacing: 1 }}>
        {t(SCORE_LABELS[name] ?? name)}
      </p>
      <div style={{ display: "flex", alignItems: "baseline", gap: 4, marginBottom: 8 }}>
        <span style={{ fontSize: 40, fontWeight: 700, color, lineHeight: 1 }}>
          {animated.toFixed(1)}
        </span>
        <span style={{ color: C.muted, fontSize: 16 }}>{t("score_out_of")}</span>
      </div>

      <div style={{ height: 4, borderRadius: 2, background: C.border, marginBottom: 10 }}>
        <div style={{ width: `${(animated / 5) * 100}%`, height: "100%", background: accent, borderRadius: 2, transition: "width 0.1s linear" }} />
      </div>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        <button onClick={() => setOpen((o) => !o)} style={{ ...btn(open), fontSize: 12 }}>
          {open ? "▲" : "▼"} Détails
        </button>
        <button onClick={() => setDebateOpen((o) => !o)} className="mf-press" style={{ ...btn(debateOpen), fontSize: 12 }}>
          💬 {t("debate_title")}
        </button>
      </div>

      {debateOpen && <DebatePanel scoreName={name} />}

      {open && (
        <div style={{ marginTop: 8 }}>
          {components.length > 0 && (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, color: C.muted }}>
              <thead>
                <tr>
                  {[t("sub_dimension"), t("weight"), t("value"), t("tier")].map((h) => (
                    <th key={h} style={{ textAlign: "left", padding: "3px 4px", color: C.muted, borderBottom: `1px solid ${C.border}` }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {components.map((c, i) => (
                  <tr key={i}>
                    <td style={{ padding: "3px 4px", color: C.text }}>{c.name.replace(/_/g, " ")}</td>
                    <td style={{ padding: "3px 4px" }}>{Math.round((c.weight ?? 0) * 100)}%</td>
                    <td style={{ padding: "3px 4px", color: scoreColor((c.normalised_value ?? 0) * 5) }}>
                      {(c.normalised_value ?? 0).toFixed(2)}
                    </td>
                    <td style={{ padding: "3px 4px" }}>{c.tier ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {justification && (
            <p style={{ color: C.muted, fontSize: 12, marginTop: 8, lineHeight: 1.5 }}>{justification}</p>
          )}
        </div>
      )}
    </div>
  );
}

export function ScoreGauge() {
  const t              = useT();
  const scores         = useStore((s) => s.scores);
  const scoreBreakdowns = useStore((s) => s.scoreBreakdowns);
  const justifications = useStore((s) => s.justifications);

  if (Object.keys(scores).length === 0) {
    return <p style={{ color: C.muted }}>{t("no_diagnostic")}</p>;
  }

  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
      {SCORE_ORDER.filter((name) => name in scores).map((name) => (
        <Gauge
          key={name}
          name={name}
          score={scores[name]}
          breakdown={scoreBreakdowns[name]}
          justification={justifications[name]}
        />
      ))}
    </div>
  );
}
