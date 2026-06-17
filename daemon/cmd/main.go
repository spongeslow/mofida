// Command moufida-daemon runs the five always-on watchers plus the nightly
// knowledge-base staleness checker. Phase 0 scaffold: every watcher starts as a
// goroutine on its real cadence and logs a heartbeat; none publishes yet. The
// Redis publisher and scraping logic are filled in during Phase 5.
package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"moufida/daemon/internal/kbstaleness"
	"moufida/daemon/internal/redis"
	"moufida/daemon/internal/watchers"
)

func main() {
	log.SetFlags(log.LstdFlags | log.Lmsgprefix)
	log.SetPrefix("[moufida-daemon] ")

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	pub := redis.NewPublisher(getenv("REDIS_URL", "redis://redis:6379/0"),
		getenv("REDIS_METRICS_CHANNEL", "moufida:metrics"))

	tasks := []watchers.Watcher{
		watchers.NewBudget(pub, 6*time.Hour),
		watchers.NewCompetitor(pub, 12*time.Hour),
		watchers.NewLegal(pub, 24*time.Hour),
		watchers.NewMilestone(pub, 24*time.Hour),
		watchers.NewTrend(pub, 7*24*time.Hour),
		kbstaleness.New(getenv("RAG_URL", "http://rag:8300"), 24*time.Hour),
	}

	var wg sync.WaitGroup
	for _, t := range tasks {
		wg.Add(1)
		go func(w watchers.Watcher) {
			defer wg.Done()
			w.Run(ctx)
		}(t)
	}

	log.Printf("started %d watchers; waiting for signal", len(tasks))
	<-ctx.Done()
	log.Print("shutdown signal received; draining watchers")
	wg.Wait()
	log.Print("stopped")
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
