package watchers

import (
	"context"
	"log"
	"time"
)

// ComposioPoller is the desktop fallback for inbound Composio triggers: a NAT'd
// machine can't receive webhooks, so the daemon nudges the orchestrator on a
// cadence to pull recent trigger events and ingest them locally. The API key
// stays server-side — this just drives the cadence (POST /integrations/poll).
//
// It is process-lifetime and project-independent (like the kb-staleness
// checker), so it is not part of the per-project watcher batch.
type ComposioPoller struct {
	orchestratorURL string
	interval        time.Duration
}

func NewComposioPoller(orchestratorURL string, d time.Duration) Watcher {
	return &ComposioPoller{orchestratorURL: orchestratorURL, interval: d}
}

func (w *ComposioPoller) Run(ctx context.Context) {
	tickLoop(ctx, "composio", w.interval, w.tick)
}

func (w *ComposioPoller) tick(ctx context.Context) {
	url := w.orchestratorURL + "/api/v1/integrations/poll"
	if err := postJSON(ctx, url, map[string]any{}); err != nil {
		log.Printf("[composio] poll: %v", err)
		return
	}
	log.Printf("[composio] poll ok")
}
