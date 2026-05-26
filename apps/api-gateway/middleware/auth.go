package middleware

import (
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
)

// APIKeyAuth enforces a shared secret key on all API routes.
// The client must send the key in the X-API-Key header.
func APIKeyAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		expectedKey := os.Getenv("API_KEY")
		if expectedKey == "" {
			// If no key is configured, skip auth (dev mode only).
			c.Next()
			return
		}

		clientKey := c.GetHeader("X-API-Key")
		if clientKey == "" || clientKey != expectedKey {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
				"error": "missing or invalid API key",
			})
			return
		}

		c.Next()
	}
}
