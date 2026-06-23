import { useEffect } from "react";
import { useStore } from "../store";

interface SSEFrame {
  event: string;
  payload: Record<string, unknown>;
}

export function SSEConsumer({ projectId }: { projectId: string | null }): null {
  // Individual action selectors — stable function refs, never trigger re-renders
  const applyScoreUpdate    = useStore((s) => s.applyScoreUpdate);
  const applyAlert          = useStore((s) => s.applyAlert);
  const applyRoadmapUpdate  = useStore((s) => s.applyRoadmapUpdate);
  const applyReviewReady    = useStore((s) => s.applyReviewReady);
  const applyMaturityUpdate = useStore((s) => s.applyMaturityUpdate);
  const applyEventNew        = useStore((s) => s.applyEventNew);
  const setRoadmapStale      = useStore((s) => s.setRoadmapStale);
  const bumpHorizonComplete  = useStore((s) => s.bumpHorizonComplete);
  const applyDaemonStatus    = useStore((s) => s.applyDaemonStatus);
  const bumpCompetitor       = useStore((s) => s.bumpCompetitor);
  const bumpOpportunity      = useStore((s) => s.bumpOpportunity);
  const bumpConcept          = useStore((s) => s.bumpConcept);
  const pulseCompanion       = useStore((s) => s.pulseCompanion);
  const setSseConnected      = useStore((s) => s.setSseConnected);

  useEffect(() => {
    if (!projectId) return;

    // Distinct path from the REST events list (which lives at /events) — the
    // SSE stream is served at /events/stream to avoid a route collision.
    const es = new EventSource(`http://localhost:8001/api/v1/project/${projectId}/events/stream`);
    es.onopen = () => setSseConnected(true);

    es.onmessage = (e: MessageEvent<string>) => {
      let frame: SSEFrame;
      try {
        frame = JSON.parse(e.data) as SSEFrame;
      } catch {
        return;
      }
      switch (frame.event) {
        case "score_update":
          applyScoreUpdate(frame.payload as Parameters<typeof applyScoreUpdate>[0]);
          break;
        case "alert":
          applyAlert(frame.payload as Parameters<typeof applyAlert>[0]);
          if ((frame.payload as { severity?: string }).severity === "critical")
            pulseCompanion("alert");
          break;
        case "roadmap_update":
          applyRoadmapUpdate(frame.payload as Parameters<typeof applyRoadmapUpdate>[0]);
          break;
        case "review_ready":
          applyReviewReady(frame.payload as Parameters<typeof applyReviewReady>[0]);
          pulseCompanion("surprised");
          break;
        case "maturity_update":
          applyMaturityUpdate(frame.payload as Parameters<typeof applyMaturityUpdate>[0]);
          break;
        case "event_new":
          // A new event arrived — add to the feed (partial; full fetch on mount)
          applyEventNew(frame.payload as unknown as Parameters<typeof applyEventNew>[0]);
          break;
        case "kb_updated":
          // KB changed → mark roadmap potentially stale
          setRoadmapStale(true);
          break;
        case "horizon_complete":
          // Celebration: advance recorded, roadmap regenerated with next horizon
          bumpHorizonComplete();
          pulseCompanion("celebrating");
          break;
        case "daemon_status":
          applyDaemonStatus(frame.payload as Parameters<typeof applyDaemonStatus>[0]);
          break;
        case "competitor_update":
          bumpCompetitor();
          break;
        case "opportunity_new":
          bumpOpportunity();
          break;
        case "concept_update":
          // Daemon-triggered re-run refreshed the concept breakdown.
          bumpConcept();
          break;
        case "watch_targets_updated":
          // Targets re-derived — nothing to render directly; competitor/feed data
          // will follow on the next daemon tick.
          break;
      }
    };

    es.onerror = () => { setSseConnected(false); es.close(); };

    return () => { setSseConnected(false); es.close(); };
  }, [projectId, applyScoreUpdate, applyAlert, applyRoadmapUpdate, applyReviewReady,
      applyMaturityUpdate, applyEventNew, setRoadmapStale, bumpHorizonComplete,
      applyDaemonStatus, bumpCompetitor, bumpOpportunity, bumpConcept,
      pulseCompanion, setSseConnected]);

  return null;
}
