// Package kbstaleness nightly-verifies knowledge-base resource source URLs whose
// last_verified date has aged past 90 days, flagging changed resources for review
// via the RAG admin endpoint. Phase 0 scaffold: heartbeat only.
package kbstaleness

import (
	"context"
	"log"
	"time"
)

type Checker struct {
	ragURL   string
	interval time.Duration
}

func New(ragURL string, interval time.Duration) *Checker {
	return &Checker{ragURL: ragURL, interval: interval}
}

func (c *Checker) Run(ctx context.Context) {
	log.Printf("[kb-staleness] started (interval %s, rag %s)", c.interval, c.ragURL)
	t := time.NewTicker(c.interval)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			log.Print("[kb-staleness] stopped")
			return
		case <-t.C:
			log.Print("[kb-staleness] heartbeat")
		}
	}
}
