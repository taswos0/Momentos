package queue

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/redis/go-redis/v9"
	"github.com/transmedia-alchemist/api-gateway/models"
)

const (
	ScrapingQueue  = "queue:scraping"
	StatusChannel  = "channel:status"
)

// Client wraps the Redis client with domain-specific queue operations.
type Client struct {
	rdb *redis.Client
}

// New creates a connected Redis queue client.
func New(addr string) (*Client, error) {
	rdb := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: "",
		DB:       0,
	})

	if err := rdb.Ping(context.Background()).Err(); err != nil {
		return nil, fmt.Errorf("redis connection failed: %w", err)
	}

	return &Client{rdb: rdb}, nil
}

// PublishJob pushes a job onto the scraping queue for the Rust engine to consume.
func (c *Client) PublishJob(ctx context.Context, job *models.Job) error {
	payload, err := json.Marshal(job)
	if err != nil {
		return fmt.Errorf("failed to marshal job: %w", err)
	}
	return c.rdb.LPush(ctx, ScrapingQueue, payload).Err()
}

// GetStatus retrieves the latest status for a given jobID from Redis.
func (c *Client) GetStatus(ctx context.Context, jobID string) (*models.JobStatus, error) {
	key := fmt.Sprintf("status:%s", jobID)
	val, err := c.rdb.Get(ctx, key).Result()
	if err == redis.Nil {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	var status models.JobStatus
	if err := json.Unmarshal([]byte(val), &status); err != nil {
		return nil, err
	}
	return &status, nil
}

// SubscribeStatus returns a Redis PubSub subscription for a specific job's status channel.
func (c *Client) SubscribeStatus(ctx context.Context, jobID string) *redis.PubSub {
	channel := fmt.Sprintf("%s:%s", StatusChannel, jobID)
	return c.rdb.Subscribe(ctx, channel)
}

// Close closes the underlying Redis connection.
func (c *Client) Close() error {
	return c.rdb.Close()
}
