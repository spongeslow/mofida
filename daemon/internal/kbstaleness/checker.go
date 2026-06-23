// Package kbstaleness verifies knowledge-base resource URLs and flags changed ones.
package kbstaleness

import (
	"bytes"
	"context"
	"crypto/md5"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"
)

type Checker struct {
	ragURL    string
	stateFile string
	interval  time.Duration
}

type kbState struct {
	Hashes map[string]string `json:"hashes"`
}

type ragResource struct {
	ID           string `json:"id"`
	URL          string `json:"url"`
	LastVerified string `json:"last_verified"`
}

// New creates a Checker. stateDir is created if it doesn't exist.
func New(ragURL, stateDir string, interval time.Duration) *Checker {
	_ = os.MkdirAll(stateDir, 0755)
	return &Checker{
		ragURL:    ragURL,
		stateFile: stateDir + "/kb_hashes.json",
		interval:  interval,
	}
}

func (c *Checker) Run(ctx context.Context) {
	log.Printf("[kb-staleness] started (interval %s, rag %s)", c.interval, c.ragURL)
	c.tick(ctx)
	t := time.NewTicker(c.interval)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			log.Print("[kb-staleness] stopped")
			return
		case <-t.C:
			c.tick(ctx)
		}
	}
}

func (c *Checker) tick(ctx context.Context) {
	resources, err := c.listResources(ctx)
	if err != nil {
		log.Printf("[kb-staleness] list resources: %v", err)
		return
	}

	var state kbState
	if b, err := os.ReadFile(c.stateFile); err == nil {
		_ = json.Unmarshal(b, &state)
	}
	if state.Hashes == nil {
		state.Hashes = map[string]string{}
	}

	cutoff := time.Now().UTC().AddDate(0, 0, -90)
	flagged := 0

	for _, r := range resources {
		if r.URL == "" {
			continue
		}
		// Skip resources whose last_verified is recent enough.
		if r.LastVerified != "" {
			lv, err := time.Parse("2006-01-02", r.LastVerified)
			if err == nil && lv.After(cutoff) {
				continue
			}
		}

		body, err := c.fetchURL(ctx, r.URL)
		if err != nil {
			log.Printf("[kb-staleness] fetch %s: %v", r.URL, err)
			continue
		}
		hash := fmt.Sprintf("%x", md5.Sum(body))
		if prev, exists := state.Hashes[r.ID]; exists && prev == hash {
			state.Hashes[r.ID] = hash
			continue
		}

		if err := c.flagResource(ctx, r.ID); err != nil {
			log.Printf("[kb-staleness] flag %s: %v", r.ID, err)
		} else {
			flagged++
			log.Printf("[kb-staleness] flagged %s (content changed)", r.ID)
		}
		state.Hashes[r.ID] = hash
	}

	b, _ := json.MarshalIndent(state, "", "  ")
	_ = os.WriteFile(c.stateFile, b, 0644)
	log.Printf("[kb-staleness] tick complete, flagged=%d / %d checked", flagged, len(resources))
}

func (c *Checker) listResources(ctx context.Context) ([]ragResource, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.ragURL+"/admin/resources", nil)
	if err != nil {
		return nil, err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var result struct {
		Resources []ragResource `json:"resources"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.Resources, nil
}

func (c *Checker) fetchURL(ctx context.Context, url string) ([]byte, error) {
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
	return io.ReadAll(resp.Body)
}

func (c *Checker) flagResource(ctx context.Context, resourceID string) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		c.ragURL+"/admin/flag/"+resourceID, bytes.NewReader(nil))
	if err != nil {
		return err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return fmt.Errorf("HTTP %d", resp.StatusCode)
	}
	return nil
}
