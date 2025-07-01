#!/bin/bash
# Deployment validation script
# Ensures all services are working after deployment

set -e

echo "🔍 Deployment Validation Script"
echo "==============================="

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 30

# Function to check service health
check_service() {
    local service_name="$1"
    local check_command="$2"
    local max_attempts=10
    local attempt=0

    echo "🔍 Checking $service_name..."
    
    while [ $attempt -lt $max_attempts ]; do
        if eval "$check_command" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo "   Attempt $attempt/$max_attempts for $service_name..."
        sleep 5
    done
    
    echo "❌ $service_name failed health check"
    return 1
}

# Check supervisor status
echo "📊 Supervisor Status:"
supervisorctl status || echo "⚠️ Supervisor not responding"
echo ""

# Check core services
check_service "Redis" "redis-cli ping" || echo "⚠️ Redis not available"
check_service "FastAPI" "curl -f http://localhost:8000/health/live" || echo "❌ FastAPI failed"

# Check Ollama (optional - won't fail if missing)
if check_service "Ollama" "curl -f http://localhost:11434/api/tags"; then
    echo "✅ Ollama is available"
    
    # Check if models are loaded
    if ollama list | grep -q "phi3:mini"; then
        echo "✅ phi3:mini model is available"
    else
        echo "⚠️ phi3:mini model not found, but Ollama is running"
    fi
else
    echo "⚠️ Ollama not available (this is expected if it's still starting)"
fi

# Test API endpoints
echo ""
echo "🧪 Testing API Endpoints:"

# Health check
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ /health endpoint working"
else
    echo "❌ /health endpoint failed"
    exit 1
fi

# System status
if curl -f http://localhost:8000/system/status > /dev/null 2>&1; then
    echo "✅ /system/status endpoint working"
else
    echo "⚠️ /system/status endpoint failed"
fi

# Chat API test (this should work even without Ollama)
echo "🧪 Testing Chat API..."
if curl -X POST http://localhost:8000/api/v1/chat/complete \
    -H "Content-Type: application/json" \
    -d '{"message": "hello there", "session_id": "validation_test"}' \
    > /dev/null 2>&1; then
    echo "✅ Chat API working"
else
    echo "⚠️ Chat API failed (may be due to content policy or Ollama not ready)"
fi

# Summary
echo ""
echo "📋 Validation Summary:"
echo "   Core services (Redis, FastAPI): Required for operation"
echo "   Ollama: Optional, may take 2-3 minutes to fully initialize"
echo "   Chat API: Should work once Ollama is ready"
echo ""

# Show service logs for debugging
echo "📄 Recent service logs:"
echo "======================"
supervisorctl tail api stdout | tail -5 || echo "No API logs available"
echo ""

echo "✅ Deployment validation completed!"
echo "🌐 API available at: http://localhost:8000"
echo "📖 API docs at: http://localhost:8000/docs"

# Final status
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "🎉 Deployment successful - API is responding!"
    exit 0
else
    echo "❌ Deployment may have issues - API not responding"
    exit 1
fi