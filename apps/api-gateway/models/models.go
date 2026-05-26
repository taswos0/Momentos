package models

// JobType defines the content template mode.
type JobType string

const (
	JobTypeTourism JobType = "tourism"
	JobTypeCourse  JobType = "course"
)

// Job represents a single extraction and synthesis task.
type Job struct {
	ID        string  `json:"id"`
	URL       string  `json:"url"`
	Type      JobType `json:"type"`
	CreatedAt int64   `json:"created_at"`
}

// JobStatus holds the current state of a job as it progresses through the pipeline.
type JobStatus struct {
	JobID   string  `json:"job_id"`
	Stage   string  `json:"stage"`   // "queued" | "scraping" | "synthesizing" | "done" | "error"
	Message string  `json:"message"` // Human-readable progress description
	Progress float32 `json:"progress"` // 0.0 → 1.0
}

// ExtractionRequest is the JSON body accepted by POST /api/v1/extract.
type ExtractionRequest struct {
	URL  string  `json:"url"  binding:"required,url"`
	Type JobType `json:"type" binding:"required,oneof=tourism course"`
}
