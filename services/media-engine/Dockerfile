# ── Build stage ─────────────────────────────────────────────────────
FROM rust:1.88-slim AS builder

# FFmpeg dev headers needed for the ffmpeg-next crate
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY Cargo.toml Cargo.lock* ./

# Cache dependencies by building a dummy main first
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -f target/release/deps/media_engine*

COPY src ./src
RUN cargo build --release

# ── Runtime image ────────────────────────────────────────────────────
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libssl3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/target/release/media-engine /app/media-engine

RUN mkdir -p /app/output

CMD ["/app/media-engine"]
