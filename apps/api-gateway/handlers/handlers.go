package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/transmedia-alchemist/api-gateway/models"
	"github.com/transmedia-alchemist/api-gateway/queue"
)

// Handler holds shared dependencies for all HTTP handlers.
type Handler struct {
	Queue *queue.Client
}

// New creates a Handler with the given queue client.
func New(q *queue.Client) *Handler {
	return &Handler{Queue: q}
}

// Extract accepts a URL and content type, creates a job, and queues it for processing.
//
// POST /api/v1/extract
// Body: { "url": "https://...", "type": "tourism" | "course" }
func (h *Handler) Extract(c *gin.Context) {
	var req models.ExtractionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	job := &models.Job{
		ID:        uuid.NewString(),
		URL:       req.URL,
		Type:      req.Type,
		CreatedAt: time.Now().UnixMilli(),
	}

	if err := h.Queue.PublishJob(c.Request.Context(), job); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to queue job"})
		return
	}

	c.JSON(http.StatusAccepted, gin.H{
		"job_id":  job.ID,
		"status":  "queued",
		"message": "The Alchemist is beginning content extraction — stream progress at /api/v1/stream/" + job.ID,
	})
}

// GetStatus returns the latest known status for a job.
//
// GET /api/v1/status/:jobId
func (h *Handler) GetStatus(c *gin.Context) {
	jobID := c.Param("jobId")
	if jobID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "missing jobId"})
		return
	}

	status, err := h.Queue.GetStatus(c.Request.Context(), jobID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to retrieve status"})
		return
	}
	if status == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "job not found"})
		return
	}

	c.JSON(http.StatusOK, status)
}

// StreamStatus opens a Server-Sent Events (SSE) connection and pushes live status
// updates to the browser as the job progresses through the pipeline.
//
// GET /api/v1/stream/:jobId
func (h *Handler) StreamStatus(c *gin.Context) {
	jobID := c.Param("jobId")

	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Header("X-Accel-Buffering", "no") // Disable Nginx buffering for SSE

	sub := h.Queue.SubscribeStatus(c.Request.Context(), jobID)
	defer sub.Close()

	ch := sub.Channel()
	clientDisconnected := c.Request.Context().Done()

	for {
		select {
		case <-clientDisconnected:
			// Browser closed the connection — clean up.
			return

		case msg, ok := <-ch:
			if !ok {
				return
			}

			var status models.JobStatus
			if err := json.Unmarshal([]byte(msg.Payload), &status); err != nil {
				continue
			}

			// Write the SSE event to the response stream.
			payload, _ := json.Marshal(status)
			fmt.Fprintf(c.Writer, "data: %s\n\n", payload)
			c.Writer.Flush()

			// Stop streaming once the job is in a terminal state.
			if status.Stage == "done" || status.Stage == "error" {
				return
			}
		}
	}
}
