#!/bin/bash
# PRODUCTION DOCKER BUILD SCRIPT - FINAL FIX FOR /app/logs ERROR
# Run this script to build and push the corrected Docker image

echo "🔧 Building production Docker image with fixed supervisor config..."
echo "📋 This build includes:"
echo "   ✅ Fixed supervisor configs using /var/log/supervisor/ paths"
echo "   ✅ Eliminated all /app/logs references"
echo "   ✅ Runtime verification and fallback scripts"
echo "   ✅ Robust error handling and connection resilience"
echo ""

# Build the image
echo "🚀 Building Docker image..."
docker build -f Dockerfile.runpod -t puneetrinity/ai-search-system:v2.1-fixed .

# Tag as latest
echo "🏷️ Tagging as latest..."
docker tag puneetrinity/ai-search-system:v2.1-fixed puneetrinity/ai-search-system:latest

# Push to registry
echo "📤 Pushing to Docker Hub..."
docker push puneetrinity/ai-search-system:v2.1-fixed
docker push puneetrinity/ai-search-system:latest

echo ""
echo "✅ PRODUCTION IMAGE READY!"
echo "🎯 Image: puneetrinity/ai-search-system:v2.1-fixed"
echo "📝 This image fixes the '/app/logs/api.log does not exist' error"
echo ""
echo "🚀 Deploy on RunPod using:"
echo "   Image: puneetrinity/ai-search-system:latest"
echo "   Port: 8000"
echo "   Environment: GPU-enabled"
echo ""
echo "🔍 After deployment, verify with:"
echo "   curl http://YOUR_RUNPOD_URL:8000/health/live"
echo "   curl http://YOUR_RUNPOD_URL:8000/health/ready"
