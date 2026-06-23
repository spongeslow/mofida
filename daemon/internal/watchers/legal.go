package watchers

import (
	"context"
	"log"
	"strings"
	"time"

	"moufida/daemon/internal/redis"
)

type LegalWatcher struct {
	orchestratorURL string
	projectID       string
	stateFile       string
	interval        time.Duration
	pub             *redis.Publisher
}

type legalState struct {
	Seen []string `json:"seen"`
}

func NewLegal(orchestratorURL, projectID, stateDir string, pub *redis.Publisher, d time.Duration) Watcher {
	return &LegalWatcher{
		orchestratorURL: orchestratorURL,
		projectID:       projectID,
		stateFile:       projectStatePath(stateDir, "legal_seen.json", projectID),
		interval:        d,
		pub:             pub,
	}
}

func (w *LegalWatcher) Run(ctx context.Context) {
	tickLoop(ctx, "legal", w.interval, w.tick)
}

func (w *LegalWatcher) tick(ctx context.Context) {
	// Fetch live profile so sources and keywords adapt to the project's current state.
	profile, err := fetchProfile(ctx, w.orchestratorURL, w.projectID)
	if err != nil {
		log.Printf("[legal] fetch profile: %v", err)
		return
	}

	targets := fetchWatchTargets(ctx, w.orchestratorURL, w.projectID)

	sector, _ := profile["sector"].(string)
	// Sources: sector seeds ∪ LLM watch-target regulators; keywords likewise.
	sources := mergeLegalSources(sectorLegalSources(sector), targets.LegalSources)
	keywords := dedup(append(deriveLegalKeywords(profile), targets.Keywords...))

	var state legalState
	_ = loadJSON(w.stateFile, &state)
	seen := make(map[string]bool, len(state.Seen))
	for _, id := range state.Seen {
		seen[id] = true
	}
	newSeen := false

	log.Printf("[legal] tick sector=%s sources=%d keywords=%d", sector, len(sources), len(keywords))

	for _, src := range sources {
		data, err := fetchPage(ctx, src.url)
		if err != nil {
			log.Printf("[legal] fetch %s: %v", src.name, err)
			continue
		}

		items := parseFeed(data)
		if len(items) > 0 {
			// RSS/Atom feed — deduplicate by item ID.
			for _, item := range items {
				id := item.ID
				if id == "" {
					id = item.Link
				}
				if id == "" || seen[id] {
					continue
				}
				text := strings.ToLower(item.Title + " " + item.Summary)
				var matched []string
				for _, kw := range keywords {
					if strings.Contains(text, strings.ToLower(kw)) {
						matched = append(matched, kw)
					}
				}
				if len(matched) == 0 {
					continue
				}
				v := map[string]any{
					"source":           src.name,
					"title":            item.Title,
					"url":              item.Link,
					"keywords_matched": matched,
				}
				if err := w.pub.Publish(ctx, w.projectID, "legal", v); err != nil {
					log.Printf("[legal] publish: %v", err)
				}
				seen[id] = true
				state.Seen = append(state.Seen, id)
				newSeen = true
				log.Printf("[legal] published: %s — %s", src.name, item.Title)
			}
		} else {
			// HTML page — match each keyword once per source.
			body := strings.ToLower(string(data))
			for _, kw := range keywords {
				id := src.url + "::" + kw
				if seen[id] || !strings.Contains(body, strings.ToLower(kw)) {
					continue
				}
				v := map[string]any{
					"source":           src.name,
					"title":            kw + " — " + src.name,
					"url":              src.url,
					"keywords_matched": []string{kw},
				}
				if err := w.pub.Publish(ctx, w.projectID, "legal", v); err != nil {
					log.Printf("[legal] publish: %v", err)
				}
				seen[id] = true
				state.Seen = append(state.Seen, id)
				newSeen = true
				log.Printf("[legal] published keyword %q from %s", kw, src.name)
			}
		}
	}

	if newSeen {
		saveJSON(w.stateFile, &state)
	}
	log.Printf("[legal] tick complete (%d seen)", len(state.Seen))
}
