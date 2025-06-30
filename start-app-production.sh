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
echo "🤖 Checking external Ollama server at $OLLAMA_HOST..."
if ! wait_for_service "Ollama" "$OLLAMA_HOST/api/version" 30; then
    echo "❌ External Ollama server not available at $OLLAMA_HOST"
    echo "⚠️  Falling back to localhost Ollama..."
    export OLLAMA_HOST="http://localhost:11434"
fi

echo "✅ Ollama server is ready at $OLLAMA_HOST"
echo "📋 Available models:"
curl -s "$OLLAMA_HOST/api/tags" | python3 -m json.tool 2>/dev/null || echo "Could not list models"

# Verify Ollama is working with a test generation
echo "🧪 Testing Ollama with phi3:mini..."
TEST_RESULT=$(curl -s -X POST "$OLLAMA_HOST/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "phi3:mini", "prompt": "test", "stream": false}' \
  --max-time 15 | grep -o '"response":"[^"]*"' | head -1)

if [ -n "$TEST_RESULT" ]; then
    echo "✅ Ollama test successful: $TEST_RESULT"
else
    echo "❌ Ollama test failed"
fi

# Start Redis server (required for chat system)
echo "🗄️ Starting Redis server..."

# Install Redis if not available
if ! command -v redis-server > /dev/null 2>&1; then
    echo "📦 Installing Redis server..."
    apt-get update -qq && apt-get install -y redis-server redis-tools
fi

# Optimize memory settings for Redis (suppress kernel warnings)
echo "🔧 Optimizing system memory settings for Redis..."
sysctl vm.overcommit_memory=1 2>/dev/null || echo "⚠️ Could not set vm.overcommit_memory (non-critical)"

# Kill any existing Redis processes
pkill redis-server 2>/dev/null || true
sleep 2

# Create Redis configuration for RunPod
cat > /tmp/redis.conf << 'EOF'
bind 127.0.0.1
port 6379
timeout 0
save ""
appendonly no
protected-mode no
daemonize no
EOF

# Start Redis server with custom config
echo "🚀 Starting Redis with custom configuration..."
nohup redis-server /tmp/redis.conf > /tmp/redis.log 2>&1 &
REDIS_PID=$!
echo "Redis started with PID: $REDIS_PID"

# Wait for Redis to be ready with better validation
echo "⏳ Waiting for Redis to be ready..."
REDIS_READY=false
for i in {1..15}; do
    if redis-cli -h 127.0.0.1 -p 6379 ping >/dev/null 2>&1; then
        PING_RESULT=$(redis-cli -h 127.0.0.1 -p 6379 ping 2>/dev/null)
        if [ "$PING_RESULT" = "PONG" ]; then
            echo "✅ Redis is ready and responding"
            REDIS_READY=true
            break
        fi
    fi
    echo "Waiting for Redis... (attempt $i/15)"
    sleep 2
done

# Comprehensive Redis testing
if [ "$REDIS_READY" = "true" ]; then
    echo "🧪 Testing Redis functionality..."
    
    # Test basic operations
    if redis-cli -h 127.0.0.1 -p 6379 set test_key "test_value" >/dev/null 2>&1; then
        TEST_VALUE=$(redis-cli -h 127.0.0.1 -p 6379 get test_key 2>/dev/null)
        if [ "$TEST_VALUE" = "test_value" ]; then
            echo "✅ Redis read/write test successful"
            redis-cli -h 127.0.0.1 -p 6379 del test_key >/dev/null 2>&1
        else
            echo "❌ Redis read/write test failed"
        fi
    else
        echo "❌ Redis write operation failed"
    fi
    
    # Test connection info
    echo "📊 Redis connection info:"
    redis-cli -h 127.0.0.1 -p 6379 info server | grep -E "redis_version|uptime_in_seconds" || true
else
    echo "❌ Redis failed to start properly"
    echo "📋 Redis startup log:"
    tail -20 /tmp/redis.log 2>/dev/null || echo "No Redis log available"
    echo "🔍 Process check:"
    ps aux | grep redis || echo "No Redis processes found"
fi

# Start FastAPI application
echo "🚀 Starting FastAPI application..."
cd /app

# Create directories for logs and data
mkdir -p logs data models

# Start the application
echo "🎯 Starting AI Search System API server..."
echo "🔧 Final environment check:"
echo "   OLLAMA_HOST: $OLLAMA_HOST"
echo "   REDIS_URL: $REDIS_URL"
echo "   API_HOST: $API_HOST:$API_PORT"

exec uvicorn app.main:app \
    --host "$API_HOST" \
    --port "$API_PORT" \
    --workers 1 \
    --access-log \
    --log-level info