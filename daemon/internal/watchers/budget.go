package watchers

import (
	"context"
	"log"
	"time"

	"moufida/daemon/internal/redis"
)

// BudgetWatcher fetches the project profile and publishes runway alerts.
type BudgetWatcher struct {
	orchestratorURL string
	projectID       string
	interval        time.Duration
	pub             *redis.Publisher
}

func NewBudget(orchestratorURL, projectID string, pub *redis.Publisher, d time.Duration) Watcher {
	return &BudgetWatcher{
		orchestratorURL: orchestratorURL,
		projectID:       projectID,
		interval:        d,
		pub:             pub,
	}
}

func (w *BudgetWatcher) Run(ctx context.Context) {
	tickLoop(ctx, "budget", w.interval, w.tick)
}

func (w *BudgetWatcher) tick(ctx context.Context) {
	profile, err := fetchProfile(ctx, w.orchestratorURL, w.projectID)
	if err != nil {
		log.Printf("[budget] fetch profile: %v", err)
		return
	}

	finance, ok := profile["finance"].(map[string]any)
	if !ok {
		return
	}
	runway, ok := finance["runway_months"].(float64)
	if !ok {
		return
	}

	var severity string
	switch {
	case runway < 1:
		severity = "fatal"
	case runway < 3:
		severity = "critical"
	case runway < 6:
		severity = "warning"
	default:
		return
	}

	v := map[string]any{"runway_months": runway, "severity": severity}
	if err := w.pub.Publish(ctx, w.projectID, "budget", v); err != nil {
		log.Printf("[budget] publish: %v", err)
		return
	}
	log.Printf("[budget] published runway=%.1f severity=%s", runway, severity)
}
