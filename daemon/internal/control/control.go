// Package control talks to the orchestrator's daemon control plane: it reads the
// pause flag + focused project and posts heartbeats. All calls are best-effort —
// on any network error the daemon treats itself as "not paused" and keeps the
// last known focus, so a flaky orchestrator never silently stops the watchers.
package control

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Control is the daemon control-plane state.
type Control struct {
	Paused         bool   `json:"paused"`
	Alive          bool   `json:"alive"`
	FocusProjectID string `json:"focus_project_id"`
}

var httpClient = &http.Client{Timeout: 10 * time.Second}

// Fetch GETs the current control state from the orchestrator.
func Fetch(ctx context.Context, orchestratorURL string) (Control, error) {
	var c Control
	req, err := http.NewRequestWithContext(ctx, http.MethodGet,
		orchestratorURL+"/api/v1/daemon/control", nil)
	if err != nil {
		return c, err
	}
	resp, err := httpClient.Do(req)
	if err != nil {
		return c, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return c, fmt.Errorf("control HTTP %d", resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return c, err
	}
	// focus_project_id may be JSON null → unmarshals to "".
	if err := json.Unmarshal(body, &c); err != nil {
		return c, err
	}
	return c, nil
}

// Heartbeat POSTs a liveness ping so the UI can tell "paused" from "offline".
func Heartbeat(ctx context.Context, orchestratorURL string) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		orchestratorURL+"/api/v1/daemon/heartbeat", nil)
	if err != nil {
		return err
	}
	resp, err := httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, resp.Body)
	if resp.StatusCode >= 400 {
		return fmt.Errorf("heartbeat HTTP %d", resp.StatusCode)
	}
	return nil
}

// SeedFocus points the daemon at projectID when no focus is set yet (first boot
// with MOUFIDA_PROJECT_ID). Best-effort; ignores conflicts.
func SeedFocus(ctx context.Context, orchestratorURL, projectID string) error {
	payload, _ := json.Marshal(map[string]any{"focus_project_id": projectID})
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		orchestratorURL+"/api/v1/daemon/control", bytes.NewReader(payload))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, resp.Body)
	return nil
}
