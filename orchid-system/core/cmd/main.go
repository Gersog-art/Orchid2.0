package main

import (
    "log"
    "net/http"
    "os"
    "orchid-core/internal/api"
    "orchid-core/internal/config"
    "orchid-core/internal/database"
    "orchid-core/internal/rabbitmq"
    "orchid-core/internal/redis"
    
    "github.com/gin-gonic/gin"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
    // Load configuration
    cfg, err := config.Load()
    if err != nil {
        log.Fatal("Failed to load config:", err)
    }
    
    // Initialize database
    db, err := database.Init(cfg)
    if err != nil {
        log.Fatal("Failed to connect to database:", err)
    }
    
    // Initialize Redis
    redisClient := redis.Init(cfg)
    
    // Initialize RabbitMQ
    mqConn, err := rabbitmq.Init(cfg)
    if err != nil {
        log.Fatal("Failed to connect to RabbitMQ:", err)
    }
    defer mqConn.Close()
    
    // Create message consumer
    consumer := rabbitmq.NewConsumer(mqConn, db, redisClient)
    go consumer.Start()
    
    // Create message producer
    producer := rabbitmq.NewProducer(mqConn)
    
    // Setup HTTP server
    router := gin.Default()
    
    // Setup routes
    api.SetupRoutes(router, db, redisClient, producer)
    
    // Metrics endpoint
    router.GET("/metrics", gin.WrapH(promhttp.Handler()))
    
    // Health check
    router.GET("/health", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{
            "status": "healthy",
            "services": gin.H{
                "database": db != nil,
                "redis":    redisClient != nil,
                "rabbitmq": mqConn != nil,
            },
        })
    })
    
    // Start server
    log.Printf("Starting server on :%s", cfg.ServerPort)
    if err := router.Run(":" + cfg.ServerPort); err != nil {
        log.Fatal("Failed to start server:", err)
    }
}
