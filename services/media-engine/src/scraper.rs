use anyhow::{Context, Result};
use reqwest::Client;
use scraper::{Html, Selector};
use std::path::Path;
use tokio::fs;
use tracing::{info, warn};

use crate::models::ScrapedAsset;

/// Scraper builds a resilient HTTP client that mimics a real browser to avoid
/// basic bot-detection blocks. For advanced protection bypass, extend with
/// rotating User-Agents and proxy support.
pub struct Scraper {
    client: Client,
}

impl Scraper {
    pub fn new() -> Result<Self> {
        let client = Client::builder()
            .user_agent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                 AppleWebKit/537.36 (KHTML, like Gecko) \
                 Chrome/125.0.0.0 Safari/537.36",
            )
            .cookie_store(true)
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .context("Failed to build HTTP client")?;

        Ok(Self { client })
    }

    /// Fetches a URL and extracts all text paragraphs and image URLs from the page.
    pub async fn extract_page(&self, url: &str) -> Result<Vec<ScrapedAsset>> {
        info!("🔍 Scraping: {}", url);

        let html = self
            .client
            .get(url)
            .send()
            .await
            .context("HTTP GET failed")?
            .text()
            .await
            .context("Failed to read response body")?;

        let document = Html::parse_document(&html);
        let mut assets: Vec<ScrapedAsset> = Vec::new();

        // ── Extract Text Paragraphs ──────────────────────────────────
        let p_selector = Selector::parse("p, h1, h2, h3, article").unwrap();
        for element in document.select(&p_selector) {
            let text = element.text().collect::<Vec<_>>().join(" ").trim().to_string();
            if text.len() > 40 {
                assets.push(ScrapedAsset {
                    asset_type: crate::models::AssetType::Text,
                    url: None,
                    content: Some(text),
                    local_path: None,
                });
            }
        }

        // ── Extract Image URLs ───────────────────────────────────────
        let img_selector = Selector::parse("img[src]").unwrap();
        for element in document.select(&img_selector) {
            if let Some(src) = element.value().attr("src") {
                let full_url = if src.starts_with("http") {
                    src.to_string()
                } else {
                    // Resolve relative URLs against the base.
                    format!("{}{}", base_url(url), src)
                };
                assets.push(ScrapedAsset {
                    asset_type: crate::models::AssetType::Image,
                    url: Some(full_url),
                    content: None,
                    local_path: None,
                });
            }
        }

        info!("✅ Extracted {} assets from {}", assets.len(), url);
        Ok(assets)
    }

    /// Downloads an image from `image_url` and saves it to `output_dir/filename`.
    /// Returns the local file path on success.
    pub async fn download_image(
        &self,
        image_url: &str,
        output_dir: &Path,
        filename: &str,
    ) -> Result<String> {
        let bytes = self
            .client
            .get(image_url)
            .send()
            .await
            .context("Image download GET failed")?
            .bytes()
            .await
            .context("Failed to read image bytes")?;

        let dest = output_dir.join(filename);
        fs::write(&dest, &bytes)
            .await
            .context("Failed to write image to disk")?;

        let path_str = dest.to_string_lossy().to_string();
        info!("📸 Saved image: {}", path_str);
        Ok(path_str)
    }
}

/// Extracts the origin (scheme + host) from a URL for resolving relative paths.
fn base_url(url: &str) -> String {
    if let Some(idx) = url.find("://") {
        let rest = &url[idx + 3..];
        if let Some(slash_idx) = rest.find('/') {
            return url[..idx + 3 + slash_idx].to_string();
        }
    }
    url.to_string()
}
