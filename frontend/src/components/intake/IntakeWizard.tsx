import { useEffect, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { startIntake, answerIntake, patchProfile } from "../../api";
import { C, F, card, btn } from "../../theme";
import { PixelMoufida } from "../companion/PixelMoufida";
import type { IntakeQuestion } from "../../types";

interface Props {
  onComplete: () => void;
  /** "create" (new project) shows creation copy; "update" refreshes context
   *  before re-diagnosing an existing project. */
  mode?: "create" | "update";
}

// The branch graph tops out around nine questions; used only for the progress hint.
const ESTIMATED_TOTAL = 9;

function prettify(value: string): string {
  if (/[A-Z]/.test(value) && value.includes(" ")) return value; // already a label
  return value
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function ProgressBar({ answered }: { answered: number }) {
  const step = answered + 1;
  const pct = Math.min(100, Math.round((answered / ESTIMATED_TOTAL) * 100));
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 12, color: C.muted, fontFamily: F.body }}>
          Question {step}
        </span>
        <span style={{ fontSize: 12, color: C.accent, fontFamily: F.body, fontWeight: 600 }}>
          {pct}%
        </span>
      </div>
      <div style={{ height: 6, borderRadius: 3, background: C.border }}>
        <div style={{
          height: "100%",
          width: `${pct}%`,
          borderRadius: 3,
          background: `linear-gradient(90deg, ${C.accent}, ${C.accentHover})`,
          transition: "width 0.4s cubic-bezier(0.4,0,0.2,1)",
        }} />
      </div>
    </div>
  );
}

function ChoiceGrid({ choices, selected, onSelect }: {
  choices: string[];
  selected: string;
  onSelect: (v: string) => void;
}) {
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
      gap: 10,
      marginTop: 20,
    }}>
      {choices.map((choice) => {
        const active = selected === choice;
        return (
          <button
            key={choice}
            onClick={() => onSelect(choice)}
            style={{
              background:   active ? C.accent : C.surfaceHigh,
              color:        active ? "#fff" : C.text,
              border:       `2px solid ${active ? C.accent : C.border}`,
              borderRadius: 12,
              padding:      "14px 16px",
              fontSize:     14,
              fontFamily:   F.body,
              fontWeight:   active ? 600 : 400,
              cursor:       "pointer",
              textAlign:    "left",
              transition:   "all 0.16s ease",
              lineHeight:   1.4,
            }}
          >
            {prettify(choice)}
          </button>
        );
      })}
    </div>
  );
}

export function IntakeWizard({ onComplete, mode = "create" }: Props) {
  const t         = useT();
  const projectId = useStore((s) => s.projectId);
  const lang      = useStore((s) => s.lang);
  const titleKey    = mode === "update" ? "intake_update_title" : "intake_title";
  const subtitleKey = mode === "update" ? "intake_update_subtitle" : "intake_subtitle";

  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [question, setQuestion]     = useState<IntakeQuestion | null>(null);
  const [answers, setAnswers]       = useState<Record<string, unknown>>({});
  const [selected, setSelected]     = useState("");
  const [textInput, setTextInput]   = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    startIntake(lang)
      .then((q) => setQuestion(q))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const finish = async (patch: Record<string, unknown>) => {
    if (projectId) {
      try {
        await patchProfile(projectId, patch);
      } catch (e) {
        console.warn("[intake] profile patch failed", e);
      }
    }
    onComplete();
  };

  const submit = async (raw: unknown) => {
    if (!question || submitting) return;
    setSubmitting(true);
    const nextAnswers = { ...answers, [question.id]: raw };
    try {
      const resp = await answerIntake(lang, nextAnswers);
      setAnswers(nextAnswers);
      if (resp.done) {
        await finish(resp.profile_patch ?? {});
        return;
      }
      setQuestion(resp.question ?? null);
      setSelected("");
      setTextInput("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const handleContinue = () => {
    if (!question) return;
    if (question.type === "choice") { if (selected) void submit(selected); }
    else if (question.type === "number") {
      if (textInput.trim()) void submit(Number(textInput));
    } else {
      if (textInput.trim()) void submit(textInput);
    }
  };

  const canContinue = question
    ? question.type === "choice" ? !!selected : !!textInput.trim()
    : false;

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: C.muted }}>
        {t("intake_loading")}
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        display: "flex", flexDirection: "column", alignItems: "center",
        justifyContent: "center", height: "100%", gap: 20, padding: 40,
      }}>
        <p style={{ color: C.error, fontSize: 14, textAlign: "center" }}>
          {t("intake_error")}<br />
          <span style={{ fontSize: 12, color: C.muted }}>{error}</span>
        </p>
        <button onClick={onComplete} style={{ ...btn(true), padding: "10px 28px" }}>
          {t("intake_skip")}
        </button>
      </div>
    );
  }

  if (!question) return null;

  return (
    <div style={{
      display:       "flex",
      flexDirection: "column",
      height:        "100%",
      padding:       "36px 48px",
      maxWidth:      760,
      margin:        "0 auto",
      width:         "100%",
    }}>
      <p style={{ margin: "0 0 6px", fontSize: 12, color: C.muted, fontFamily: F.body, letterSpacing: "0.06em", textTransform: "uppercase" }}>
        {t(titleKey)}
      </p>
      <h2 style={{ margin: "0 0 24px", fontSize: 22, color: C.primary, fontFamily: F.heading, fontWeight: 700 }}>
        {t(subtitleKey)}
      </h2>

      <ProgressBar answered={Object.keys(answers).length} />

      <div style={{ display: "flex", gap: 32, alignItems: "flex-start" }}>
        {/* Character */}
        <div style={{
          flexShrink: 0,
          filter: "drop-shadow(0 6px 18px rgba(111,78,55,0.22))",
        }}>
          <PixelMoufida state="idle" cssScale={1.4} />
        </div>

        {/* Question card */}
        <div style={{ ...card, flex: 1 }}>
          <p style={{ margin: 0, fontSize: 18, color: C.text, fontFamily: F.heading, fontWeight: 600, lineHeight: 1.45 }}>
            {question.question}
          </p>

          {question.type === "choice" && question.choices && (
            <ChoiceGrid choices={question.choices} selected={selected} onSelect={setSelected} />
          )}

          {question.type === "boolean" && (
            <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
              <button
                onClick={() => { void submit(true); }}
                disabled={submitting}
                style={{ ...btn(false), flex: 1, padding: "14px 16px", fontSize: 15, border: `2px solid ${C.border}` }}
              >
                {t("intake_yes")}
              </button>
              <button
                onClick={() => { void submit(false); }}
                disabled={submitting}
                style={{ ...btn(false), flex: 1, padding: "14px 16px", fontSize: 15, border: `2px solid ${C.border}` }}
              >
                {t("intake_no")}
              </button>
            </div>
          )}

          {(question.type === "text" || question.type === "number") && (
            <input
              type={question.type === "number" ? "number" : "text"}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleContinue(); }}
              placeholder={t("intake_input_placeholder")}
              autoFocus
              style={{
                display:      "block",
                marginTop:    20,
                width:        "100%",
                background:   C.surfaceHigh,
                border:       `1.5px solid ${C.border}`,
                borderRadius: 10,
                color:        C.text,
                fontSize:     15,
                fontFamily:   F.body,
                padding:      "12px 16px",
                outline:      "none",
                boxSizing:    "border-box",
              }}
            />
          )}

          {/* Continue button — booleans submit on click, so hide it for them */}
          {question.type !== "boolean" && (
            <div style={{ marginTop: 24 }}>
              <button
                onClick={handleContinue}
                disabled={!canContinue || submitting}
                style={{
                  ...btn(canContinue),
                  padding: "10px 28px",
                  fontSize: 14,
                  opacity: canContinue && !submitting ? 1 : 0.5,
                }}
              >
                {submitting ? "…" : t("intake_continue")}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
