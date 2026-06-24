/**
 * PersonaChat — converse with one generated customer persona (H3).
 * Shows claim sources per reply, an objection tracker, and a close-strategy
 * card once enough exchanges have happened. The character tints to the persona.
 */
import { useEffect, useRef, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { personaChat, personaCloseStrategy } from "../../api";
import { C, F, btn } from "../../theme";
import type { CloseStrategy, Persona, PersonaChatTurn } from "../../types";
import { PixelMoufida } from "../companion/PixelMoufida";
import type { CharacterState } from "../../pixelArt/moufida";
import { CloseStrategyCard } from "./CloseStrategyCard";
import { IconCheck } from "../shared/icons";

// Persona archetype → character hue rotation for visual identity.
function personaHue(archetype: string): number {
  const a = archetype.toLowerCase();
  if (/agri|farm|coop|agro/.test(a)) return 90;
  if (/tech|dev|engineer|cto/.test(a)) return 200;
  if (/financ|invest|account/.test(a)) return 160;
  if (/manager|distrib|sme|retail/.test(a)) return 30;
  return 0;
}

export function PersonaChat({ projectId, persona, onBack }: {
  projectId: string; persona: Persona; onBack: () => void;
}) {
  const t = useT();
  const lang = useStore((s) => s.lang);
  const [turns, setTurns] = useState<PersonaChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [charState, setCharState] = useState<CharacterState>("idle");
  const [objections, setObjections] = useState<Set<string>>(new Set());
  const [resolved, setResolved] = useState<Set<string>>(new Set());
  const [strategy, setStrategy] = useState<CloseStrategy | null>(null);
  const [loadingStrategy, setLoadingStrategy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const hue = personaHue(persona.archetype);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  const founderTurns = turns.filter((x) => x.role === "founder").length;

  const send = async () => {
    if (!input.trim()) return;
    const msg = input.trim();
    const history = turns.map((x) => ({ role: x.role === "founder" ? "founder" : "persona", text: x.text }));
    setTurns((prev) => [...prev, { role: "founder", text: msg }]);
    setInput(""); setBusy(true); setCharState("thinking");
    try {
      const r = await personaChat(projectId, persona.id, msg, history, lang);
      setTurns((prev) => [...prev, {
        role: "persona", text: r.reply, claims: r.claims,
        objection: r.objection, buying_signal: r.buying_signal,
      }]);
      if (r.objection) {
        setObjections((prev) => new Set(prev).add(r.objection!));
        setCharState("alert"); setTimeout(() => setCharState("idle"), 1400);
      } else if (r.buying_signal) {
        setCharState("celebrating"); setTimeout(() => setCharState("idle"), 1400);
        // A buying signal implies the prior objection is easing.
        setResolved((prev) => new Set([...prev, ...objections]));
      } else {
        setCharState("idle");
      }
    } catch {
      setCharState("idle");
    } finally { setBusy(false); }
  };

  const getStrategy = async () => {
    setLoadingStrategy(true);
    try {
      const history = turns.map((x) => ({ role: x.role === "founder" ? "founder" : "persona", text: x.text }));
      setStrategy(await personaCloseStrategy(projectId, persona.id, history, lang));
    } catch { /* best-effort */ } finally { setLoadingStrategy(false); }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <button onClick={onBack} className="mf-press" style={btn(false)}>← {t("persona_back")}</button>
        <div style={{ filter: `hue-rotate(${hue}deg)`, flexShrink: 0 }}>
          <PixelMoufida state={charState} cssScale={0.45} />
        </div>
        <div>
          <div style={{ fontWeight: 700, color: C.text, fontFamily: F.body }}>{persona.name}</div>
          <div style={{ fontSize: 12, color: C.muted }}>{persona.archetype}{persona.region ? ` · ${persona.region}` : ""}</div>
        </div>
      </div>

      {/* Objection tracker */}
      {objections.size > 0 && (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {[...objections].map((o) => {
            const done = resolved.has(o);
            return (
              <span key={o} style={{
                display: "inline-flex", alignItems: "center", gap: 5,
                fontSize: 11, padding: "3px 9px", borderRadius: 20,
                background: done ? `${C.success}22` : `${C.error}18`,
                color: done ? C.success : C.error, border: `1px solid ${done ? C.success : C.error}44`,
              }}>
                {done
                  ? <IconCheck size={12} />
                  : <span style={{ width: 7, height: 7, borderRadius: "50%", background: C.error, flexShrink: 0 }} />}
                {o.slice(0, 40)}
              </span>
            );
          })}
        </div>
      )}

      <div ref={scrollRef} className="mf-scroll" style={{
        maxHeight: 320, overflowY: "auto", display: "flex", flexDirection: "column", gap: 10,
        padding: 4,
      }}>
        {turns.length === 0 && (
          <p style={{ color: C.muted, fontSize: 13 }}>
            {t("persona_chat_hint")} <em>{persona.top_objection}</em>
          </p>
        )}
        {turns.map((turn, i) => (
          <div key={i} className="mf-anim-row" style={{
            alignSelf: turn.role === "founder" ? "flex-end" : "flex-start", maxWidth: "85%",
            background: turn.role === "founder" ? C.primary : C.surface,
            color: turn.role === "founder" ? C.bg : C.text,
            border: `1px solid ${C.border}`, borderRadius: 14, padding: "9px 13px",
          }}>
            <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.5 }}>{turn.text}</p>
            {turn.role === "persona" && turn.claims && turn.claims.length > 0 && (
              <details style={{ marginTop: 6 }}>
                <summary style={{ cursor: "pointer", fontSize: 11, color: C.muted }}>{t("persona_claim_sources")}</summary>
                <ul style={{ margin: "4px 0 0", paddingLeft: 16, fontSize: 11, color: C.muted }}>
                  {turn.claims.map((c, j) => <li key={j}>{c.claim} — <em>{c.source_ref}</em></li>)}
                </ul>
              </details>
            )}
          </div>
        ))}
        {busy && <p style={{ color: C.muted, fontSize: 12 }}>…</p>}
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") void send(); }}
          placeholder={t("persona_input_placeholder")}
          className="mf-input"
          style={{ flex: 1, background: C.surfaceHigh, border: `1.5px solid ${C.border}`,
                   borderRadius: 10, color: C.text, fontSize: 13.5, padding: "9px 12px",
                   fontFamily: F.body, outline: "none" }}
        />
        <button onClick={send} disabled={busy || !input.trim()} className="mf-press" style={btn(true)}>
          {t("send")} →
        </button>
      </div>

      {founderTurns >= 3 && !strategy && (
        <button onClick={getStrategy} disabled={loadingStrategy} className="mf-press"
          style={{ ...btn(false), alignSelf: "flex-start" }}>
          {loadingStrategy ? "…" : t("persona_get_strategy")}
        </button>
      )}
      {strategy && <CloseStrategyCard strategy={strategy} />}
    </div>
  );
}
