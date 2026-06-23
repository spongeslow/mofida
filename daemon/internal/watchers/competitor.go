package watchers

import (
	"context"
	"crypto/md5"
	"fmt"
	"log"
	"strings"
	"time"

	"moufida/daemon/internal/redis"
)

type CompetitorWatcher struct {
	orchestratorURL string
	projectID       string
	stateFile       string
	interval        time.Duration
	pub             *redis.Publisher
}

type competitorState struct {
	Hashes  map[string]string `json:"hashes"`
	LastRun string            `json:"last_run"`
}

func NewCompetitor(orchestratorURL, projectID, stateDir string, pub *redis.Publisher, d time.Duration) Watcher {
	return &CompetitorWatcher{
		orchestratorURL: orchestratorURL,
		projectID:       projectID,
		stateFile:       projectStatePath(stateDir, "competitor_hashes.json", projectID),
		interval:        d,
		pub:             pub,
	}
}

func (w *CompetitorWatcher) Run(ctx context.Context) {
	tickLoop(ctx, "competitor", w.interval, w.tick)
}

func (w *CompetitorWatcher) tick(ctx context.Context) {
	profile, err := fetchProfile(ctx, w.orchestratorURL, w.projectID)
	if err != nil {
		log.Printf("[competitor] fetch profile: %v", err)
		return
	}

	sector, _ := profile["sector"].(string)
	targets := fetchWatchTargets(ctx, w.orchestratorURL, w.projectID)

	var state competitorState
	_ = loadJSON(w.stateFile, &state)
	if state.Hashes == nil {
		state.Hashes = map[string]string{}
	}

	observeURL := w.orchestratorURL + "/api/v1/project/" + w.projectID + "/competitor/observe"

	// --- 1. Hash-check competitor pages (profile competitors ∪ LLM targets) ---

	type tracked struct{ name, url string }
	var pages []tracked
	if market, ok := profile["market"].(map[string]any); ok {
		if competitors, ok := market["competitors"].([]any); ok {
			for _, c := range competitors {
				if comp, ok := c.(map[string]any); ok {
					name, _ := comp["name"].(string)
					url, _ := comp["url"].(string)
					if url != "" {
						pages = append(pages, tracked{name, url})
					}
				}
			}
		}
	}
	for _, c := range targets.Competitors {
		if c.URL != "" {
			pages = append(pages, tracked{c.Name, c.URL})
		}
	}

	for _, p := range pages {
		body, err := fetchPage(ctx, p.url)
		if err != nil {
			log.Printf("[competitor] fetch %s: %v", p.url, err)
			continue
		}
		hash := fmt.Sprintf("%x", md5.Sum(body))
		if prev, exists := state.Hashes[p.url]; exists && prev != hash {
			// Page changed: POST trimmed text for LLM extraction + diff + SWOT.
			payload := map[string]any{
				"name":     p.name,
				"url":      p.url,
				"raw_text": trimText(string(body), 6000),
				"source":   "page_changed",
			}
			if err := postJSON(ctx, observeURL, payload); err != nil {
				log.Printf("[competitor] observe %s: %v", p.name, err)
			} else {
				log.Printf("[competitor] page changed → observed: %s", p.name)
			}
		}
		state.Hashes[p.url] = hash
	}

	// --- 2. Scan feeds (sector seeds ∪ LLM target feeds) for name mentions ---

	names := deriveCompetitorSearchTerms(profile)
	if len(names) > 0 {
		feeds := dedup(append(sectorNewsFeeds(sector), targets.feedURLs()...))
		for _, feedURL := range feeds {
			data, err := fetchPage(ctx, feedURL)
			if err != nil {
				log.Printf("[competitor] rss %s: %v", feedURL, err)
				continue
			}
			for _, item := range parseFeed(data) {
				title := strings.ToLower(item.Title)
				for _, name := range names {
					if strings.Contains(title, name) {
						payload := map[string]any{
							"name":     name,
							"url":      item.Link,
							"source":   "news_mention",
							"headline": item.Title,
						}
						if err := postJSON(ctx, observeURL, payload); err != nil {
							log.Printf("[competitor] observe news: %v", err)
						} else {
							log.Printf("[competitor] news mention: %s in %q", name, item.Title)
						}
					}
				}
			}
		}
	}

	state.LastRun = time.Now().UTC().Format(time.RFC3339)
	saveJSON(w.stateFile, &state)
	log.Printf("[competitor] tick complete (sector=%s names=%d pages=%d)", sector, len(names), len(pages))
}
