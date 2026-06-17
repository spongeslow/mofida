// Package redis publishes metric changes to the moufida:metrics channel.
//
// Phase 0 scaffold: the publisher logs the message it would publish. A real
// Redis client is wired in Phase 5 (kept dependency-free for now so the daemon
// builds with the standard library only).
package redis

import (
	"encoding/json"
	"log"
	"time"
)

// Metric is the schema published to moufida:metrics.
type Metric struct {
	ProjectID string      `json:"project_id"`
	Type      string      `json:"type"`
	Value     interface{} `json:"value"`
	Timestamp string      `json:"timestamp"`
}

type Publisher struct {
	url     string
	channel string
}

func NewPublisher(url, channel string) *Publisher {
	return &Publisher{url: url, channel: channel}
}

// Publish emits a metric to the channel. Currently logs only.
func (p *Publisher) Publish(projectID, metricType string, value interface{}) {
	m := Metric{
		ProjectID: projectID,
		Type:      metricType,
		Value:     value,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
	}
	b, _ := json.Marshal(m)
	log.Printf("[publish %s] %s", p.channel, string(b))
}
