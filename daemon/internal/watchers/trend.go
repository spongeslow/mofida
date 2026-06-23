package watchers

import (
	"context"
	"log"
	"math"
	"strings"
	"time"

	"moufida/daemon/internal/redis"
)

type TrendWatcher struct {
	orchestratorURL string
	projectID       string
	stateFile       string
	interval        time.Duration
	pub             *redis.Publisher
}

type trendState struct {
	// ISO week-start date -> keyword -> count
	Counts map[string]map[string]int `json:"counts"`
}

func NewTrend(orchestratorURL, projectID, stateDir string, pub *redis.Publisher, d time.Duration) Watcher {
	return &TrendWatcher{
		orchestratorURL: orchestratorURL,
		projectID:       projectID,
		stateFile:       projectStatePath(stateDir, "trend_counts.json", projectID),
		interval:        d,
		pub:             pub,
	}
}

func (w *TrendWatcher) Run(ctx context.Context) {
	tickLoop(ctx, "trend", w.interval, w.tick)
}

func (w *TrendWatcher) tick(ctx context.Context) {
	profile, err := fetchProfile(ctx, w.orchestratorURL, w.projectID)
	if err != nil {
		log.Printf("[trend] fetch profile: %v", err)
		return
	}

	targets := fetchWatchTargets(ctx, w.orchestratorURL, w.projectID)

	// Keywords: profile-derived ∪ LLM watch-target keywords — specific to this project.
	keywords := dedup(append(deriveTrendKeywords(profile), targets.Keywords...))
	if len(keywords) == 0 {
		log.Printf("[trend] no trend keywords derived from profile, skipping")
		return
	}

	sector, _ := profile["sector"].(string)
	feeds := dedup(append(sectorNewsFeeds(sector), targets.feedURLs()...))

	log.Printf("[trend] tick sector=%s feeds=%d keywords=%v", sector, len(feeds), keywords)

	// Count keyword hits across all sector-appropriate feeds this week.
	current := make(map[string]int, len(keywords))
	for _, feedURL := range feeds {
		data, err := fetchPage(ctx, feedURL)
		if err != nil {
			log.Printf("[trend] rss %s: %v", feedURL, err)
			continue
		}
		for _, item := range parseFeed(data) {
			text := strings.ToLower(item.Title + " " + item.Summary)
			for _, kw := range keywords {
				if strings.Contains(text, strings.ToLower(kw)) {
					current[kw]++
				}
			}
		}
	}

	var state trendState
	_ = loadJSON(w.stateFile, &state)
	if state.Counts == nil {
		state.Counts = map[string]map[string]int{}
	}

	thisWeek := mondayISO(time.Now().UTC())
	lastWeek := mondayISO(time.Now().UTC().Add(-7 * 24 * time.Hour))
	prev := state.Counts[lastWeek]

	for _, kw := range keywords {
		curr := current[kw]
		old := 0
		if prev != nil {
			old = prev[kw]
		}
		if old == 0 {
			// No baseline yet — store counts but don't alert.
			continue
		}
		changePct := (float64(curr-old) / float64(old)) * 100
		if math.Abs(changePct) <= 50 {
			continue
		}
		direction := "up"
		if changePct < 0 {
			direction = "down"
		}
		v := map[string]any{
			"keyword":        kw,
			"previous_count": old,
			"current_count":  curr,
			"change_pct":     changePct,
			"direction":      direction,
		}
		if err := w.pub.Publish(ctx, w.projectID, "trend", v); err != nil {
			log.Printf("[trend] publish: %v", err)
		} else {
			log.Printf("[trend] keyword=%s change=%.0f%% (%s)", kw, changePct, direction)
		}
	}

	state.Counts[thisWeek] = current
	saveJSON(w.stateFile, &state)
	log.Printf("[trend] tick complete, keywords=%d", len(keywords))
}

func mondayISO(t time.Time) string {
	weekday := int(t.Weekday())
	if weekday == 0 {
		weekday = 7
	}
	monday := t.AddDate(0, 0, -(weekday - 1))
	return monday.Format("2006-01-02")
}
