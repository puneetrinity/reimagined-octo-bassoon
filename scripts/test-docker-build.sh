#!/bin/bash
# Local Docker Build Test for RunPod Container
# This script helps verify the container builds correctly before pushing

echo "🔧 Building RunPod Docker container locally..."

# Build the container
docker build -f Dockerfile.runpod -t ai-search-test:local . || {
    echo "❌ Docker build failed!"
    exit 1
}

echo "✅ Docker build successful!"

# Test directory structure inside the container
echo "🔍 Testing directory structure in container..."
docker run --rm ai-search-test:local bash -c "
echo 'Directory structure test:'
echo '  /app exists: $(test -d /app && echo \"✅ YES\" || echo \"❌ NO\")'
echo '  /app/logs exists: $(test -d /app/logs && echo \"✅ YES\" || echo \"❌ NO\")'
echo '  /app/logs writable: $(test -w /app/logs && echo \"✅ YES\" || echo \"❌ NO\")'
echo '  supervisord.conf: $(test -f /etc/supervisor/supervisord.conf && echo \"✅ YES\" || echo \"❌ NO\")'
echo '  ai-search.conf: $(test -f /etc/supervisor/conf.d/ai-search.conf && echo \"✅ YES\" || echo \"❌ NO\")'
echo ''
echo 'Log files in /app/logs:'
ls -la /app/logs/ 2>/dev/null || echo 'No files found'
echo ''
echo 'Supervisor configuration test:'
supervisord -t -c /etc/supervisor/supervisord.conf 2>&1
"

echo "🧪 Test startup script..."
docker run --rm ai-search-test:local /app/scripts/runpod-debug.sh

echo "✅ Local container test completed!"
echo "💡 If tests pass, the container should work on RunPod"
