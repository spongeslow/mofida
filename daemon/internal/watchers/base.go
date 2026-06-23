// Package watchers holds the five always-on monitors.
package watchers

import (
	"bytes"
	"context"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"sync/atomic"
	"time"
)

// Watcher is anything the daemon runs as a goroutine on a fixed cadence.
type Watcher interface {
	Run(ctx context.Context)
}

// paused is the cached control-plane pause flag. The supervisor in main.go
// refreshes it via SetPaused; tickLoop reads it before doing any work so
// pausing stops *work* without tearing down the goroutines.
var paused atomic.Bool

// SetPaused updates the cached pause flag (called by the daemon supervisor).
func SetPaused(p bool) { paused.Store(p) }

// IsPaused reports the cached pause flag.
func IsPaused() bool { return paused.Load() }

// tickLoop drives a watcher: fires tick immediately, then every interval.
// When paused, the work body is skipped but the loop keeps running.
func tickLoop(ctx context.Context, name string, interval time.Duration, tick func(ctx context.Context)) {
	log.Printf("[%s] started (interval %s)", name, interval)
	if !paused.Load() {
		tick(ctx)
	}
	t := time.NewTicker(interval)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			log.Printf("[%s] stopped", name)
			return
		case <-t.C:
			if paused.Load() {
				log.Printf("[%s] paused — skipping tick", name)
				continue
			}
			tick(ctx)
		}
	}
}

// postJSON POSTs a JSON body to the orchestrator (best-effort helper).
func postJSON(ctx context.Context, url string, payload any) error {
	b, _ := json.Marshal(payload)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(b))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", "moufida-daemon/1.0")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, resp.Body)
	if resp.StatusCode >= 400 {
		return fmt.Errorf("HTTP %d from %s", resp.StatusCode, url)
	}
	return nil
}

// fetchPage does a GET and returns the body bytes.
func fetchPage(ctx context.Context, url string) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "moufida-daemon/1.0")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("HTTP %d from %s", resp.StatusCode, url)
	}
	return io.ReadAll(resp.Body)
}

// fetchProfile loads the project profile dict from the orchestrator.
func fetchProfile(ctx context.Context, orchestratorURL, projectID string) (map[string]any, error) {
	body, err := fetchPage(ctx, orchestratorURL+"/api/v1/project/"+projectID)
	if err != nil {
		return nil, err
	}
	var state struct {
		Profile map[string]any `json:"profile"`
	}
	if err := json.Unmarshal(body, &state); err != nil {
		return nil, err
	}
	return state.Profile, nil
}

// --- Feed parser -----------------------------------------------------------

type feedItem struct {
	Title   string
	Link    string
	Summary string
	ID      string
}

type rssBody struct {
	XMLName xml.Name `xml:"rss"`
	Channel struct {
		Items []struct {
			Title       string `xml:"title"`
			Link        string `xml:"link"`
			Description string `xml:"description"`
			GUID        string `xml:"guid"`
		} `xml:"item"`
	} `xml:"channel"`
}

type atomBody struct {
	XMLName xml.Name `xml:"feed"`
	Entries []struct {
		Title string `xml:"title"`
		Link  struct {
			Href string `xml:"href,attr"`
		} `xml:"link"`
		Summary string `xml:"summary"`
		ID      string `xml:"id"`
	} `xml:"entry"`
}

// parseFeed tries RSS then Atom; returns nil if data is neither.
func parseFeed(data []byte) []feedItem {
	var rss rssBody
	if xml.Unmarshal(data, &rss) == nil && len(rss.Channel.Items) > 0 {
		out := make([]feedItem, 0, len(rss.Channel.Items))
		for _, it := range rss.Channel.Items {
			out = append(out, feedItem{Title: it.Title, Link: it.Link, Summary: it.Description, ID: it.GUID})
		}
		return out
	}
	var atom atomBody
	if xml.Unmarshal(data, &atom) == nil && len(atom.Entries) > 0 {
		out := make([]feedItem, 0, len(atom.Entries))
		for _, e := range atom.Entries {
			out = append(out, feedItem{Title: e.Title, Link: e.Link.Href, Summary: e.Summary, ID: e.ID})
		}
		return out
	}
	return nil
}

// --- State-file helpers ----------------------------------------------------

func loadJSON(path string, v any) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(b, v)
}

func saveJSON(path string, v any) {
	b, _ := json.MarshalIndent(v, "", "  ")
	_ = os.WriteFile(path, b, 0644)
}

func statePath(dir, name string) string {
	return dir + "/" + name
}

// projectStatePath keys a state file per project so swapping focus doesn't
// cross-contaminate change-detection hashes (e.g. competitor_hashes.<id>.json).
func projectStatePath(dir, name, projectID string) string {
	dot := len(name)
	for i := len(name) - 1; i >= 0; i-- {
		if name[i] == '.' {
			dot = i
			break
		}
	}
	return statePath(dir, name[:dot]+"."+projectID+name[dot:])
}

// --- Adaptive watch targets ------------------------------------------------

// WatchTargets is the merged (deterministic ∪ LLM) target set the orchestrator
// returns from GET /watch-targets. Watchers union these with derive.go seeds.
type WatchTargets struct {
	Feeds        []struct{ URL, Why string } `json:"-"`
	LegalSources []legalSource               `json:"-"`
	Keywords     []string                    `json:"keywords"`
	Competitors  []struct{ Name, URL string } `json:"-"`
}

// fetchWatchTargets GETs the merged watch targets for a project. Best-effort:
// on any error it returns a zero value and the watcher falls back to derive.go.
func fetchWatchTargets(ctx context.Context, orchestratorURL, projectID string) WatchTargets {
	var wt WatchTargets
	body, err := fetchPage(ctx, orchestratorURL+"/api/v1/project/"+projectID+"/watch-targets")
	if err != nil {
		return wt
	}
	var raw struct {
		Feeds        []map[string]any `json:"feeds"`
		LegalSources []map[string]any `json:"legal_sources"`
		Keywords     []string         `json:"keywords"`
		Competitors  []map[string]any `json:"competitors"`
	}
	if err := json.Unmarshal(body, &raw); err != nil {
		return wt
	}
	for _, f := range raw.Feeds {
		if u, _ := f["url"].(string); u != "" {
			why, _ := f["why"].(string)
			wt.Feeds = append(wt.Feeds, struct{ URL, Why string }{u, why})
		}
	}
	for _, l := range raw.LegalSources {
		if u, _ := l["url"].(string); u != "" {
			name, _ := l["name"].(string)
			wt.LegalSources = append(wt.LegalSources, legalSource{name: name, url: u})
		}
	}
	wt.Keywords = raw.Keywords
	for _, c := range raw.Competitors {
		if n, _ := c["name"].(string); n != "" {
			u, _ := c["url"].(string)
			wt.Competitors = append(wt.Competitors, struct{ Name, URL string }{n, u})
		}
	}
	return wt
}

// trimText strips HTML tags and collapses whitespace, capping at max bytes.
// Used to turn a fetched competitor page into an LLM-friendly excerpt.
func trimText(html string, max int) string {
	var b []byte
	inTag := false
	lastSpace := false
	for i := 0; i < len(html); i++ {
		c := html[i]
		switch {
		case c == '<':
			inTag = true
		case c == '>':
			inTag = false
			if !lastSpace {
				b = append(b, ' ')
				lastSpace = true
			}
		case inTag:
			// skip tag contents
		case c == ' ' || c == '\n' || c == '\t' || c == '\r':
			if !lastSpace {
				b = append(b, ' ')
				lastSpace = true
			}
		default:
			b = append(b, c)
			lastSpace = false
		}
		if len(b) >= max {
			break
		}
	}
	return string(b)
}

// feedURLs returns the watch-target feed URLs as a plain slice.
func (wt WatchTargets) feedURLs() []string {
	out := make([]string, 0, len(wt.Feeds))
	for _, f := range wt.Feeds {
		out = append(out, f.URL)
	}
	return out
}
