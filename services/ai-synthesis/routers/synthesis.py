"""
Synthesis router — main pipeline endpoint called by the Rust Media Engine
after scraping is complete.
"""
import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from config import settings
from services import llm, tts, vectors, layout

router = APIRouter(prefix="", tags=["synthesis"])


class SynthesisRequest(BaseModel):
    job_id: str
    job_type: str          # "tourism" | "course"
    text_blocks: list[str]
    image_paths: list[str]
    output_dir: str


@router.post("/synthesize", status_code=202)
async def synthesize(req: SynthesisRequest, background_tasks: BackgroundTasks):
    """
    Kicks off the full AI synthesis pipeline in the background.
    Returns immediately — progress is tracked via the Redis status channel.
    """
    background_tasks.add_task(_run_pipeline, req)
    return {"status": "synthesis_started", "job_id": req.job_id}


async def _run_pipeline(req: SynthesisRequest) -> None:
    """
    Full synthesis pipeline:
      1. Embed text blocks into Qdrant
      2. GPT-4o → structured magazine layout
      3. Semantic image ↔ paragraph matching via Cosine Similarity
      4. ElevenLabs TTS → narrator voice MP3
      5. WeasyPrint → print-ready PDF
      6. Save metadata.json
    """
    job_dir = Path(req.output_dir)
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ── Step 1: Embed text into Qdrant ───────────────────────────
        await vectors.embed_texts(req.text_blocks, req.job_id)

        # ── Step 2: Generate structured layout with GPT-4o ───────────
        magazine_layout = await llm.synthesize_content(req.text_blocks, req.job_type)

        # ── Step 3: Semantic image → section matching ─────────────────
        image_map: dict[str, str] = {}
        for section in magazine_layout.get("sections", []):
            heading = section.get("heading", "")
            body = section.get("body", "")
            best_image = await vectors.find_best_image_for_paragraph(
                f"{heading} {body}", req.job_id
            )
            if best_image:
                image_map[heading] = best_image

        # ── Step 4: Generate narrator voice (ElevenLabs) ─────────────
        podcast_script = tts.build_podcast_script(magazine_layout, req.job_type)
        voice_path = job_dir / "voice_raw.mp3"
        await tts.generate_voice(podcast_script, req.job_type, voice_path)

        # ── Step 5: Generate the PDF magazine ─────────────────────────
        pdf_path = job_dir / "magazine.pdf"
        layout.generate_pdf(magazine_layout, req.job_type, image_map, pdf_path)

        # ── Step 6: Save metadata ─────────────────────────────────────
        meta = {
            "job_id": req.job_id,
            "job_type": req.job_type,
            "source_url": "",
            "section_count": len(magazine_layout.get("sections", [])),
            "image_count": len(req.image_paths),
            "files": {
                "magazine": str(pdf_path),
                "voice_raw": str(voice_path),
            },
        }
        (job_dir / "metadata.json").write_text(json.dumps(meta, indent=2))

    except Exception as e:
        # Log and let the Rust engine handle the error status update.
        print(f"❌ Synthesis pipeline failed for job {req.job_id}: {e}")
        raise
