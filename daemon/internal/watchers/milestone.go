package watchers

import (
	"context"
	"log"
	"time"

	"moufida/daemon/internal/redis"
)

var milestoneThresholds = []int{14, 7, 1, 0}

type MilestoneWatcher struct {
	orchestratorURL string
	projectID       string
	stateFile       string
	interval        time.Duration
	pub             *redis.Publisher
}

type milestoneState struct {
	// milestone name -> list of days-left thresholds already published
	Published map[string][]int `json:"published"`
}

func NewMilestone(orchestratorURL, projectID, stateDir string, pub *redis.Publisher, d time.Duration) Watcher {
	return &MilestoneWatcher{
		orchestratorURL: orchestratorURL,
		projectID:       projectID,
		stateFile:       projectStatePath(stateDir, "milestone_alerts.json", projectID),
		interval:        d,
		pub:             pub,
	}
}

func (w *MilestoneWatcher) Run(ctx context.Context) {
	tickLoop(ctx, "milestone", w.interval, w.tick)
}

func (w *MilestoneWatcher) tick(ctx context.Context) {
	profile, err := fetchProfile(ctx, w.orchestratorURL, w.projectID)
	if err != nil {
		log.Printf("[milestone] fetch profile: %v", err)
		return
	}

	milestones, _ := profile["milestones"].([]any)
	if len(milestones) == 0 {
		return
	}

	var state milestoneState
	_ = loadJSON(w.stateFile, &state)
	if state.Published == nil {
		state.Published = map[string][]int{}
	}

	today := time.Now().UTC().Truncate(24 * time.Hour)
	changed := false

	for _, m := range milestones {
		ms, ok := m.(map[string]any)
		if !ok {
			continue
		}
		name, _ := ms["name"].(string)
		deadline, _ := ms["deadline_date"].(string)
		completed, _ := ms["completed"].(bool)
		if completed || name == "" || deadline == "" {
			continue
		}

		dl, err := time.Parse("2006-01-02", deadline)
		if err != nil {
			continue
		}

		daysLeft := int(dl.UTC().Sub(today).Hours() / 24)
		for _, threshold := range milestoneThresholds {
			if daysLeft != threshold {
				continue
			}
			if intSliceContains(state.Published[name], threshold) {
				continue
			}
			v := map[string]any{
				"name":          name,
				"deadline_date": deadline,
				"days_left":     daysLeft,
			}
			if err := w.pub.Publish(ctx, w.projectID, "milestone", v); err != nil {
				log.Printf("[milestone] publish: %v", err)
				continue
			}
			state.Published[name] = append(state.Published[name], threshold)
			changed = true
			log.Printf("[milestone] published %s days_left=%d", name, daysLeft)
		}
	}

	if changed {
		saveJSON(w.stateFile, &state)
	}
}

func intSliceContains(s []int, v int) bool {
	for _, x := range s {
		if x == v {
			return true
		}
	}
	return false
}
