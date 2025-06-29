#!/bin/bash
# AI Model Diagnostic and Fix Script for RunPod
# This script diagnoses and fixes model initialization issues

echo "🔍 AI Model Diagnostic & Fix Script"
echo "==================================="

# Function to test API endpoint
test_api_endpoint() {
    local endpoint=$1
    local description=$2
    echo "Testing $description..."
    
    if curl -f -s -m 10 "$endpoint" > /dev/null 2>&1; then
        echo "✅ $description - OK"
        return 0
    else
        echo "❌ $description - FAILED"
        return 1
    fi
}

# Function to test model with simple prompt
test_model_generation() {
    local model=$1
    echo "Testing model: $model"
    
    # Test with a very simple prompt
    local test_response=$(curl -s -X POST http://localhost:11434/api/generate \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$model\",\"prompt\":\"Say hello\",\"stream\":false}" \
        --max-time 30)
    
    if echo "$test_response" | jq -e '.response' > /dev/null 2>&1; then
        local response_text=$(echo "$test_response" | jq -r '.response')
        if [ -n "$response_text" ] && [ "$response_text" != "null" ]; then
            echo "✅ Model $model working - Response: $response_text"
            return 0
        fi
    fi
    
    echo "❌ Model $model failed - Response: $test_response"
    return 1
}

echo "1. Checking service status..."
supervisorctl status

echo ""
echo "2. Testing API endpoints..."
test_api_endpoint "http://localhost:6379/ping" "Redis"
test_api_endpoint "http://localhost:11434/api/version" "Ollama"
test_api_endpoint "http://localhost:8000/health" "FastAPI"

echo ""
echo "3. Checking available models..."
if curl -f -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "📋 Available models:"
    curl -s http://localhost:11434/api/tags | jq -r '.models[].name' || echo "No models found"
    
    echo ""
    echo "4. Testing model functionality..."
    
    # Test each available model
    models=$(curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "")
    
    if [ -z "$models" ]; then
        echo "❌ No models available. Initializing models..."
        
        # Force model initialization
        echo "🔄 Pulling essential models..."
        supervisorctl stop model-init 2>/dev/null || true
        supervisorctl start model-init
        
        # Wait for model initialization
        for i in {1..60}; do
            if [ -f /workspace/models/.initialized ]; then
                echo "✅ Model initialization complete"
                break
            fi
            echo "⏳ Waiting for models... ($i/60)"
            sleep 5
        done
        
        # Recheck models
        models=$(curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "")
    fi
    
    working_models=()
    failed_models=()
    
    for model in $models; do
        if test_model_generation "$model"; then
            working_models+=("$model")
        else
            failed_models+=("$model")
        fi
    done
    
    echo ""
    echo "📊 Model Test Results:"
    echo "✅ Working models: ${working_models[*]}"
    echo "❌ Failed models: ${failed_models[*]}"
    
    # If no models are working, try to fix
    if [ ${#working_models[@]} -eq 0 ]; then
        echo ""
        echo "🚨 No models are working! Attempting fixes..."
        
        # Restart Ollama service
        echo "🔄 Restarting Ollama..."
        supervisorctl restart ollama
        sleep 10
        
        # Try pulling a simple model
        echo "🔄 Pulling tinyllama model..."
        ollama pull tinyllama:latest
        
        # Test again
        echo "🔄 Testing tinyllama..."
        if test_model_generation "tinyllama:latest"; then
            echo "✅ Fixed! tinyllama is now working"
        else
            echo "❌ Still having issues. Manual intervention may be needed."
        fi
    fi
    
else
    echo "❌ Cannot connect to Ollama API"
    echo "🔄 Restarting Ollama service..."
    supervisorctl restart ollama
    sleep 10
    
    # Recheck
    if curl -f -s http://localhost:11434/api/version > /dev/null 2>&1; then
        echo "✅ Ollama restarted successfully"
    else
        echo "❌ Ollama still not responding"
    fi
fi

echo ""
echo "5. Testing FastAPI chat endpoint..."
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "🔄 Testing chat completion..."
    
    chat_response=$(curl -s -X POST http://localhost:8000/api/v1/chat/complete \
        -H "Content-Type: application/json" \
        -d '{"message":"Hello, test message","stream":false}' \
        --max-time 30)
    
    if echo "$chat_response" | jq -e '.success' > /dev/null 2>&1; then
        echo "✅ Chat endpoint working"
        echo "📝 Response preview: $(echo "$chat_response" | jq -r '.data.content' | head -c 100)..."
    else
        echo "❌ Chat endpoint failed"
        echo "📝 Error response: $chat_response"
        
        # Try restarting the FastAPI service
        echo "🔄 Restarting FastAPI service..."
        supervisorctl restart ai-search-app
        sleep 5
        
        echo "🔄 Retesting chat endpoint..."
        chat_response=$(curl -s -X POST http://localhost:8000/api/v1/chat/complete \
            -H "Content-Type: application/json" \
            -d '{"message":"Hello after restart","stream":false}' \
            --max-time 30)
        
        if echo "$chat_response" | jq -e '.success' > /dev/null 2>&1; then
            echo "✅ Chat endpoint working after restart"
        else
            echo "❌ Chat endpoint still failing after restart"
        fi
    fi
else
    echo "❌ FastAPI not responding"
fi

echo ""
echo "6. System Summary:"
echo "=================="
echo "📊 Memory usage:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null || echo "No GPU info available"

echo ""
echo "📋 Service status:"
supervisorctl status

echo ""
echo "🔧 Quick fixes applied:"
echo "- Checked and restarted failed services"
echo "- Initialized missing models"
echo "- Tested API endpoints"

echo ""
echo "💡 If issues persist:"
echo "1. Check logs: supervisorctl tail ai-search-app"
echo "2. Check Ollama logs: supervisorctl tail ollama"
echo "3. Restart all services: supervisorctl restart all"

echo ""
echo "🎯 Diagnostic complete!"
