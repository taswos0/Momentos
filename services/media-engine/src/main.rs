mod audio;
mod models;
mod scraper;

use anyhow::Result;
use redis::AsyncCommands;
use serde_json;
use std::path::PathBuf;
use tokio::fs;
use tracing::{error, info};
use tracing_subscriber::{fmt, EnvFilter};
use uuid::Uuid;

use audio::AudioMixer;
use models::{Job, JobStatus, JobType};
use scraper::Scraper;

/// Default AI Synthesis URL used when the env var is not set.
const DEFAULT_AI_SYNTHESIS_URL: &str = "http://localhost:8000";

#[tokio::main]
async fn main() -> Result<()> {
    // ── Logging ─────────────────────────────────────────────────────
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("info".parse()?))
        .init();

    // ── Config ───────────────────────────────────────────────────────
    dotenvy::dotenv().ok();
    let redis_url = std::env::var("REDIS_URL").unwrap_or_else(|_| "redis://127.0.0.1".into());
    let output_root = std::env::var("OUTPUT_DIR").unwrap_or_else(|_| "./output".into());

    // ── Redis Connection ─────────────────────────────────────────────
    let client = redis::Client::open(redis_url.as_str())?;
    let mut con = client.get_multiplexed_async_connection().await?;
    info!("🦀 Rust Media Engine connected to Redis at {}", redis_url);
    info!("🔊 Listening on queue:scraping — waiting for jobs...");

    // ── Main Worker Loop ─────────────────────────────────────────────
    // BRPOP blocks with zero CPU usage until a job arrives.
    // We never spin — only wake on real work.
    loop {
        let result: Result<Option<(String, String)>, redis::RedisError> =
            con.brpop("queue:scraping", 0.0).await;

        match result {
            Ok(Some((_, payload))) => {
                let job: Job = match serde_json::from_str(&payload) {
                    Ok(j) => j,
                    Err(e) => {
                        error!("❌ Malformed job payload: {} — payload: {}", e, payload);
                        continue;
                    }
                };

                info!("🚀 Received job: id={} url={}", job.id, job.url);

                // Spawn an independent async task per job so the main loop
                // is never blocked — multiple jobs process concurrently.
                let output_root_clone = output_root.clone();
                tokio::spawn(async move {
                    if let Err(e) = process_job(job, PathBuf::from(output_root_clone)).await {
                        error!("❌ Job processing failed: {}", e);
                    }
                });
            }
            Ok(None) => continue,
            Err(e) => error!("❌ Redis error: {}", e),
        }
    }
}

/// Orchestrates the full media pipeline for a single job.
async fn process_job(job: Job, output_root: PathBuf) -> Result<()> {
    let job_dir = output_root.join(&job.id);
    let images_dir = job_dir.join("images");
    fs::create_dir_all(&images_dir).await?;

    publish_status(&job.id, "scraping", "Extracting content from source URL...", 0.1).await;

    // ── Step 1: Scrape ───────────────────────────────────────────────
    let s = Scraper::new()?;
    let assets = s.extract_page(&job.url).await?;

    // Download images found during scraping.
    let mut downloaded_images: Vec<String> = Vec::new();
    for (i, asset) in assets.iter().enumerate() {
        if let (models::AssetType::Image, Some(img_url)) = (&asset.asset_type, &asset.url) {
            let filename = format!("{}.jpg", Uuid::new_v4());
            match s.download_image(img_url, &images_dir, &filename).await {
                Ok(path) => downloaded_images.push(path),
                Err(e) => error!("⚠️ Skipping image {}: {}", i, e),
            }
        }
    }

    publish_status(&job.id, "scraping", &format!("Scraped {} assets", assets.len()), 0.3).await;

    // ── Step 2: Forward to AI Synthesis ─────────────────────────────
    publish_status(&job.id, "synthesizing", "Sending assets to AI for synthesis...", 0.5).await;

    let text_blocks: Vec<String> = assets
        .iter()
        .filter_map(|a| a.content.clone())
        .collect();

    let synthesis_payload = serde_json::json!({
        "job_id": job.id,
        "job_type": job.job_type,
        "text_blocks": text_blocks,
        "image_paths": downloaded_images,
        "output_dir": job_dir.to_str().unwrap_or(""),
    });

    let ai_url =
        std::env::var("AI_SYNTHESIS_URL").unwrap_or_else(|_| DEFAULT_AI_SYNTHESIS_URL.into());
    let client = reqwest::Client::new();
    client
        .post(format!("{}/synthesize", ai_url))
        .json(&synthesis_payload)
        .send()
        .await?;

    publish_status(&job.id, "done", "Your content bundle is ready for download!", 1.0).await;
    info!("✨ Job {} complete. Output: {:?}", job.id, job_dir);
    Ok(())
}

/// Publishes a job status update to the Redis channel that the Go gateway broadcasts via SSE.
async fn publish_status(job_id: &str, stage: &str, message: &str, progress: f32) {
    let status = JobStatus {
        job_id: job_id.to_string(),
        stage: stage.to_string(),
        message: message.to_string(),
        progress,
    };

    let redis_url = std::env::var("REDIS_URL").unwrap_or_else(|_| "redis://127.0.0.1".into());
    if let Ok(client) = redis::Client::open(redis_url.as_str()) {
        if let Ok(mut con) = client.get_multiplexed_async_connection().await {
            let channel = format!("channel:status:{}", job_id);
            let payload = serde_json::to_string(&status).unwrap_or_default();
            let _: Result<(), _> = con.publish(channel, payload).await;

            // Also persist the latest status for polling via GET /api/v1/status/:jobId
            let key = format!("status:{}", job_id);
            let _: Result<(), _> = con.set_ex(key, serde_json::to_string(&status).unwrap_or_default(), 3600).await;
        }
    }
}
