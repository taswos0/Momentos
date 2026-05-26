use serde::{Deserialize, Serialize};

/// Mirrors the job model published by the Go API Gateway.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Job {
    pub id: String,
    pub url: String,
    #[serde(rename = "type")]
    pub job_type: JobType,
    pub created_at: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum JobType {
    Tourism,
    Course,
}

/// Progress update published back to Redis for the Go gateway to broadcast via SSE.
#[derive(Debug, Serialize, Deserialize)]
pub struct JobStatus {
    pub job_id: String,
    pub stage: String,
    pub message: String,
    pub progress: f32,
}

/// A single scraped asset (image, text block, etc.)
#[derive(Debug, Serialize, Deserialize)]
pub struct ScrapedAsset {
    pub asset_type: AssetType,
    pub url: Option<String>,
    pub content: Option<String>,
    pub local_path: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AssetType {
    Image,
    Text,
    Script,
}
