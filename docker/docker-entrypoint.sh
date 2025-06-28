#!/bin/bash
set -e

# Agentical Docker Entrypoint Script
# Handles initialization, health checks, and graceful startup

echo "🚀 Starting Agentical Multi-Agent Framework"
echo "Environment: ${ENV:-development}"
echo "Port: ${PORT:-8000}"

# Function to log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Health check function
health_check() {
    log "Performing health check..."
    
    # Check if required environment variables are set
    required_vars=(
        "SURREALDB_URL"
        "SURREALDB_NAMESPACE"
        "SURREALDB_DATABASE"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log "ERROR: Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log "✅ Environment variables validated"
}

# Database connectivity check
check_database() {
    log "Checking database connectivity..."
    
    # Simple connectivity test (could be enhanced with actual DB ping)
    if [ -n "$SURREALDB_URL" ]; then
        log "✅ Database configuration found"
    else
        log "⚠️  Database configuration missing"
    fi
}

# Initialize application
initialize_app() {
    log "Initializing Agentical application..."
    
    # Create necessary directories
    mkdir -p /app/logs /app/data /app/cache
    
    # Set up logging directory permissions
    if [ -w /app/logs ]; then
        log "✅ Logging directory ready"
    else
        log "⚠️  Logging directory not writable"
    fi
    
    # Initialize cache directory
    if [ -w /app/cache ]; then
        log "✅ Cache directory ready"
    else
        log "⚠️  Cache directory not writable"
    fi
}

# Graceful shutdown handler
shutdown_handler() {
    log "Received shutdown signal, initiating graceful shutdown..."
    
    # Kill the main process
    if [ -n "$MAIN_PID" ]; then
        kill -TERM "$MAIN_PID" 2>/dev/null || true
        wait "$MAIN_PID" 2>/dev/null || true
    fi
    
    log "✅ Graceful shutdown completed"
    exit 0
}

# Set up signal handlers
trap shutdown_handler SIGTERM SIGINT

# Main execution
main() {
    log "Starting Agentical initialization sequence..."
    
    # Run initialization steps
    health_check
    check_database
    initialize_app
    
    log "✅ Initialization completed successfully"
    log "Starting main application: $@"
    
    # Execute the main command
    exec "$@" &
    MAIN_PID=$!
    
    # Wait for the main process
    wait $MAIN_PID
}

# Run main function with all arguments
main "$@"