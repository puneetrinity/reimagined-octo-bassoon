#!/bin/bash
# RunPod startup script - ensures all directories and dependencies are ready

set -e

echo "🚀 Starting AI Search System - RunPod Container"
echo "================================================="

# FIRST PRIORITY: Create all directories that supervisor needs
echo "📁 Creating ALL required directories IMMEDIATELY..."
mkdir -p /app/logs /var/log/supervisor /root/.ollama/models /app/cache /var/run /tmp

# Force create the directory with explicit permissions
chmod 755 /app/logs /var/log/supervisor /var/run
chown root:root /app/logs /var/log/supervisor

# Verify the directory was created successfully
if [[ ! -d /app/logs ]]; then
    echo "❌ CRITICAL ERROR: Failed to create /app/logs directory!"
    echo "🔍 Current /app structure:"
    ls -la /app/ || echo "Cannot list /app"
    echo "🔍 Current filesystem info:"
    df -h
    exit 1
fi

# Test if directory is writable
if ! touch /app/logs/test.log 2>/dev/null; then
    echo "❌ CRITICAL ERROR: /app/logs directory is not writable!"
    echo "🔍 Directory permissions:"
    ls -ld /app/logs
    exit 1
fi

# Clean up test file
rm -f /app/logs/test.log

echo "✅ Successfully created and verified /app/logs directory"

# Now create all log files that supervisor expects
echo "📝 Creating ALL log files..."
touch /app/logs/api.log
touch /app/logs/redis.err.log /app/logs/redis.out.log
touch /app/logs/ollama.err.log /app/logs/ollama.out.log
touch /app/logs/model-init.err.log /app/logs/model-init.out.log
touch /app/logs/health.err.log /app/logs/health.out.log
touch /app/logs/supervisord.log

# Set proper permissions on all files
chmod 666 /app/logs/*.log 2>/dev/null || echo "⚠️ Some log files may not exist yet"
chmod 755 /app/scripts/*.py 2>/dev/null || true
chmod 755 /app/scripts/*.sh 2>/dev/null || true

echo "✅ All log files created successfully"

# Environment information
echo "🌍 Environment configured:"
echo "  - Ollama: ${OLLAMA_BASE_URL:-http://localhost:11434}"
echo "  - Environment: ${ENVIRONMENT:-production}"
echo "  - API: 0.0.0.0:8000"
echo "  - RunPod Pod ID: ${RUNPOD_POD_ID:-unknown}"
echo "  - RunPod Port: ${RUNPOD_TCP_PORT_8000:-8000}"

# Verify supervisor configuration - SAFE VERSION
echo "🔧 Checking supervisor configuration (using system paths)..."
echo "📄 Configuration files in use:"
echo "   Main config: /etc/supervisor/supervisord.conf"
echo "   Service config: /etc/supervisor/conf.d/ai-search.conf"

if [[ ! -f /etc/supervisor/conf.d/ai-search.conf ]]; then
    echo "❌ Supervisor config not found at /etc/supervisor/conf.d/ai-search.conf!"
    echo "📁 Listing contents of /etc/supervisor/conf.d/:"
    ls -la /etc/supervisor/conf.d/ || echo "Directory not found"
    exit 1
fi

echo "✅ Found supervisor config file"

# Show the actual configuration being used
echo "📋 Main supervisord.conf contents:"
echo "=================================="
cat /etc/supervisor/supervisord.conf | head -20
echo "=================================="

echo "📋 Service configuration contents:"
echo "=================================="
cat /etc/supervisor/conf.d/ai-search.conf | head -20
echo "=================================="

# Test configuration with verbose output
echo "🧪 Testing supervisor configuration..."
if ! supervisord -t -c /etc/supervisor/supervisord.conf 2>&1; then
    echo "❌ Supervisor configuration test failed!"
    echo "📋 Configuration file contents:"
    echo "=== /etc/supervisor/supervisord.conf ==="
    cat /etc/supervisor/supervisord.conf
    echo "=== /etc/supervisor/conf.d/ai-search.conf ==="
    cat /etc/supervisor/conf.d/ai-search.conf
    exit 1
fi

echo "✅ Supervisor configuration test passed"

echo "🎯 Starting supervisor in foreground mode..."
echo "   This will start all services: Redis -> Ollama -> FastAPI -> Model Init"

# Start supervisor - this should work now!
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
