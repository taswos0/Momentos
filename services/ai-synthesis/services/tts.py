"""
TTS Service — ElevenLabs voice generation for the AI podcast layer.
Produces a high-fidelity MP3 narrator track that the Rust engine will
later mix with background music using FFmpeg audio ducking.
"""
import httpx
from pathlib import Path
from config import settings

# ElevenLabs voice IDs — choose based on content type.
# These are stable default voices; swap for cloned voices as needed.
VOICE_IDS = {
    "tourism": "EXAVITQu4vr4xnSDxMaL",  # Passionate, enthusiastic narrator
    "course":  "pNInz6obpgDQGcFmaJgB",  # Calm, authoritative professor tone
}

ELEVENLABS_API = "https://api.elevenlabs.io/v1"


async def generate_voice(text: str, job_type: str, output_path: Path) -> Path:
    """
    Calls ElevenLabs TTS API and saves the resulting MP3 to output_path.
    Returns the path to the saved file.
    """
    voice_id = VOICE_IDS.get(job_type, VOICE_IDS["tourism"])

    # Build a podcast-style script from the structured content.
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{ELEVENLABS_API}/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": settings.elevenlabs_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.85,
                    "style": 0.3,
                    "use_speaker_boost": True,
                },
            },
        )
        response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    return output_path


def build_podcast_script(layout: dict, job_type: str) -> str:
    """
    Converts the structured magazine layout into a natural-sounding podcast script.
    """
    lines = []

    if job_type == "tourism":
        lines.append(f"Welcome. Today, we journey to: {layout.get('title', 'an incredible destination')}.")
        lines.append(layout.get("subtitle", ""))
        for section in layout.get("sections", []):
            lines.append(f"\n{section.get('heading', '')}.")
            lines.append(section.get("body", ""))
    else:
        lines.append(f"In this chapter: {layout.get('title', 'our lesson today')}.")
        objectives = layout.get("learning_objectives", [])
        if objectives:
            lines.append("By the end, you will understand: " + "; ".join(objectives) + ".")
        for section in layout.get("sections", []):
            lines.append(f"\n{section.get('heading', '')}.")
            lines.append(section.get("body", ""))
            if kp := section.get("key_point"):
                lines.append(f"Key takeaway: {kp}")

    return " ".join(filter(None, lines))
