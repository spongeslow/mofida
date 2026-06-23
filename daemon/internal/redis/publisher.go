// Package redis publishes metric changes to the moufida:metrics channel.
package redis

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	goredis "github.com/redis/go-redis/v9"
)

// Metric is the schema published to moufida:metrics.
type Metric struct {
	ProjectID string `json:"project_id"`
	Type      string `json:"type"`
	Value     any    `json:"value"`
	Timestamp string `json:"timestamp"`
}

// Publisher sends metric events to a Redis Pub/Sub channel.
type Publisher struct {
	client  *goredis.Client
	channel string
}

// NewPublisher connects to Redis and returns a ready Publisher.
func NewPublisher(url, channel string) (*Publisher, error) {
	opt, err := goredis.ParseURL(url)
	if err != nil {
		return nil, fmt.Errorf("invalid REDIS_URL %q: %w", url, err)
	}
	client := goredis.NewClient(opt)
	if err := client.Ping(context.Background()).Err(); err != nil {
		return nil, fmt.Errorf("redis ping failed: %w", err)
	}
	log.Printf("[redis] connected channel=%s", channel)
	return &Publisher{client: client, channel: channel}, nil
}

// Publish emits a Metric to the configured channel.
func (p *Publisher) Publish(ctx context.Context, projectID, metricType string, value any) error {
	m := Metric{
		ProjectID: projectID,
		Type:      metricType,
		Value:     value,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
	}
	b, _ := json.Marshal(m)
	return p.client.Publish(ctx, p.channel, string(b)).Err()
}
