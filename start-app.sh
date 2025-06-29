#!/bin/bash
# Container startup script for production deployment
set -e

echo "Starting AI Search System - Production Container"
echo "================================================="

# Create necessary directories with proper permissions
mkdir -p /workspace/logs /workspace/data /workspace/models /root/.ollama/models
chmod 755 /workspace/logs /workspace/data /workspace/models /root/.ollama /root/.ollama/models

# Set environment variables
export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
export ENVIRONMENT="${ENVIRONMENT:-production}"
export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-8000}"
export PYTHONPATH="/"
export OLLAMA_MODELS="/root/.ollama/models"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

echo "Environment configured:"
echo "  - Redis: $REDIS_URL"
echo "  - Ollama: $OLLAMA_HOST"
echo "  - Environment: $ENVIRONMENT"
echo "  - API: $API_HOST:$API_PORT"
echo "  - CUDA Device: $CUDA_VISIBLE_DEVICES"

# Pre-start service checks
echo "Pre-start checks..."

# Ensure Ollama directories exist
echo "Setting up Ollama directories..."
mkdir -p /root/.ollama/models
chown -R root:root /root/.ollama

# Initialize models in background if not already done
if [ ! -f "/workspace/models/.initialized" ]; then
    echo "Initializing models in background..."
    /app/init-models.sh &
fi

# Start supervisor with the provided command
echo "Starting services with supervisor..."
echo "Services will start in order: Redis -> Ollama -> FastAPI App -> Model Init"
exec "$@"
