// Command moufida-daemon runs the always-on watchers plus the nightly
// knowledge-base staleness checker.
//
// The project it watches is a *runtime* input, not a boot input: a supervisor
// loop polls the orchestrator control plane (pause flag + focused project),
// emits a heartbeat, and hot-swaps the project-scoped watchers when the focused
// project changes — no restart, no MOUFIDA_PROJECT_ID required. The env var, if
// set, is only used to seed the focus on first boot.
package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"moufida/daemon/internal/control"
	"moufida/daemon/internal/kbstaleness"
	"moufida/daemon/internal/redis"
	"moufida/daemon/internal/watchers"
)

const nilUUID = "00000000-0000-0000-0000-000000000000"

// heartbeatInterval is the supervisor cadence: heartbeat + control poll. Kept
// short so liveness is fresh and focus changes apply promptly.
const heartbeatInterval = 30 * time.Second

func main() {
	log.SetFlags(log.LstdFlags | log.Lmsgprefix)
	log.SetPrefix("[moufida-daemon] ")

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	pub, err := redis.NewPublisher(mustenv("REDIS_URL"), mustenv("REDIS_METRICS_CHANNEL"))
	if err != nil {
		log.Fatalf("redis: %v", err)
	}

	orchestratorURL := mustenv("ORCHESTRATOR_URL")
	dir := stateDir()
	if err := os.MkdirAll(dir, 0755); err != nil {
		log.Fatalf("create state dir %s: %v", dir, err)
	}

	// Project-independent watchers run for the whole process lifetime and
	// survive project hot-swaps: the kb-staleness checker and the Composio poll
	// fallback (pulls inbound triggers for NAT'd desktops).
	var wg sync.WaitGroup
	lifetime := []watchers.Watcher{
		kbstaleness.New(mustenv("RAG_URL"), dir, 24*time.Hour),
		watchers.NewComposioPoller(orchestratorURL, 5*time.Minute),
	}
	for _, lw := range lifetime {
		wg.Add(1)
		go func(w watchers.Watcher) {
			defer wg.Done()
			w.Run(ctx)
		}(lw)
	}

	// First-boot seed: if no project is focused yet but MOUFIDA_PROJECT_ID is
	// set, push it once so existing dev setups keep working.
	if seed := os.Getenv("MOUFIDA_PROJECT_ID"); seed != "" && seed != nilUUID {
		if c, err := control.Fetch(ctx, orchestratorURL); err == nil && c.FocusProjectID == "" {
			if err := control.SeedFocus(ctx, orchestratorURL, seed); err != nil {
				log.Printf("seed focus failed: %v", err)
			} else {
				log.Printf("seeded focus from MOUFIDA_PROJECT_ID=%s", seed)
			}
		}
	}

	log.Printf("supervisor started (heartbeat %s); waiting for a focused project", heartbeatInterval)
	supervise(ctx, orchestratorURL, dir, pub)

	log.Print("shutdown signal received; draining watchers")
	wg.Wait()
	log.Print("stopped")
}

// supervise polls the control plane, mirrors the pause flag, and hot-swaps the
// project-scoped watchers whenever the focused project changes.
func supervise(ctx context.Context, orchestratorURL, dir string, pub *redis.Publisher) {
	var (
		currentFocus  string
		cancelCurrent context.CancelFunc
		projectWG     sync.WaitGroup
	)

	stopCurrent := func() {
		if cancelCurrent != nil {
			cancelCurrent()
			projectWG.Wait() // let the old batch drain before swapping
			cancelCurrent = nil
		}
	}
	defer stopCurrent()

	t := time.NewTicker(heartbeatInterval)
	defer t.Stop()

	apply := func() {
		// Heartbeat first so the UI sees liveness even if control read fails.
		if err := control.Heartbeat(ctx, orchestratorURL); err != nil {
			log.Printf("heartbeat: %v", err)
		}
		c, err := control.Fetch(ctx, orchestratorURL)
		if err != nil {
			log.Printf("control fetch: %v (keeping focus=%q)", err, currentFocus)
			return
		}
		watchers.SetPaused(c.Paused)

		newFocus := c.FocusProjectID
		if newFocus == nilUUID {
			newFocus = ""
		}
		if newFocus == currentFocus {
			return
		}

		// Focus changed → tear down the old batch, start a fresh one.
		log.Printf("focus change: %q → %q", currentFocus, newFocus)
		stopCurrent()
		currentFocus = newFocus
		if newFocus == "" {
			log.Printf("no project focused — project watchers idle")
			return
		}

		// Refresh adaptive watch targets for the newly focused project before
		// its watchers start (best-effort; watchers fall back to derive.go).
		refreshWatchTargets(ctx, orchestratorURL, newFocus)

		var childCtx context.Context
		childCtx, cancelCurrent = context.WithCancel(ctx)
		batch := []watchers.Watcher{
			watchers.NewBudget(orchestratorURL, newFocus, pub, 6*time.Hour),
			watchers.NewCompetitor(orchestratorURL, newFocus, dir, pub, 12*time.Hour),
			watchers.NewLegal(orchestratorURL, newFocus, dir, pub, 24*time.Hour),
			watchers.NewMilestone(orchestratorURL, newFocus, dir, pub, 24*time.Hour),
			watchers.NewTrend(orchestratorURL, newFocus, dir, pub, 7*24*time.Hour),
			watchers.NewGrant(orchestratorURL, newFocus, dir, pub, 24*time.Hour),
		}
		for _, w := range batch {
			projectWG.Add(1)
			go func(w watchers.Watcher) {
				defer projectWG.Done()
				w.Run(childCtx)
			}(w)
		}
		log.Printf("started %d project watchers for %s", len(batch), newFocus)
	}

	apply() // act immediately, then on each tick
	for {
		select {
		case <-ctx.Done():
			return
		case <-t.C:
			apply()
		}
	}
}

// refreshWatchTargets asks the orchestrator to (re-)derive the LLM watch targets
// for a project. Best-effort: the watchers GET the merged result themselves.
func refreshWatchTargets(ctx context.Context, orchestratorURL, projectID string) {
	url := orchestratorURL + "/api/v1/project/" + projectID + "/watch-targets/refresh"
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, nil)
	if err != nil {
		return
	}
	resp, err := (&http.Client{Timeout: 5 * time.Minute}).Do(req)
	if err != nil {
		log.Printf("watch-targets refresh: %v", err)
		return
	}
	resp.Body.Close()
	log.Printf("watch-targets refresh for %s: HTTP %d", projectID, resp.StatusCode)
}

func mustenv(key string) string {
	v := os.Getenv(key)
	if v == "" {
		log.Fatalf("required env var %s is not set", key)
	}
	return v
}

func stateDir() string {
	if d := os.Getenv("DAEMON_STATE_DIR"); d != "" {
		return d
	}
	return "/tmp/moufida-daemon-state"
}
