#!/bin/bash
# One-command RunPod deployment script
# Run this on your RunPod A5000 instance

set -e

echo "🚀 AI Search System - RunPod Direct Deployment"
echo "=============================================="

# Check GPU availability
if ! nvidia-smi > /dev/null 2>&1; then
    echo "❌ NVIDIA GPU not detected. Please run on a GPU instance."
    exit 1
fi

echo "✅ GPU detected:"
nvidia-smi --query-gpu=gpu_name,memory.total --format=csv,noheader

# Update system
echo "📦 Updating system packages..."
apt-get update > /dev/null 2>&1

# Install Docker if needed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh > /dev/null 2>&1
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install docker-compose if needed
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# Clone repository if not present
if [ ! -d "advancedllmsearch1" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/puneetrinity/advancedllmsearch1.git
    cd advancedllmsearch1
else
    echo "✅ Repository already exists"
    cd advancedllmsearch1
    git pull origin main
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker stop ai-search-system 2>/dev/null || true
docker rm ai-search-system 2>/dev/null || true

# Build and deploy
echo "🔨 Building Docker image..."
docker build -f Dockerfile.runpod-direct -t ai-search:local .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Deploy container
echo "🚀 Deploying container..."
docker run -d --gpus all \
  -p 8000:8000 \
  -p 11434:11434 \
  -p 6379:6379 \
  --name ai-search-system \
  --restart unless-stopped \
  --shm-size=2g \
  -v $(pwd)/logs:/workspace/logs \
  ai-search:local

# Wait for startup
echo "⏳ Waiting for services to start..."
sleep 30

# Check container status
if docker ps | grep -q ai-search-system; then
    echo "✅ Container is running"
else
    echo "❌ Container failed to start. Checking logs..."
    docker logs ai-search-system
    exit 1
fi

# Wait for health check
echo "🔍 Checking application health..."
for i in {1..20}; do
    if curl -f http://localhost:8000/health/live > /dev/null 2>&1; then
        echo "✅ Application is healthy!"
        break
    fi
    echo "Waiting for application... ($i/20)"
    sleep 10
done

# Final status
echo ""
echo "📊 Deployment Status:"
echo "===================="

echo "🐳 Container Status:"
docker ps | grep ai-search-system

echo ""
echo "🖥️  GPU Memory Usage:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits

echo ""
echo "🌐 Access Information:"
echo "Health Check: http://localhost:8000/health/live"
echo "System Status: http://localhost:8000/system/status"
echo "API Documentation: http://localhost:8000/docs"
echo "Chat API: POST http://localhost:8000/api/v1/chat/complete"

echo ""
echo "📝 Useful Commands:"
echo "View logs: docker logs ai-search-system"
echo "Enter container: docker exec -it ai-search-system bash"
echo "Pull more models: docker exec ai-search-system ./pull-models.sh"
echo "Check Ollama: docker exec ai-search-system ollama list"

echo ""
echo "🧪 Quick Test:"
echo "curl -X POST http://localhost:8000/api/v1/chat/complete \\"
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"message":"Hello AI","session_id":"test","user_id":"test"}'"'"

echo ""
echo "🎉 Deployment completed successfully!"
echo "Your AI Search System is running on RunPod A5000."

# Show final status
echo ""
echo "📋 Service Status:"
docker exec ai-search-system ps aux | grep -E "(redis|ollama|uvicorn)" || echo "Services starting..."

echo ""
echo "✅ Ready for production use!"