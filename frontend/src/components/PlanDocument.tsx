/**
 * PlanDocument — collapsible living plan with one section per axis.
 * Supports inline edit (fires re-generate via constraints) and PDF export.
 */
import { useState } from "react";
import { useT } from "../i18n";
import { C, F, card, btn } from "../theme";
import type { PlanSection } from "../types";
import { PlanSectionView } from "./PlanSectionView";
import { generateAxis, approveAxis } from "../api";

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

interface SectionCardProps {
  section: PlanSection;
  projectId: string;
  onUpdated: (updated: PlanSection) => void;
}

function SectionCard({ section, projectId, onUpdated }: SectionCardProps) {
  const t = useT();
  const [open, setOpen] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [editText, setEditText] = useState("");
  const [busy, setBusy] = useState(false);
  const [localContent, setLocalContent] = useState(section.content);
  const [localSummary, setLocalSummary] = useState(section.summary);

  const handleEdit = async () => {
    if (!editText.trim() || busy) return;
    setBusy(true);
    try {
      const proposal = await generateAxis(projectId, section.axis_slug, editText.trim());
      await approveAxis(projectId, section.axis_slug, proposal.content, proposal.summary);
      setLocalContent(proposal.content);
      setLocalSummary(proposal.summary);
      onUpdated({
        ...section,
        content: proposal.content,
        summary: proposal.summary,
        version: section.version + 1,
        source: "manual",
      });
      setEditMode(false);
      setEditText("");
    } catch (e) {
      console.warn("[plan-edit]", e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ ...card, overflow: "hidden" }}>
      {/* Section header */}
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          width: "100%", padding: "14px 20px",
          background: "transparent", border: "none", cursor: "pointer",
          textAlign: "left",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{
            width: 8, height: 8, borderRadius: "50%", background: C.success, flexShrink: 0,
          }} />
          <span style={{ fontSize: 15, fontWeight: 700, color: C.primary, fontFamily: F.heading }}>
            {t(AXIS_LABEL_KEYS[section.axis_slug] ?? section.axis_slug)}
          </span>
          {localSummary && (
            <span style={{ fontSize: 12, color: C.muted, fontFamily: F.body }}>
              — {localSummary}
            </span>
          )}
        </div>
        <span style={{ color: C.muted, fontSize: 16, transform: open ? "rotate(90deg)" : "none",
          transition: "transform 0.2s", display: "inline-block" }}>
          ▶
        </span>
      </button>

      {/* Section body */}
      {open && (
        <div style={{ padding: "0 20px 20px", borderTop: `1px solid ${C.border}` }}>
          <div style={{ marginTop: 16 }}>
            <PlanSectionView axis={section.axis_slug} content={localContent} />
          </div>

          {/* Inline edit controls */}
          {section.axis_slug !== "roadmap" && (
            <div style={{ marginTop: 16 }}>
              {editMode ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    placeholder={t("creation_edit_hint")}
                    rows={2}
                    style={{
                      width: "100%", background: C.surfaceHigh,
                      border: `1.5px solid ${C.border}`, borderRadius: 9,
                      color: C.text, fontSize: 13, padding: "9px 12px",
                      boxSizing: "border-box", fontFamily: F.body,
                      resize: "vertical", outline: "none",
                    }}
                  />
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      onClick={() => { void handleEdit(); }}
                      disabled={busy || !editText.trim()}
                      style={{ ...btn(true), padding: "7px 16px", fontSize: 13 }}
                    >
                      {busy ? "…" : `↩ ${t("creation_regenrate")}`}
                    </button>
                    <button
                      onClick={() => { setEditMode(false); setEditText(""); }}
                      disabled={busy}
                      style={{ ...btn(false), padding: "7px 14px", fontSize: 13 }}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setEditMode(true)}
                  style={{ ...btn(false), padding: "6px 14px", fontSize: 12 }}
                >
                  ✎ {t("edit")}
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface Props {
  sections: PlanSection[];
  projectId: string;
}

export function PlanDocument({ sections, projectId }: Props) {
  const t = useT();
  const [localSections, setLocalSections] = useState<PlanSection[]>(sections);

  const handleUpdated = (updated: PlanSection) => {
    setLocalSections((prev) =>
      prev.map((s) => (s.axis_slug === updated.axis_slug ? updated : s))
    );
  };

  const handleExportPdf = () => {
    window.print();
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {/* Toolbar */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        marginBottom: 20,
      }}>
        <h3 style={{ margin: 0, fontSize: 18, color: C.primary, fontFamily: F.heading, fontWeight: 700 }}>
          {t("creation_plan_title")}
        </h3>
        <button
          onClick={handleExportPdf}
          style={{ ...btn(false), padding: "8px 18px", fontSize: 13,
            border: `1.5px solid ${C.accent}`, color: C.accent }}
        >
          ⬇ {t("creation_export_pdf")}
        </button>
      </div>

      {/* Sections */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {localSections.length === 0 ? (
          <p style={{ color: C.muted, fontFamily: F.body, fontSize: 14 }}>
            {t("creation_plan_empty")}
          </p>
        ) : (
          localSections.map((section) => (
            <SectionCard
              key={section.axis_slug}
              section={section}
              projectId={projectId}
              onUpdated={handleUpdated}
            />
          ))
        )}
      </div>
    </div>
  );
}
