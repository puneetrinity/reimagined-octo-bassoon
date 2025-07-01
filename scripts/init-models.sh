#!/bin/bash
# Ollama model initialization script for RunPod
# This script ensures the required models are downloaded and ready

set -e

echo "🤖 Ollama Model Initialization Script"
echo "====================================="

# Wait for Ollama service to be ready
echo "⏳ Waiting for Ollama service to start..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama service is ready!"
        break
    fi
    
    echo "⏳ Attempt $((attempt + 1))/$max_attempts - Waiting for Ollama..."
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Ollama service failed to start after $max_attempts attempts"
    echo "🔍 Checking Ollama process:"
    ps aux | grep ollama || echo "No Ollama processes found"
    echo "🔍 Checking port 11434:"
    netstat -tlnp | grep 11434 || echo "Port 11434 not listening"
    exit 1
fi

# Function to download model with retry logic
download_model() {
    local model_name="$1"
    local max_retries=3
    local retry=0
    
    echo "📦 Downloading model: $model_name"
    
    while [ $retry -lt $max_retries ]; do
        if ollama pull "$model_name"; then
            echo "✅ Successfully downloaded $model_name"
            return 0
        else
            retry=$((retry + 1))
            echo "❌ Failed to download $model_name (attempt $retry/$max_retries)"
            if [ $retry -lt $max_retries ]; then
                echo "⏳ Retrying in 10 seconds..."
                sleep 10
            fi
        fi
    done
    
    echo "❌ Failed to download $model_name after $max_retries attempts"
    return 1
}

# Check if models already exist
echo "🔍 Checking existing models..."
if ! ollama list >/dev/null 2>&1; then
    echo "❌ Cannot connect to ollama service for model check"
    exit 1
fi

if ollama list | grep -q "phi3:mini"; then
    echo "✅ phi3:mini model already exists"
else
    echo "📦 phi3:mini model not found, downloading..."
    if ! download_model "phi3:mini"; then
        echo "❌ Failed to download phi3:mini - this is critical"
        exit 1
    fi
fi

# Optional: Download additional models for better performance
echo "🔍 Checking for additional models..."

# Uncomment to download more models
# if ! ollama list | grep -q "llama2:7b"; then
#     echo "📦 Downloading llama2:7b for enhanced capabilities..."
#     download_model "llama2:7b" || echo "⚠️ Failed to download llama2:7b"
# fi

# List all available models
echo "📋 Available models:"
if ! ollama list; then
    echo "❌ Failed to list models - ollama may not be ready"
    exit 1
fi

# Test model functionality
echo "🧪 Testing model functionality..."
if echo "Hello, this is a test." | ollama run phi3:mini > /dev/null 2>&1; then
    echo "✅ Model test successful!"
else
    echo "⚠️ Model test failed, but continuing..."
fi

echo "🎉 Model initialization complete!"
echo "📊 Model statistics:"
if ! ollama list; then
    echo "❌ Failed to get final model statistics"
    exit 1
fi

# Create a flag file to indicate initialization is complete
mkdir -p /root/.ollama/models
touch /root/.ollama/models/.initialized
echo "✅ Initialization flag created"

echo "🚀 Ollama is ready for use!"