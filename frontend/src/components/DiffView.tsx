/**
 * DiffView — renders field-level before/after diffs from the events.diff JSONB.
 * Expected shape: { [field]: { before: unknown, after: unknown } }
 * Handles nested objects, arrays, and primitives.
 */
import { C, F } from "../theme";

interface FieldDiff {
  before: unknown;
  after: unknown;
}

function isFieldDiff(v: unknown): v is FieldDiff {
  return (
    v !== null &&
    typeof v === "object" &&
    "before" in (v as object) &&
    "after" in (v as object)
  );
}

function renderValue(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "string")  return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (Array.isArray(v)) {
    if (v.length === 0) return "(empty list)";
    return v.map((item) => (typeof item === "string" ? item : JSON.stringify(item))).join(", ");
  }
  return JSON.stringify(v, null, 2);
}

interface RowProps {
  field: string;
  before: unknown;
  after: unknown;
}

function DiffRow({ field, before, after }: RowProps) {
  const changed = JSON.stringify(before) !== JSON.stringify(after);

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "160px 1fr 1fr",
      gap: 8,
      padding: "8px 0",
      borderBottom: `1px solid ${C.border}`,
      alignItems: "flex-start",
    }}>
      {/* Field name */}
      <span style={{
        fontSize: 12, fontWeight: 600, color: C.muted,
        fontFamily: F.body, textTransform: "capitalize",
        wordBreak: "break-word",
        paddingRight: 8,
      }}>
        {field.replace(/_/g, " ")}
      </span>

      {/* Before */}
      <div style={{
        background: changed ? "#FDDEDE" : C.surfaceHigh,
        borderRadius: 6, padding: "5px 8px",
        fontSize: 12, fontFamily: "monospace",
        color: changed ? C.error : C.muted,
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
        maxHeight: 120,
        overflowY: "auto",
        border: changed ? `1px solid ${C.error}30` : `1px solid ${C.border}`,
      }}>
        {renderValue(before)}
      </div>

      {/* After */}
      <div style={{
        background: changed ? "#DDFADD" : C.surfaceHigh,
        borderRadius: 6, padding: "5px 8px",
        fontSize: 12, fontFamily: "monospace",
        color: changed ? C.success : C.muted,
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
        maxHeight: 120,
        overflowY: "auto",
        border: changed ? `1px solid ${C.success}30` : `1px solid ${C.border}`,
      }}>
        {renderValue(after)}
      </div>
    </div>
  );
}

interface Props {
  diff: Record<string, unknown>;
}

export function DiffView({ diff }: Props) {
  if (!diff || Object.keys(diff).length === 0) {
    return (
      <p style={{ fontSize: 12, color: C.muted, fontFamily: F.body, margin: 0 }}>
        No diff available.
      </p>
    );
  }

  const rows: Array<{ field: string; before: unknown; after: unknown }> = [];

  for (const [field, value] of Object.entries(diff)) {
    if (isFieldDiff(value)) {
      rows.push({ field, before: value.before, after: value.after });
    } else if (typeof value === "object" && value !== null) {
      // Nested object: flatten one level
      for (const [subField, subValue] of Object.entries(value as Record<string, unknown>)) {
        if (isFieldDiff(subValue)) {
          rows.push({ field: `${field}.${subField}`, before: subValue.before, after: subValue.after });
        }
      }
    }
  }

  if (rows.length === 0) {
    return (
      <p style={{ fontSize: 12, color: C.muted, fontFamily: F.body, margin: 0 }}>
        No field-level changes recorded.
      </p>
    );
  }

  return (
    <div style={{ overflow: "hidden" }}>
      {/* Column headers */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "160px 1fr 1fr",
        gap: 8,
        marginBottom: 4,
        padding: "0 0 4px 0",
        borderBottom: `2px solid ${C.border}`,
      }}>
        <span style={{ fontSize: 11, color: C.muted, fontFamily: F.body, fontWeight: 700, textTransform: "uppercase" }}>
          Field
        </span>
        <span style={{ fontSize: 11, color: C.error, fontFamily: F.body, fontWeight: 700, textTransform: "uppercase" }}>
          Before
        </span>
        <span style={{ fontSize: 11, color: C.success, fontFamily: F.body, fontWeight: 700, textTransform: "uppercase" }}>
          After
        </span>
      </div>

      {rows.map((r) => (
        <DiffRow key={r.field} field={r.field} before={r.before} after={r.after} />
      ))}
    </div>
  );
}
