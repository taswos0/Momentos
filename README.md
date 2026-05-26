# The Transmedia Alchemist (Memento) 🧙‍♂️

> An elite, polyglot microservices platform that reverse-engineers raw internet content
> (YouTube, Instagram, Blogs) and synthesizes it into a **premium interactive digital
> magazine** (Print-Ready PDF) and an **AI-driven audio podcast** with automatic
> audio ducking — built to impress any senior software engineer.

---

## Architecture Overview

This platform is built on a **Highly Scalable, Event-Driven, Polyglot Microservices
Architecture** — each language is chosen for what it does best, not for convenience:

```
┌─────────────────────────────────────────────────────────────────┐
│                   Next.js 15  (Cinematic 3D UI)                 │
│          Three.js Black Hole · SSE Real-time Radar              │
└───────────────────────────┬─────────────────────────────────────┘
                            │  HTTP / SSE
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Go / Gin  — API Gateway & Orchestrator             │
│        < 5ms job acceptance · Goroutines · Redis LPUSH          │
└───────────────────────────┬─────────────────────────────────────┘
                            │  Redis Pub/Sub
              ┌─────────────┴──────────────┐
              ▼                            ▼
┌─────────────────────┐      ┌──────────────────────────────┐
│  Rust + Tokio       │      │  Python + FastAPI            │
│  Media Engine       │      │  AI Synthesis Core           │
│                     │      │                              │
│  · Web Scraping     │      │  · GPT-4o Summarization      │
│  · Image Download   │◄────►│  · Vector Embeddings (CLIP)  │
│  · FFmpeg Audio Mix │      │  · Qdrant Semantic Search    │
│  · Audio Ducking    │      │  · ElevenLabs TTS Voice      │
│  · PDF Assembly     │      │  · Magazine Layout Engine    │
└─────────────────────┘      └──────────────────────────────┘
              │                            │
              └─────────────┬──────────────┘
                            ▼
                ┌─────────────────────┐
                │  Redis  +  Qdrant   │
                │  Queue  +  Vectors  │
                └─────────────────────┘
```

---

## Repository Structure

```
transmedia-alchemist/
├── apps/
│   ├── web-client/               # Next.js 15 App Router — Cinematic Frontend
│   │   ├── src/app/              # App Router pages & layouts
│   │   ├── src/components/       # UI components (Radar, Magazine Preview, etc.)
│   │   └── src/lib/              # SSE client, Zustand stores, API helpers
│   │
│   └── api-gateway/              # Go / Gin — Task Orchestrator
│       ├── main.go               # Entry point: routes & server setup
│       ├── handlers/             # HTTP handler functions
│       ├── middleware/           # Auth (API Key), CORS, rate limiting
│       ├── queue/                # Redis client & job publishing
│       └── go.mod
│
├── services/
│   ├── media-engine/             # Rust + Tokio — Scraping & Audio Engine
│   │   ├── src/
│   │   │   ├── main.rs           # Entry: Redis BRPOP listener
│   │   │   ├── scraper.rs        # Async web scraping module
│   │   │   ├── audio.rs          # FFmpeg audio mixing & ducking
│   │   │   └── models.rs         # Shared data structs (Job, Asset, etc.)
│   │   └── Cargo.toml
│   │
│   └── ai-synthesis/             # Python + FastAPI — AI Core
│       ├── main.py               # FastAPI app entry point
│       ├── routers/
│       │   ├── synthesis.py      # Magazine & podcast generation endpoints
│       │   └── vectors.py        # Embedding & Qdrant operations
│       ├── services/
│       │   ├── llm.py            # GPT-4o calls & prompt management
│       │   ├── tts.py            # ElevenLabs voice generation
│       │   └── layout.py         # PDF layout construction
│       └── requirements.txt
│
├── shared/
│   └── docker-compose.yml        # One command to rule them all
│
├── system-prompt.md              # AI Agent context & constraints
├── requirements.md               # Full technical specifications
└── README.md
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js 15 + Three.js | Server components + WebGL 3D radar animation |
| Gateway | Go + Gin | Sub-millisecond routing, goroutine concurrency |
| Scraping & Audio | Rust + Tokio | Zero-cost async, no GC pauses, raw FFmpeg control |
| AI & Vectors | Python + FastAPI | Best-in-class AI/ML ecosystem |
| Queue | Redis 7 | Ultra-fast pub/sub, zero-persistence job queue |
| Vector DB | Qdrant | High-performance semantic vector search |

---

## Technical Highlights

### Zero-Block Queueing
Requests are accepted by the Go gateway in **< 5ms** and immediately enqueued in Redis.
The gateway never waits for processing — it returns a `jobId` instantly.

### Cross-Media Semantic Mapping
Text paragraphs and downloaded images are both converted to vector embeddings and stored
in Qdrant. **Cosine Similarity** search automatically identifies which image belongs with
which paragraph — no human curation needed.

### Automated Audio Ducking
The Rust engine calls FFmpeg via native bindings to:
1. Generate the narrator voice track (ElevenLabs TTS)
2. Select thematic background music based on content type
3. Auto-duck background music by **-12dB** when the narrator speaks
4. Output a single, broadcast-ready **MP3** file

### Thematic Intelligence
Two content modes — `tourism` and `course` — automatically adjust typography, color
palette, narrator tone, and background music without any code changes.

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/your-username/transmedia-alchemist
cd transmedia-alchemist

# 2. Copy environment variables
cp shared/.env.example shared/.env
# → Fill in OPENAI_API_KEY and ELEVENLABS_API_KEY

# 3. Launch all services (Redis, Qdrant, all microservices)
cd shared
docker compose up --build

# 4. Open the app
open http://localhost:3000
```

---

## Engineering Pitch

> *"This platform is an Event-Driven, Polyglot Microservices Architecture. The Next.js 15
> frontend communicates via SSE with a Go API Gateway built for High Concurrency.
> Heavy data processing, web scraping, and audio layering run inside a Rust engine for
> maximum speed and zero CPU bottlenecks. Semantic image-text alignment is performed via
> Vector Search in Qdrant. All tasks flow through a Redis Queue to ensure the system
> handles thousands of concurrent jobs without degradation."*
