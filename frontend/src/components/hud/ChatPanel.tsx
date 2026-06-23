import { useEffect, useRef, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { chat } from "../../api";
import { C, F, btn, card, inputStyle } from "../../theme";
import { startListening } from "../../voice/stt";
import { speak } from "../../voice/tts";
import { PixelMoufida } from "../companion/PixelMoufida";
import type { VoiceState } from "../../types";

interface Message {
  role: "user" | "assistant";
  text: string;
}

function voiceToPixelState(v: VoiceState): string {
  switch (v) {
    case "listening":    return "listening";
    case "transcribing": return "thinking";
    case "processing":   return "thinking";
    case "speaking":     return "speaking";
    default:             return "idle";
  }
}

export function ChatPanel() {
  const t = useT();
  const projectId     = useStore((s) => s.projectId);
  const lang          = useStore((s) => s.lang);
  const voiceState    = useStore((s) => s.voiceState);
  const setVoiceState = useStore((s) => s.setVoiceState);
  const voiceRequest  = useStore((s) => s.voiceRequest);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput]       = useState("");
  const [sending, setSending]   = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Persist chat history per project so it survives navigation/refresh (Phase 6).
  useEffect(() => {
    if (!projectId) { setMessages([]); return; }
    try {
      const raw = localStorage.getItem(`moufida.chat.${projectId}`);
      setMessages(raw ? (JSON.parse(raw) as Message[]) : []);
    } catch { setMessages([]); }
  }, [projectId]);

  useEffect(() => {
    if (!projectId) return;
    try { localStorage.setItem(`moufida.chat.${projectId}`, JSON.stringify(messages)); } catch { /* ignore */ }
  }, [messages, projectId]);

  const charState = voiceToPixelState(voiceState);

  const addMsg = (role: Message["role"], text: string) => {
    setMessages((prev) => {
      const next = [...prev, { role, text }];
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
      return next;
    });
  };

  const send = async (text: string) => {
    if (!projectId || !text.trim() || sending) return;
    setSending(true);
    addMsg("user", text);
    setInput("");
    try {
      setVoiceState("processing");
      const { reply } = await chat(projectId, text, lang);
      addMsg("assistant", reply);
      await speak(reply, lang);
    } catch (e) {
      addMsg("assistant", `[Erreur: ${e instanceof Error ? e.message : "inconnue"}]`);
    } finally {
      setSending(false);
      setVoiceState("idle");
    }
  };

  const handleVoice = async () => {
    if (voiceState !== "idle") return;
    try {
      const transcript = await startListening();
      if (transcript.trim()) await send(transcript);
    } catch (e) {
      console.warn("[voice]", e);
      setVoiceState("idle");
    }
  };

  // External voice requests (Ctrl+Shift+V)
  useEffect(() => {
    if (voiceRequest > 0) void handleVoice();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voiceRequest]);

  const voiceLabel =
    charState === "listening" ? t("listening")  :
    charState === "speaking"  ? t("speaking")   :
    charState === "thinking"  ? "…"             : null;


  return (
    <div style={{
      ...card,
      display:       "flex",
      flexDirection: "column",
      height:        460,
      padding:       0,
      overflow:      "hidden",
    }}>
      {/* Header with mini avatar */}
      <div style={{
        display:        "flex",
        alignItems:     "center",
        gap:             12,
        padding:        "14px 20px",
        borderBottom:   `1px solid ${C.border}`,
        background:     C.surfaceHigh,
        borderRadius:   "16px 16px 0 0",
        flexShrink:      0,
      }}>
        <div style={{
          filter:     "drop-shadow(0 2px 6px rgba(111,78,55,0.18))",
          flexShrink: 0,
        }}>
          <PixelMoufida state={charState} cssScale={0.55} />
        </div>
        <div style={{ flex: 1 }}>
          <p style={{
            margin: 0,
            fontFamily: F.heading,
            fontSize: 16,
            color: C.primary,
            fontWeight: 700,
          }}>
            {t("moufida")}
          </p>
          {voiceLabel ? (
            <p style={{ margin: 0, fontSize: 12, color: C.accent, fontWeight: 500 }}>
              {voiceLabel}
            </p>
          ) : (
            <p style={{ margin: 0, fontSize: 12, color: C.muted }}>
              {t("wake_prompt")}
            </p>
          )}
        </div>
      </div>

      {/* Message list */}
      <div className="mf-scroll" style={{ flex: 1, overflowY: "auto", padding: "16px 20px" }}>
        {messages.length === 0 && (
          <div style={{
            display:        "flex",
            flexDirection:  "column",
            alignItems:     "center",
            justifyContent: "center",
            height:         "100%",
            gap:             8,
          }}>
            <p style={{ color: C.muted, fontSize: 14, textAlign: "center", lineHeight: 1.6 }}>
              {t("wake_prompt")}
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{
            display:        "flex",
            justifyContent: m.role === "user" ? "flex-end" : "flex-start",
            marginBottom:   10,
          }}>
            <div style={{
              maxWidth:     "76%",
              background:   m.role === "user"
                ? C.surfaceHigh
                : `${C.accent}1A`,
              borderRadius: m.role === "user"
                ? "14px 14px 4px 14px"
                : "14px 14px 14px 4px",
              padding:      "9px 14px",
              fontSize:     14,
              color:        m.role === "user" ? C.text : C.text,
              lineHeight:   1.55,
              fontFamily:   F.body,
              boxShadow:    "0 1px 4px rgba(111,78,55,0.07)",
            }}>
              {m.text}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div style={{
        display:       "flex",
        gap:            10,
        padding:       "14px 20px",
        borderTop:     `1px solid ${C.border}`,
        background:    C.surfaceHigh,
        borderRadius:  "0 0 16px 16px",
        flexShrink:    0,
      }}>
        <button
          onClick={() => { void handleVoice(); }}
          disabled={voiceState !== "idle"}
          title={t("start_voice")}
          style={{
            ...btn(voiceState !== "idle"),
            padding:      "0 14px",
            height:       40,
            fontSize:     18,
            borderRadius: 10,
            flexShrink:   0,
          }}
        >
          🎤
        </button>
        <input
          className="mf-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") void send(input); }}
          placeholder={t("chat_placeholder")}
          style={{
            ...inputStyle,
            flex:   1,
            height: 40,
          }}
        />
        <button
          onClick={() => { void send(input); }}
          disabled={sending || !input.trim()}
          style={{
            ...btn(true),
            height:       40,
            padding:      "0 18px",
            borderRadius: 10,
            flexShrink:   0,
          }}
        >
          {t("send")}
        </button>
      </div>
    </div>
  );
}
