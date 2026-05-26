# Technical Specifications & Requirements

## Project: The Transmedia Alchemist (Memento)

---

## 1. Service Specifications

### A. Frontend — `apps/web-client`

| Property | Value |
|---|---|
| Framework | Next.js 15 (App Router) + React 19 |
| Styling | TailwindCSS v4 + Shadcn UI |
| Animation | Framer Motion (page transitions & micro-interactions) |
| 3D Graphics | Three.js / React Three Fiber (Processing Radar / Black Hole on landing page) |
| Real-time | Server-Sent Events (SSE) for live extraction progress |
| State | Zustand (lightweight global state) |
| Icons | Lucide React |

---

### B. API Gateway — `apps/api-gateway`

| Property | Value |
|---|---|
| Language | Go 1.24+ |
| Framework | Gin Gonic |
| Concurrency | Goroutines — handles thousands of concurrent requests |
| Queue | Redis (`LPUSH` to push jobs, SSE to broadcast progress) |
| Endpoints | `POST /api/v1/extract` · `GET /api/v1/status/:jobId` · `GET /api/v1/stream/:jobId` |
| Auth | API Key header (`X-API-Key`) — middleware validation |
| Config | Environment variables via `.env` |

---

### C. Media & Scraping Engine — `services/media-engine`

| Property | Value |
|---|---|
| Language | Rust (Stable) |
| Async Runtime | Tokio |
| HTTP Client | `reqwest` (async, with cookie jar & custom headers for scraping) |
| HTML Parsing | `scraper` crate (CSS selector-based extraction) |
| Redis Client | `redis` crate (`BRPOP` blocking pull) |
| Audio Processing | `ffmpeg-next` (native FFmpeg bindings — mixing, ducking, encoding to MP3) |
| Image Upscaling | Placeholder: call Python service via internal REST |
| Output | Saves assets to `./output/{jobId}/` directory |

---

### D. AI Synthesis Core — `services/ai-synthesis`

| Property | Value |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI + Uvicorn |
| LLM | OpenAI GPT-4o (text summarization, magazine layout generation) |
| Voice TTS | ElevenLabs API (high-fidelity narrator voice generation) |
| Embeddings | OpenAI `text-embedding-3-small` + CLIP for images |
| Vector DB | Qdrant (self-hosted via Docker, port 6333) |
| Orchestration | LangChain |
| PDF Generation | WeasyPrint or Typst (Print-Ready CMYK output) |
| Config | `python-dotenv` for secrets |

---

## 2. Infrastructure & DevOps

| Service | Image | Port |
|---|---|---|
| Redis | `redis:7-alpine` | 6379 |
| Qdrant | `qdrant/qdrant:latest` | 6333, 6334 |
| API Gateway | Custom Go build | 8080 |
| Media Engine | Custom Rust build | — (worker, no HTTP port) |
| AI Synthesis | Custom Python build | 8000 |
| Web Client | Node.js (Next.js) | 3000 |

- **Networking**: All services communicate via a shared Docker bridge network `alchemist-net`
- **Volumes**: Redis data, Qdrant storage, and job outputs are persisted via named volumes

---

## 3. Content Thematic Templates

The AI Synthesis engine supports two modes, controlled by the `type` field in the job:

| Mode | Design Style | Narrator Tone | Background Music |
|---|---|---|---|
| `tourism` | Warm Terracotta / Sand tones | Enthusiastic & passionate | Regional folk / ambient nature sounds |
| `course` | Slate Grey / Cool Blue | Calm professor | Minimal lo-fi, removed during explanations |

---

## 4. Output Bundle Per Job

Each completed job produces a downloadable bundle containing:

1. `magazine.pdf` — Print-ready interactive PDF (CMYK, 300 DPI)
2. `podcast.mp3` — AI narrated audio with ducked background music
3. `assets/` — Upscaled images and cleaned text scripts
4. `metadata.json` — Full job manifest (sources, word count, processing time)
