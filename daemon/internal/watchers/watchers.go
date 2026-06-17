// Package watchers holds the five always-on monitors. Phase 0 scaffold: each
// watcher ticks on its real cadence and logs a heartbeat; the scraping,
// threshold, and comparison logic lands in Phase 5.
package watchers

import (
	"context"
	"log"
	"time"

	"moufida/daemon/internal/redis"
)

// Watcher is anything the daemon runs as a goroutine.
type Watcher interface {
	Run(ctx context.Context)
}

// base provides the shared ticker loop and heartbeat.
type base struct {
	name     string
	interval time.Duration
	pub      *redis.Publisher
	tick     func()
}

func (b base) Run(ctx context.Context) {
	log.Printf("[%s] started (interval %s)", b.name, b.interval)
	t := time.NewTicker(b.interval)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			log.Printf("[%s] stopped", b.name)
			return
		case <-t.C:
			log.Printf("[%s] heartbeat", b.name)
			if b.tick != nil {
				b.tick()
			}
		}
	}
}

// NewBudget -- every 6h reads spend/limit and publishes at 80/90/100% thresholds.
func NewBudget(pub *redis.Publisher, d time.Duration) Watcher {
	return base{name: "budget", interval: d, pub: pub}
}

// NewCompetitor -- every 12h scrapes competitor RSS/pages, publishes on change.
func NewCompetitor(pub *redis.Publisher, d time.Duration) Watcher {
	return base{name: "competitor", interval: d, pub: pub}
}

// NewLegal -- daily regulatory feed scan (GDPR / Startup Act / AI Act).
func NewLegal(pub *redis.Publisher, d time.Duration) Watcher {
	return base{name: "legal", interval: d, pub: pub}
}

// NewMilestone -- daily deadline alerts at 14/7/1/0 days.
func NewMilestone(pub *redis.Publisher, d time.Duration) Watcher {
	return base{name: "milestone", interval: d, pub: pub}
}

// NewTrend -- weekly keyword-frequency scan over news feeds.
func NewTrend(pub *redis.Publisher, d time.Duration) Watcher {
	return base{name: "trend", interval: d, pub: pub}
}
