#!/bin/bash
# Model initialization script for RunPod A5000
# Downloads and prepares recruitment-optimized models

set -e

echo "Initializing AI models for recruitment workflow..."

# Wait for Ollama to be fully ready
echo "Ensuring Ollama is ready..."
for i in {1..60}; do
    if curl -f http://localhost:11434/api/version > /dev/null 2>&1; then
        echo "Ollama is ready"
        break
    fi
    echo "Waiting for Ollama... ($i/60)"
    sleep 5
    
    # If it's taking too long, check if Ollama is even running
    if [ $i -eq 30 ]; then
        echo "Ollama taking longer than expected, checking status..."
        ps aux | grep ollama | grep -v grep || echo "No Ollama process found"
        supervisorctl status ollama || echo "Ollama not in supervisor"
    fi
done

# Final check
if ! curl -f http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "ERROR: Ollama is not responding after 5 minutes. Cannot initialize models."
    echo "This is not fatal - models can be pulled manually later."
    exit 0  # Exit gracefully to not crash the container
fi

# Function to pull model with retry logic
pull_model() {
    local model=$1
    local max_retries=3
    local retry=1
    
    while [ $retry -le $max_retries ]; do
        echo "Pulling $model (attempt $retry/$max_retries)..."
        if ollama pull $model; then
            echo "Successfully pulled $model"
            return 0
        else
            echo "Failed to pull $model (attempt $retry/$max_retries)"
            retry=$((retry + 1))
            sleep 10
        fi
    done
    
    echo "Failed to pull $model after $max_retries attempts"
    return 1
}

# Pull recruitment-optimized models based on A5000 memory strategy
echo "Pulling recruitment models..."

# Tier 0: Always loaded (lightweight)
echo "Tier 0: Lightweight models (always loaded)"
pull_model "phi3:mini" || echo "Warning: Failed to pull phi3:mini"

# Tier 1: Keep warm (primary recruitment models)
echo "Tier 1: Primary recruitment models (keep warm)"
pull_model "deepseek-llm:7b" || echo "Warning: Failed to pull deepseek-llm:7b"
pull_model "mistral:7b" || echo "Warning: Failed to pull mistral:7b"

# Tier 2: Load on demand (complex reasoning)
echo "Tier 2: Complex reasoning models (on-demand)"
pull_model "llama3:8b" || echo "Warning: Failed to pull llama3:8b"

# Alternative lightweight models as fallbacks
echo "Fallback models"
pull_model "tinyllama:latest" || echo "Warning: Failed to pull tinyllama"

# List available models
echo "Available models:"
ollama list

# Test model functionality
echo "Testing model functionality..."

test_model() {
    local model=$1
    echo "Testing $model..."
    # Use a simpler test that doesn't require interactive input
    if ollama run $model "Say OK" 2>/dev/null | head -1 | grep -q -i "ok"; then
        echo "$model is working"
    else
        echo "$model loaded but test response unclear"
    fi
}

# Test key models (only if they were successfully pulled)
if ollama list | grep -q "phi3:mini"; then
    test_model "phi3:mini"
fi

echo "Model initialization complete!"
echo "Memory usage:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits

echo "Available models for recruitment tasks:"
echo "- Resume Parsing: deepseek-llm:7b"
echo "- Bias Detection: mistral:7b" 
echo "- Matching Logic: llama3:8b"
echo "- Script Generation: llama3:8b"
echo "- Report Generation: phi3:mini"
echo "- Fallback: tinyllama:latest"

# Mark initialization as complete
mkdir -p /workspace/models
touch /workspace/models/.initialized
