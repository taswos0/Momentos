use anyhow::{Context, Result};
use std::path::Path;
use std::process::Command;
use tracing::info;

/// AudioMixer handles all FFmpeg-based audio operations.
/// It uses the system FFmpeg binary, which must be available in the container.
///
/// The ducking pipeline:
///   1. Voice track (TTS MP3 from AI Synthesis)
///   2. Thematic background music (selected by content type)
///   3. FFmpeg `sidechaincompress` filter: auto-lowers music by ~12dB when voice is present
///   4. Output: single broadcast-ready MP3
pub struct AudioMixer;

impl AudioMixer {
    /// Merges a voice track with background music using FFmpeg's sidechain compression
    /// to achieve professional audio ducking.
    ///
    /// # Arguments
    /// * `voice_path`  — path to the TTS-generated narrator MP3
    /// * `music_path`  — path to the background music file
    /// * `output_path` — destination path for the final mixed MP3
    pub fn mix_with_ducking(
        voice_path: &Path,
        music_path: &Path,
        output_path: &Path,
    ) -> Result<()> {
        info!(
            "🎵 Mixing audio: voice={:?} music={:?} → output={:?}",
            voice_path, music_path, output_path
        );

        // The FFmpeg filter graph:
        //   [1:a]    → background music stream
        //   asplit   → duplicate it: one for listening, one as the sidechain trigger
        //   [0:a]    → the voice/narrator stream (also the sidechain input)
        //   sidechaincompress: when voice (sc) is loud, music (in) is compressed down
        //   amix     → blend compressed music + original voice into one output
        let filter_complex = "\
            [1:a]asplit=2[music_in][music_sc];\
            [0:a][music_sc]sidechaincompress=\
                threshold=0.02:\
                ratio=20:\
                attack=200:\
                release=1000[compressed_music];\
            [0:a][compressed_music]amix=inputs=2:duration=longest[out]";

        let status = Command::new("ffmpeg")
            .args([
                "-y",                                    // overwrite output without asking
                "-i", voice_path.to_str().unwrap(),      // input 0: narrator voice
                "-i", music_path.to_str().unwrap(),      // input 1: background music
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-codec:a", "libmp3lame",
                "-q:a", "2",                             // high quality VBR (~190 kbps)
                output_path.to_str().unwrap(),
            ])
            .status()
            .context("Failed to spawn FFmpeg process — ensure ffmpeg is installed")?;

        if !status.success() {
            anyhow::bail!("FFmpeg exited with non-zero status: {}", status);
        }

        info!("✅ Audio mixing complete: {:?}", output_path);
        Ok(())
    }

    /// Converts text to a temporary placeholder audio file.
    /// In production, the real TTS file comes from the AI Synthesis service (ElevenLabs).
    /// This generates a silent MP3 of the given duration as a dev fallback.
    pub fn generate_silence(duration_secs: u32, output_path: &Path) -> Result<()> {
        let status = Command::new("ffmpeg")
            .args([
                "-y",
                "-f", "lavfi",
                "-i", &format!("anullsrc=r=44100:cl=stereo:d={}", duration_secs),
                "-codec:a", "libmp3lame",
                "-q:a", "9",
                output_path.to_str().unwrap(),
            ])
            .status()
            .context("Failed to generate silence track")?;

        if !status.success() {
            anyhow::bail!("FFmpeg silence generation failed");
        }

        Ok(())
    }
}
