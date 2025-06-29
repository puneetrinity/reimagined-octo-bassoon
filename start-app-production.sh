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

# Start Ollama in background
echo "🤖 Starting Ollama server..."
nohup ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!
echo "Ollama started with PID: $OLLAMA_PID"

# Wait for Ollama to be ready
if ! wait_for_service "Ollama" "http://localhost:11434/api/version" 60; then
    echo "❌ Failed to start Ollama"
    exit 1
fi

# Pull essential models
echo "📥 Ensuring essential models are available..."
MODELS_TO_PULL=("phi3:mini" "tinyllama:latest")

for model in "${MODELS_TO_PULL[@]}"; do
    if ! ollama list | grep -q "$model"; then
        echo "📥 Pulling $model..."
        ollama pull "$model" || echo "⚠️ Failed to pull $model (will retry later)"
    else
        echo "✅ $model already available"
    fi
done

echo "✅ Model initialization complete"
ollama list

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