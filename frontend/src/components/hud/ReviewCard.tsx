import { useState } from "react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { submitReview } from "../../api";
import { C, card, btn } from "../../theme";
import type { Review } from "../../types";
import { PlanSectionView } from "../PlanSectionView";

function SingleReview({ review }: { review: Review }) {
  const t = useT();
  const projectId    = useStore((s) => s.projectId);
  const dismissReview = useStore((s) => s.dismissReview);

  const [editing, setEditing]   = useState(false);
  const [editText, setEditText] = useState("");
  const [loading, setLoading]   = useState(false);

  const handle = async (decision: "approve" | "edit" | "retry") => {
    if (!projectId) return;
    setLoading(true);
    try {
      await submitReview(projectId, review.axis, decision, decision === "edit" ? editText : undefined);
      dismissReview(review.axis);
    } catch (e) {
      console.warn("[review]", e);
    } finally {
      setLoading(false);
    }
  };

  const content: Record<string, unknown> =
    review.output && typeof review.output === "object"
      ? (review.output as Record<string, unknown>)
      : { value: String(review.output) };

  return (
    <div style={{ ...card, marginBottom: 12 }}>
      <p style={{ color: C.muted, fontSize: 12, margin: "0 0 6px", textTransform: "uppercase", letterSpacing: 1 }}>
        {t("review_title")} — {review.axis}
      </p>
      <div style={{
        background: C.surfaceHigh, borderRadius: 8, padding: 12,
        marginBottom: 12, border: `1px solid ${C.border}`,
        maxHeight: 280, overflowY: "auto",
      }}>
        <PlanSectionView axis={review.axis} content={content} />
      </div>

      {editing && (
        <textarea
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          placeholder={t("edit_placeholder")}
          rows={3}
          style={{
            width:        "100%",
            background:   C.surfaceHigh,
            border:       `1.5px solid ${C.border}`,
            borderRadius: 9,
            color:        C.text,
            fontSize:     13,
            padding:      "9px 12px",
            marginBottom:  8,
            boxSizing:    "border-box",
            fontFamily:   "'Plus Jakarta Sans', system-ui, sans-serif",
            resize:       "vertical",
            outline:      "none",
          }}
        />
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={() => { void handle("approve"); }} disabled={loading} style={btn()}>
          ✓ {t("approve")}
        </button>
        <button
          onClick={() => { editing ? void handle("edit") : setEditing(true); }}
          disabled={loading}
          style={btn()}
        >
          ✎ {t("edit")}
        </button>
        <button onClick={() => { void handle("retry"); }} disabled={loading} style={btn()}>
          ↺ {t("retry")}
        </button>
      </div>
    </div>
  );
}

export function ReviewCard() {
  const reviews = useStore((s) => s.reviews);
  if (reviews.length === 0) return null;
  return (
    <div>
      {reviews.map((r) => <SingleReview key={r.id} review={r} />)}
    </div>
  );
}
