#!/bin/bash
# Production startup script for AI Search System with Ollama
set -e

echo "🚀 Starting AI Search System - Production Mode"
echo "=============================================="

# Set environment variables
export PYTHONPATH="/app"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
export ENVIRONMENT="${ENVIRONMENT:-production}"
export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-8000}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

echo "Environment configured:"
echo "  - Redis: $REDIS_URL"
echo "  - Ollama: $OLLAMA_HOST"
echo "  - Environment: $ENVIRONMENT"
echo "  - API: $API_HOST:$API_PORT"
echo "  - CUDA: $CUDA_VISIBLE_DEVICES"

# Function to check if a service is ready
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=0
    
    echo "⏳ Waiting for $service_name to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 2
    done
    
    echo "❌ $service_name failed to start within timeout"
    return 1
}

# Check if external Ollama is available
echo "🤖 Checking external Ollama server..."
if ! wait_for_service "Ollama" "$OLLAMA_HOST/api/version" 30; then
    echo "❌ External Ollama server not available at $OLLAMA_HOST"
    exit 1
fi

echo "✅ External Ollama server is ready"
echo "📋 Available models:"
curl -s "$OLLAMA_HOST/api/tags" | python3 -m json.tool 2>/dev/null || echo "Could not list models"

# Optional: Start Redis if not running (for local development)
if ! curl -s "$REDIS_URL" > /dev/null 2>&1; then
    echo "⚠️ Redis not detected at $REDIS_URL"
    echo "   Starting Redis if available..."
    if command -v redis-server > /dev/null 2>&1; then
        nohup redis-server > /tmp/redis.log 2>&1 &
        sleep 3
    fi
fi

# Start FastAPI application
echo "🚀 Starting FastAPI application..."
cd /app

# Create directories for logs and data
mkdir -p logs data models

# Start the application
echo "🎯 Starting AI Search System API server..."
exec uvicorn app.main:app \
    --host "$API_HOST" \
    --port "$API_PORT" \
    --workers 1 \
    --access-log \
    --log-level info