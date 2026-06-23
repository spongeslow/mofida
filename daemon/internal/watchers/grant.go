package watchers

import (
	"context"
	"log"
	"time"

	"moufida/daemon/internal/redis"
)

// GrantWatcher scans curated Tunisian / regional funding sources and posts
// candidate opportunities to the orchestrator, which match-scores them against
// the project profile and extracts apply-by deadlines.
type GrantWatcher struct {
	orchestratorURL string
	projectID       string
	stateFile       string
	interval        time.Duration
	pub             *redis.Publisher
}

type grantState struct {
	Seen    map[string]bool `json:"seen"` // URL -> already posted
	LastRun string          `json:"last_run"`
}

// grantSource is a curated funding feed (RSS/Atom) tagged with its programme.
type grantSource struct{ source, url string }

// curatedGrantSources are Tunisian + regional funding/innovation news feeds.
// Entries are matched per-project by the orchestrator, so the list is broad.
var curatedGrantSources = []grantSource{
	{"startup_act", "https://www.startupact.tn/feed"},
	{"apii", "http://www.tunisieindustrie.nat.tn/fr/rss.asp"},
	{"wamda", "https://www.wamda.com/feed"},
	{"eu_calls", "https://ec.europa.eu/info/funding-tenders/opportunities/rss/calls.xml"},
	{"africarena", "https://africarena.com/feed"},
}

func NewGrant(orchestratorURL, projectID, stateDir string, pub *redis.Publisher, d time.Duration) Watcher {
	return &GrantWatcher{
		orchestratorURL: orchestratorURL,
		projectID:       projectID,
		stateFile:       projectStatePath(stateDir, "grant_seen.json", projectID),
		interval:        d,
		pub:             pub,
	}
}

func (w *GrantWatcher) Run(ctx context.Context) {
	tickLoop(ctx, "grant", w.interval, w.tick)
}

func (w *GrantWatcher) tick(ctx context.Context) {
	var state grantState
	_ = loadJSON(w.stateFile, &state)
	if state.Seen == nil {
		state.Seen = map[string]bool{}
	}

	observeURL := w.orchestratorURL + "/api/v1/project/" + w.projectID + "/opportunity/observe"
	posted := 0

	for _, src := range curatedGrantSources {
		data, err := fetchPage(ctx, src.url)
		if err != nil {
			log.Printf("[grant] fetch %s: %v", src.url, err)
			continue
		}
		for _, item := range parseFeed(data) {
			key := item.Link
			if key == "" {
				key = item.ID
			}
			if key == "" || state.Seen[key] {
				continue
			}
			payload := map[string]any{
				"title":    item.Title,
				"source":   src.source,
				"url":      item.Link,
				"raw_text": trimText(item.Title+" "+item.Summary, 3000),
			}
			if err := postJSON(ctx, observeURL, payload); err != nil {
				log.Printf("[grant] observe %q: %v", item.Title, err)
				continue
			}
			state.Seen[key] = true
			posted++
		}
	}

	state.LastRun = time.Now().UTC().Format(time.RFC3339)
	saveJSON(w.stateFile, &state)
	log.Printf("[grant] tick complete (sources=%d posted=%d)", len(curatedGrantSources), posted)
}
