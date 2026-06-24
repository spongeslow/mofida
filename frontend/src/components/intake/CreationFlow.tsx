import { useEffect, useRef, useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { approveAxis, finalizeProject, generateAxis, retryAxis } from "../../api";
import { C, F, card, btn } from "../../theme";
import { PixelMoufida } from "../companion/PixelMoufida";
import { IconDoc } from "../shared/icons";
import type { AxisProposal, PlanSection } from "../../types";
import { PlanSectionView } from "../PlanSectionView";
import { PlanDocument } from "../PlanDocument";

interface Props {
  onComplete: () => void;
}

const GENERATION_ORDER = [
  "ideation", "market", "product", "brand",
  "business-model", "legal", "operations", "marketing", "sales",
] as const;

type Axis = typeof GENERATION_ORDER[number];

const AXIS_LABEL_KEYS: Record<string, string> = {
  "ideation":       "axis_ideation",
  "market":         "axis_market",
  "product":        "axis_product",
  "brand":          "axis_brand",
  "business-model": "axis_business_model",
  "legal":          "axis_legal",
  "operations":     "axis_operations",
  "marketing":      "axis_marketing",
  "sales":          "axis_sales",
  "roadmap":        "axis_roadmap",
};

// Moufida's narration for each axis — explains *why* this step matters before
// the founder reviews it (analysis §1). Kept inline (fr/en/ar) so the flow is
// self-contained.
const NARRATION: Record<string, { fr: string; en: string; ar: string }> = {
  "ideation": {
    fr: "Commençons par ton idée — je vérifie qu'elle est claire, originale et défendable.",
    en: "Let's start with your idea — I check it's clear, original and defensible.",
    ar: "لنبدأ بفكرتك — أتأكد أنها واضحة وأصيلة وقابلة للدفاع عنها.",
  },
  "market": {
    fr: "Place au marché : taille, clients cibles et concurrents en Tunisie.",
    en: "Now the market: size, target customers and competitors in Tunisia.",
    ar: "الآن السوق: الحجم والعملاء المستهدفون والمنافسون في تونس.",
  },
  "product": {
    fr: "Ton produit — les fonctionnalités essentielles de ton MVP pour démarrer.",
    en: "Your product — the essential MVP features to get started.",
    ar: "منتجك — الميزات الأساسية للحد الأدنى من المنتج للانطلاق.",
  },
  "brand": {
    fr: "Ta marque et ton innovation — ce qui te rend vraiment unique.",
    en: "Your brand and innovation — what makes you truly unique.",
    ar: "علامتك التجارية وابتكارك — ما الذي يجعلك مميزًا حقًا.",
  },
  "business-model": {
    fr: "Ton modèle économique — comment tu crées et captures de la valeur.",
    en: "Your business model — how you create and capture value.",
    ar: "نموذج عملك — كيف تنشئ القيمة وتحقق الأرباح.",
  },
  "legal": {
    fr: "Le cadre légal et l'impact green — statut, conformité et durabilité.",
    en: "Legal frame and green impact — status, compliance and sustainability.",
    ar: "الإطار القانوني والأثر البيئي — الوضع والامتثال والاستدامة.",
  },
  "operations": {
    fr: "Tes opérations — ce qu'il te faut pour livrer au quotidien.",
    en: "Your operations — what you need to deliver day to day.",
    ar: "عملياتك — ما تحتاجه للتسليم يوميًا.",
  },
  "marketing": {
    fr: "Ton marketing — comment tu attires et fidélises tes clients.",
    en: "Your marketing — how you attract and retain customers.",
    ar: "تسويقك — كيف تجذب عملاءك وتحافظ عليهم.",
  },
  "sales": {
    fr: "Ta stratégie commerciale — comment tu transformes l'intérêt en ventes.",
    en: "Your sales strategy — how you turn interest into sales.",
    ar: "استراتيجيتك التجارية — كيف تحوّل الاهتمام إلى مبيعات.",
  },
};

function narrationFor(axis: string, lang: string): string {
  const n = NARRATION[axis];
  if (!n) return "";
  return lang === "en" ? n.en : lang === "ar" ? n.ar : n.fr;
}

// Persist creation-flow position so closing/reopening mid-plan resumes where the
// founder left off (analysis §1 / Phase 6). Approved sections also live server-side.
function creationKey(pid: string | null): string | null {
  return pid ? `moufida.creation.${pid}` : null;
}
function loadCreation(pid: string | null): { currentIdx: number; approved: PlanSection[] } {
  const key = creationKey(pid);
  if (key) {
    try {
      const raw = localStorage.getItem(key);
      if (raw) {
        const v = JSON.parse(raw) as { currentIdx?: number; approved?: PlanSection[] };
        const len = GENERATION_ORDER.length;
        return {
          currentIdx: Math.min(Math.max(0, v.currentIdx ?? 0), len - 1),
          approved: Array.isArray(v.approved) ? v.approved : [],
        };
      }
    } catch { /* ignore */ }
  }
  return { currentIdx: 0, approved: [] };
}

type StepStatus = "pending" | "current" | "done";

function Stepper({
  axes,
  currentIdx,
  doneCount,
}: {
  axes: readonly Axis[];
  currentIdx: number;
  doneCount: number;
}) {
  const t = useT();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {axes.map((ax, i) => {
        const status: StepStatus =
          i < currentIdx ? "done" : i === currentIdx ? "current" : "pending";
        const color =
          status === "done" ? C.success : status === "current" ? C.accent : C.border;
        const icon = status === "done" ? "✓" : status === "current" ? "►" : "·";
        return (
          <div
            key={ax}
            style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "8px 12px", borderRadius: 8,
              background: status === "current" ? `${C.accent}12` : "transparent",
            }}
          >
            <span style={{
              width: 18, height: 18, borderRadius: "50%",
              background: color,
              color: status === "pending" ? "transparent" : "#fff",
              fontSize: 11, fontWeight: 700,
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0,
            }}>
              {icon}
            </span>
            <span style={{
              fontSize: 13,
              color: status === "pending" ? C.muted : C.text,
              fontFamily: F.body,
              fontWeight: status === "current" ? 600 : 400,
            }}>
              {t(AXIS_LABEL_KEYS[ax] ?? ax)}
            </span>
          </div>
        );
      })}
      <div style={{ marginTop: 16, paddingTop: 12, borderTop: `1px solid ${C.border}` }}>
        <span style={{ fontSize: 12, color: C.muted, fontFamily: F.body }}>
          {doneCount} / {axes.length} {t("creation_axes_done")}
        </span>
      </div>
    </div>
  );
}

export function CreationFlow({ onComplete }: Props) {
  const t = useT();
  const projectId = useStore((s) => s.projectId);
  const lang = useStore((s) => s.lang);

  const savedFlow = useRef(loadCreation(projectId)).current;
  const [phase, setPhase] = useState<"generating" | "reviewing" | "finalizing" | "done" | "error">("generating");
  const [currentIdx, setCurrentIdx] = useState(savedFlow.currentIdx);
  const [proposal, setProposal] = useState<AxisProposal | null>(null);
  const [approved, setApproved] = useState<PlanSection[]>(savedFlow.approved);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editText, setEditText] = useState("");
  const [showPlan, setShowPlan] = useState(false);

  const currentAxis = GENERATION_ORDER[currentIdx] as Axis | undefined;
  const started = useRef(false);

  const fireGenerate = async (axis: string, constraints?: string) => {
    if (!projectId) return;
    setPhase("generating");
    setProposal(null);
    setEditMode(false);
    setEditText("");
    try {
      const p = await generateAxis(projectId, axis, constraints);
      setProposal(p);
      setPhase("reviewing");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase("error");
    }
  };

  useEffect(() => {
    if (!projectId || started.current || !currentAxis) return;
    started.current = true;
    void fireGenerate(currentAxis);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  // Persist position; clear once the plan is finished.
  useEffect(() => {
    const key = creationKey(projectId);
    if (!key) return;
    try {
      if (phase === "done") localStorage.removeItem(key);
      else localStorage.setItem(key, JSON.stringify({ currentIdx, approved }));
    } catch { /* ignore */ }
  }, [currentIdx, approved, phase, projectId]);

  const handleApprove = async () => {
    if (!projectId || !proposal || !currentAxis || busy) return;
    setBusy(true);
    try {
      await approveAxis(projectId, currentAxis, proposal.content, proposal.summary || undefined);
      const section: PlanSection = {
        axis_slug: currentAxis,
        version: approved.length + 1,
        content: proposal.content,
        summary: proposal.summary,
        approved: true,
        source: "generate",
        created_at: new Date().toISOString(),
      };
      const nextApproved = [...approved, section];
      setApproved(nextApproved);

      const nextIdx = currentIdx + 1;
      if (nextIdx >= GENERATION_ORDER.length) {
        // All axes done → finalize
        setPhase("finalizing");
        try {
          await finalizeProject(projectId);
        } catch (e) {
          console.warn("[finalize]", e);
        }
        setPhase("done");
      } else {
        setCurrentIdx(nextIdx);
        void fireGenerate(GENERATION_ORDER[nextIdx]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase("error");
    } finally {
      setBusy(false);
    }
  };

  const handleEdit = async () => {
    if (!projectId || !currentAxis || busy || !editText.trim()) return;
    setBusy(true);
    try {
      await fireGenerate(currentAxis, editText.trim());
    } finally {
      setBusy(false);
    }
  };

  const handleRetry = async () => {
    if (!projectId || !currentAxis || busy) return;
    setBusy(true);
    setPhase("generating");
    setProposal(null);
    try {
      const p = await retryAxis(projectId, currentAxis);
      setProposal(p);
      setPhase("reviewing");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase("error");
    } finally {
      setBusy(false);
    }
  };

  const pct =
    phase === "done" ? 100 :
    GENERATION_ORDER.length > 0
      ? Math.round((approved.length / GENERATION_ORDER.length) * 100)
      : 0;

  // ── Plan document view (after completion) ─────────────────────────────
  if (showPlan && phase === "done") {
    return (
      <div style={{ display: "flex", flexDirection: "column", height: "100%", padding: "28px 36px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
          <button onClick={() => setShowPlan(false)} style={{ ...btn(false), fontSize: 13 }}>
            ← {t("creation_back_completion")}
          </button>
          <h2 style={{ margin: 0, fontSize: 20, color: C.primary, fontFamily: F.heading, fontWeight: 700 }}>
            {t("creation_plan_title")}
          </h2>
        </div>
        <div style={{ flex: 1, overflowY: "auto" }}>
          <PlanDocument sections={approved} projectId={projectId ?? ""} />
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", padding: "28px 36px" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <p style={{
          margin: "0 0 4px", fontSize: 12, color: C.muted,
          textTransform: "uppercase", letterSpacing: "0.06em", fontFamily: F.body,
        }}>
          {t("creation_title")}
        </p>
        <h2 style={{ margin: 0, fontSize: 22, color: C.primary, fontFamily: F.heading, fontWeight: 700 }}>
          {phase === "done" ? t("creation_complete_title") :
           phase === "finalizing" ? t("creation_finalizing") :
           t("creation_in_progress")}
        </h2>
        <div style={{ height: 5, borderRadius: 3, background: C.border, marginTop: 10 }}>
          <div style={{
            height: "100%", borderRadius: 3, width: `${pct}%`,
            background: phase === "done"
              ? C.success
              : `linear-gradient(90deg, ${C.accent}, ${C.accentHover})`,
            transition: "width 0.5s cubic-bezier(0.4,0,0.2,1)",
          }} />
        </div>
      </div>

      {/* Body */}
      <div style={{ display: "flex", gap: 28, flex: 1, overflow: "hidden", minHeight: 0 }}>
        {/* Stepper sidebar */}
        <div style={{ ...card, width: 220, flexShrink: 0, overflowY: "auto", padding: "16px 12px" }}>
          <Stepper
            axes={GENERATION_ORDER}
            currentIdx={phase === "done" ? GENERATION_ORDER.length : currentIdx}
            doneCount={approved.length}
          />
        </div>

        {/* Content area */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16, overflowY: "auto" }}>

          {/* Generating spinner */}
          {phase === "generating" && (
            <div style={{ ...card, padding: "24px", display: "flex", alignItems: "center", gap: 16 }}>
              <PixelMoufida state="thinking" cssScale={0.9} />
              <div>
                <p style={{ margin: 0, fontSize: 15, color: C.text, fontFamily: F.body, fontWeight: 600 }}>
                  {t("creation_generating")} {t(AXIS_LABEL_KEYS[currentAxis ?? ""] ?? "")}…
                </p>
                <p style={{ margin: "4px 0 0", fontSize: 13, color: C.muted, fontFamily: F.body }}>
                  {t("creation_awaiting_desc")}
                </p>
              </div>
            </div>
          )}

          {/* Finalizing */}
          {phase === "finalizing" && (
            <div style={{ ...card, padding: "24px", display: "flex", alignItems: "center", gap: 16 }}>
              <PixelMoufida state="thinking" cssScale={0.9} />
              <p style={{ margin: 0, fontSize: 15, color: C.text, fontFamily: F.body, fontWeight: 600 }}>
                {t("creation_finalizing_desc")}
              </p>
            </div>
          )}

          {/* Error */}
          {phase === "error" && (
            <div style={{ ...card, borderLeft: `3px solid ${C.error}`, padding: "18px 22px" }}>
              <p style={{ margin: 0, fontSize: 14, color: C.error }}>
                {t("creation_start_error")}: {error}
              </p>
              <button
                onClick={() => currentAxis && void fireGenerate(currentAxis)}
                style={{ ...btn(false), marginTop: 14 }}
              >
                ↺ {t("retry")}
              </button>
            </div>
          )}

          {/* Proposal review card */}
          {phase === "reviewing" && proposal && currentAxis && (
            <div style={{ ...card, display: "flex", flexDirection: "column", gap: 16 }}>
              {/* Axis label */}
              <div>
                <p style={{
                  margin: "0 0 4px", fontSize: 11, color: C.muted,
                  textTransform: "uppercase", letterSpacing: 1,
                }}>
                  {t("review_title")}
                </p>
                <h3 style={{ margin: 0, fontSize: 18, color: C.primary, fontFamily: F.heading }}>
                  {t(AXIS_LABEL_KEYS[currentAxis] ?? currentAxis)}
                </h3>
                {proposal.summary && (
                  <p style={{ margin: "6px 0 0", fontSize: 13, color: C.muted, fontFamily: F.body }}>
                    {proposal.summary}
                  </p>
                )}
              </div>

              {/* Moufida narrates why this axis matters (analysis §1) */}
              {narrationFor(currentAxis, lang) && (
                <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                  <div style={{ flexShrink: 0 }}>
                    <PixelMoufida state="presenting" cssScale={0.5} />
                  </div>
                  <div style={{
                    position: "relative", flex: 1, background: `${C.accent}10`,
                    border: `1px solid ${C.accent}33`, borderRadius: 12,
                    padding: "10px 14px", marginTop: 6,
                  }}>
                    <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.55, fontFamily: F.body }}>
                      {narrationFor(currentAxis, lang)}
                    </p>
                  </div>
                </div>
              )}

              {/* Axis-aware content renderer */}
              <PlanSectionView axis={currentAxis} content={proposal.content} />

              {/* Assumptions / needs_input */}
              {proposal.assumptions?.length > 0 && (
                <div style={{
                  background: `${C.accent}0d`, borderRadius: 8,
                  padding: "10px 14px", borderLeft: `3px solid ${C.accent}`,
                }}>
                  <p style={{ margin: "0 0 6px", fontSize: 11, color: C.accent,
                    textTransform: "uppercase", letterSpacing: 1 }}>
                    {t("creation_assumptions")}
                  </p>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {proposal.assumptions.map((a, i) => (
                      <li key={i} style={{ fontSize: 13, color: C.text, lineHeight: 1.6, fontFamily: F.body }}>{a}</li>
                    ))}
                  </ul>
                </div>
              )}
              {proposal.needs_input?.length > 0 && (
                <div style={{
                  background: `${C.warning ?? "#e0a000"}0d`, borderRadius: 8,
                  padding: "10px 14px", borderLeft: `3px solid ${C.warning ?? "#e0a000"}`,
                }}>
                  <p style={{ margin: "0 0 6px", fontSize: 11, color: C.warning ?? "#e0a000",
                    textTransform: "uppercase", letterSpacing: 1 }}>
                    {t("creation_needs_input")}
                  </p>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {proposal.needs_input.map((n, i) => (
                      <li key={i} style={{ fontSize: 13, color: C.text, lineHeight: 1.6, fontFamily: F.body }}>{n}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Edit textarea */}
              {editMode && (
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  placeholder={t("edit_placeholder")}
                  rows={3}
                  style={{
                    width: "100%", background: C.surfaceHigh,
                    border: `1.5px solid ${C.border}`, borderRadius: 9,
                    color: C.text, fontSize: 13, padding: "9px 12px",
                    boxSizing: "border-box", fontFamily: F.body,
                    resize: "vertical", outline: "none",
                  }}
                />
              )}

              {/* Actions */}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button
                  onClick={() => { void handleApprove(); }}
                  disabled={busy || editMode}
                  style={{ ...btn(true), padding: "8px 20px" }}
                >
                  ✓ {t("approve")}
                </button>
                {editMode ? (
                  <>
                    <button
                      onClick={() => { void handleEdit(); }}
                      disabled={busy || !editText.trim()}
                      style={{ ...btn(true), padding: "8px 16px", background: C.accent }}
                    >
                      ↩ {t("creation_regenrate")}
                    </button>
                    <button
                      onClick={() => { setEditMode(false); setEditText(""); }}
                      disabled={busy}
                      style={{ ...btn(false), padding: "8px 14px" }}
                    >
                      ✕ {t("creation_cancel_edit")}
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setEditMode(true)}
                    disabled={busy}
                    style={{ ...btn(false), padding: "8px 16px" }}
                  >
                    ✎ {t("edit")}
                  </button>
                )}
                <button
                  onClick={() => { void handleRetry(); }}
                  disabled={busy}
                  style={{ ...btn(false), padding: "8px 16px" }}
                >
                  ↺ {t("retry")}
                </button>
              </div>
            </div>
          )}

          {/* Completion screen */}
          {phase === "done" && (
            <div style={{
              ...card, background: `${C.success}12`,
              border: `1.5px solid ${C.success}`, padding: "28px 32px", textAlign: "center",
            }}>
              <div style={{ marginBottom: 16, display: "flex", justifyContent: "center" }}>
                <PixelMoufida state="celebrating" cssScale={1.2} />
              </div>
              <h3 style={{ margin: "0 0 8px", fontSize: 20, color: C.success, fontFamily: F.heading }}>
                {t("creation_complete_title")}
              </h3>
              <p style={{ margin: "0 0 24px", fontSize: 14, color: C.muted, fontFamily: F.body }}>
                {t("creation_complete_desc")}
              </p>
              <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
                <button
                  onClick={() => setShowPlan(true)}
                  style={{ ...btn(false), padding: "12px 28px", fontSize: 14,
                    border: `1.5px solid ${C.accent}`, color: C.accent,
                    display: "inline-flex", alignItems: "center", gap: 7 }}
                >
                  <IconDoc size={15} /> {t("creation_view_plan")}
                </button>
                <button
                  onClick={onComplete}
                  style={{ ...btn(true), padding: "12px 32px", fontSize: 15 }}
                >
                  {t("creation_view_dashboard")} →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
