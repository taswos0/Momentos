package main

import (
	"log"
	"os"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/transmedia-alchemist/api-gateway/handlers"
	"github.com/transmedia-alchemist/api-gateway/middleware"
	"github.com/transmedia-alchemist/api-gateway/queue"
)

func main() {
	// ── Configuration ────────────────────────────────────────────────
	redisAddr := getEnv("REDIS_ADDR", "localhost:6379")
	port := getEnv("GATEWAY_PORT", "8080")

	// ── Redis Queue Client ───────────────────────────────────────────
	q, err := queue.New(redisAddr)
	if err != nil {
		log.Fatalf("❌ Failed to connect to Redis at %s: %v", redisAddr, err)
	}
	defer q.Close()
	log.Printf("✅ Redis connected at %s", redisAddr)

	// ── HTTP Server ──────────────────────────────────────────────────
	r := gin.New()
	r.Use(gin.Logger())
	r.Use(gin.Recovery())

	// CORS: allow the Next.js frontend origin.
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:3000"},
		AllowMethods:     []string{"GET", "POST", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "X-API-Key"},
		AllowCredentials: false,
	}))

	// ── Routes ───────────────────────────────────────────────────────
	h := handlers.New(q)

	api := r.Group("/api/v1")
	api.Use(middleware.APIKeyAuth())
	{
		api.POST("/extract", h.Extract)
		api.GET("/status/:jobId", h.GetStatus)
		api.GET("/stream/:jobId", h.StreamStatus)
	}

	// Health check (no auth required)
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok", "service": "api-gateway"})
	})

	log.Printf("🚀 API Gateway running on :%s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("❌ Server failed: %v", err)
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
