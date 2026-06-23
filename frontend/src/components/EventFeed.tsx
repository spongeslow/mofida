/**
 * EventFeed — chronological filterable event list for the dashboard.
 * Shows events from all four sources with Act/Manual/Ignore actions.
 * Includes a DiffView modal on "View diff".
 */
import { useEffect, useState } from "react";
import { useStore } from "../store";
import { useT } from "../i18n";
import { actOnEvent, ignoreEvent, listEvents, manualEvent } from "../api";
import { C, F, card, btn } from "../theme";
import type { EventRecord } from "../types";
import { DiffView } from "./DiffView";

const SOURCE_ICON: Record<string, string> = {
  manual: "✎",
  chat:   "💬",
  tool:   "📡",
  daemon: "🛰️",
};

const SEVERITY_COLOR: Record<string, string> = {
  critical: C.error,
  warning:  C.warning,
  info:     C.muted,
};

function AxisChip({ axis }: { axis: string }) {
  return (
    <span style={{
      background: `${C.accent}14`, borderRadius: 20,
      padding: "2px 8px", fontSize: 11, color: C.accent,
      fontFamily: F.body, fontWeight: 500,
    }}>
      {axis}
    </span>
  );
}

interface EventCardProps {
  event: EventRecord;
  onStatusChange: (id: string, status: EventRecord["status"]) => void;
}

function EventCard({ event, onStatusChange }: EventCardProps) {
  const t = useT();
  const [busy, setBusy] = useState(false);
  const [showDiff, setShowDiff] = useState(false);

  const isResolved = event.status !== "new";
  const sevColor = SEVERITY_COLOR[event.severity] ?? C.muted;

  const handleAct = async () => {
    setBusy(true);
    try {
      await actOnEvent(event.id);
      onStatusChange(event.id, "acted");
    } catch (e) { console.warn("[act]", e); }
    finally { setBusy(false); }
  };

  const handleManual = async () => {
    setBusy(true);
    try {
      await manualEvent(event.id);
      onStatusChange(event.id, "manual");
    } catch (e) { console.warn("[manual]", e); }
    finally { setBusy(false); }
  };

  const handleIgnore = async () => {
    setBusy(true);
    try {
      await ignoreEvent(event.id);
      onStatusChange(event.id, "ignored");
    } catch (e) { console.warn("[ignore]", e); }
    finally { setBusy(false); }
  };

  return (
    <div style={{
      ...card,
      padding: "14px 18px",
      borderLeft: `3px solid ${sevColor}`,
      opacity: isResolved ? 0.65 : 1,
      transition: "opacity 0.2s",
    }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
        {/* Source + summary */}
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <span title={event.source} style={{ fontSize: 16 }}>
              {SOURCE_ICON[event.source] ?? "●"}
            </span>
            <span style={{
              fontSize: 13, color: C.text, fontFamily: F.body, fontWeight: 600, lineHeight: 1.4,
            }}>
              {event.summary}
            </span>
          </div>

          {/* Axes chips */}
          {event.axes_affected.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 6 }}>
              {event.axes_affected.map((a) => <AxisChip key={a} axis={a} />)}
            </div>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <span style={{ fontSize: 11, color: C.muted, fontFamily: F.body }}>
              {new Date(event.created_at).toLocaleString()}
            </span>
            <span style={{
              fontSize: 10, color: sevColor, fontWeight: 700,
              textTransform: "uppercase", letterSpacing: 0.5,
            }}>
              {event.severity}
            </span>
            {isResolved && (
              <span style={{
                fontSize: 10, color: C.success, fontWeight: 600,
                textTransform: "uppercase", letterSpacing: 0.5,
              }}>
                {event.status}
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        {!isResolved && (
          <div style={{ display: "flex", gap: 6, flexShrink: 0, flexWrap: "wrap" }}>
            <button
              onClick={() => { void handleAct(); }}
              disabled={busy}
              style={{ ...btn(true), padding: "5px 12px", fontSize: 12 }}
              title={t("event_act_desc")}
            >
              ⚡ {t("event_act")}
            </button>
            <button
              onClick={() => { void handleManual(); }}
              disabled={busy}
              style={{ ...btn(false), padding: "5px 12px", fontSize: 12 }}
              title={t("event_manual_desc")}
            >
              ✎ {t("event_manual")}
            </button>
            <button
              onClick={() => { void handleIgnore(); }}
              disabled={busy}
              style={{ ...btn(false), padding: "5px 10px", fontSize: 12 }}
              title={t("event_ignore")}
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {/* Suggestion hint */}
      {(() => {
        if (isResolved) return null;
        const desc = (event.suggestion as Record<string, unknown>)?.description;
        if (!desc) return null;
        return (
          <p style={{ margin: "8px 0 0 24px", fontSize: 12, color: C.muted, fontFamily: F.body, lineHeight: 1.5 }}>
            → {String(desc)}
          </p>
        );
      })()}

      {/* Diff toggle */}
      {event.diff && Object.keys(event.diff).length > 0 && (
        <div style={{ marginTop: 8 }}>
          <button
            onClick={() => setShowDiff((v) => !v)}
            style={{ background: "none", border: "none", color: C.accent,
              cursor: "pointer", fontSize: 12, padding: 0, fontFamily: F.body }}
          >
            {showDiff ? "▲" : "▼"} {t("event_view_diff")}
          </button>
          {showDiff && (
            <div style={{ marginTop: 8 }}>
              <DiffView diff={event.diff} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Filter bar
type FilterStatus = "all" | "new" | "acted" | "manual" | "ignored";
type FilterSource = "all" | "manual" | "chat" | "tool" | "daemon";

interface Props {
  projectId: string;
}

export function EventFeed({ projectId }: Props) {
  const t = useT();
  const storeEvents    = useStore((s) => s.eventFeed);
  const updateStatus   = useStore((s) => s.updateEventStatus);

  const [loaded, setLoaded] = useState<EventRecord[]>([]);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("all");
  const [filterSource, setFilterSource] = useState<FilterSource>("all");
  const [loading, setLoading] = useState(false);

  const reload = () => {
    if (!projectId) return;
    setLoading(true);
    listEvents(projectId, {
      status: filterStatus !== "all" ? filterStatus : undefined,
      source: filterSource !== "all" ? filterSource : undefined,
      limit: 50,
    })
      .then((r) => setLoaded(r.events))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { reload(); }, [projectId, filterStatus, filterSource]);

  // Merge SSE-pushed events with loaded list (SSE adds new items live).
  const merged: EventRecord[] = [
    ...storeEvents.filter(
      (e) =>
        (filterStatus === "all" || e.status === filterStatus) &&
        (filterSource === "all" || e.source === filterSource) &&
        !loaded.some((l) => l.id === e.id)
    ),
    ...loaded,
  ];

  const handleStatusChange = (id: string, status: EventRecord["status"]) => {
    setLoaded((prev) => prev.map((e) => (e.id === id ? { ...e, status } : e)));
    updateStatus(id, status);
  };

  const filterBtn = (active: boolean) => ({
    ...btn(active),
    padding: "5px 12px",
    fontSize: 12,
    borderRadius: 20,
  });

  if (merged.length === 0 && !loading) {
    return (
      <div style={{ ...card, padding: "20px 24px" }}>
        <p style={{ margin: 0, color: C.muted, fontSize: 13, fontFamily: F.body }}>
          {t("event_feed_empty")}
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {/* Header + filters */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <span style={{ fontSize: 12, color: C.muted, fontFamily: F.body, textTransform: "uppercase", letterSpacing: 1 }}>
          {t("event_feed_title")}
        </span>
        <div style={{ display: "flex", gap: 4 }}>
          {(["all", "new", "acted", "ignored"] as FilterStatus[]).map((s) => (
            <button key={s} onClick={() => setFilterStatus(s)} style={filterBtn(filterStatus === s)}>
              {t(`event_status_${s}`)}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {(["all", "manual", "chat", "tool", "daemon"] as FilterSource[]).map((s) => (
            <button key={s} onClick={() => setFilterSource(s)} style={filterBtn(filterSource === s)}>
              {SOURCE_ICON[s] ?? s}
            </button>
          ))}
        </div>
        {loading && <span style={{ fontSize: 12, color: C.muted }}>…</span>}
      </div>

      {/* Event cards */}
      {merged.map((e) => (
        <EventCard key={e.id} event={e} onStatusChange={handleStatusChange} />
      ))}
    </div>
  );
}
