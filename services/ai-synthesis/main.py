"""
FastAPI entry point for the AI Synthesis service.
"""
from fastapi import FastAPI
from routers import synthesis

app = FastAPI(
    title="Transmedia Alchemist — AI Synthesis Core",
    description="LLM orchestration, vector embeddings, voice generation, and PDF layout engine.",
    version="0.1.0",
)

app.include_router(synthesis.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-synthesis"}
