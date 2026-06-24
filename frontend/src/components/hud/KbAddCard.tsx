/**
 * KbAddCard — lets the founder teach Moufida (analysis §17/§23). Wraps the
 * previously UI-less `addKbEntry()` endpoint; the note enriches RAG and bumps
 * the project's kb_version.
 */
import { useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { addKbEntry } from "../../api";
import { C, F, card, btn } from "../../theme";
import { IconBook } from "../shared/icons";

export function KbAddCard() {
  const t = useT();
  const projectId = useStore((s) => s.projectId);
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const add = async () => {
    if (!projectId || !content.trim() || busy) return;
    setBusy(true); setDone(false);
    try {
      await addKbEntry(projectId, content.trim());
      setContent(""); setDone(true);
      setTimeout(() => setDone(false), 3000);
    } catch { /* best-effort */ }
    finally { setBusy(false); }
  };

  return (
    <div style={card}>
      <h3 style={{ margin: "0 0 12px", color: C.text, fontFamily: F.heading, fontSize: 16, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ color: C.accent }}><IconBook size={17} /></span> {t("kb_add_title")}
      </h3>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={t("kb_add_placeholder")}
        rows={3}
        style={{
          width: "100%", background: C.surfaceHigh, border: `1.5px solid ${C.border}`,
          borderRadius: 10, color: C.text, fontSize: 13, padding: "9px 12px",
          boxSizing: "border-box", fontFamily: F.body, resize: "vertical", outline: "none",
          marginBottom: 10,
        }}
      />
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <button onClick={() => { void add(); }} disabled={busy || !content.trim()} className="mf-press" style={btn(true)}>
          {busy ? "…" : t("kb_add_button")}
        </button>
        {done && <span style={{ color: C.success, fontSize: 12 }}>✓ {t("kb_added")}</span>}
      </div>
    </div>
  );
}
