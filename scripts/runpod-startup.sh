#!/bin/bash
# RunPod startup script - ensures all directories and dependencies are ready

set -e

echo "🚀 Starting AI Search System - RunPod Container"
echo "================================================="

# Environment information
echo "Environment configured:"
echo "  - Ollama: ${OLLAMA_BASE_URL:-http://localhost:11434}"
echo "  - Environment: ${ENVIRONMENT:-production}"
echo "  - API: 0.0.0.0:8000"
echo "  - RunPod Pod ID: ${RUNPOD_POD_ID:-unknown}"
echo "  - RunPod Port: ${RUNPOD_TCP_PORT_8000:-8000}"

# Ensure all required directories exist
echo "📁 Creating required directories..."
mkdir -p /app/logs /var/log/supervisor /root/.ollama/models /app/cache /var/run

# Verify critical directories exist
if [[ ! -d /app/logs ]]; then
    echo "❌ Failed to create /app/logs directory!"
    exit 1
fi

echo "✅ Directory /app/logs exists and is writable: $(test -w /app/logs && echo "YES" || echo "NO")"

# Create all log files that supervisor expects
echo "📝 Creating log files..."
touch /app/logs/api.log
touch /app/logs/redis.err.log /app/logs/redis.out.log
touch /app/logs/ollama.err.log /app/logs/ollama.out.log
touch /app/logs/model-init.err.log /app/logs/model-init.out.log
touch /app/logs/health.err.log /app/logs/health.out.log
touch /app/logs/supervisord.log

# Set proper permissions
chmod 666 /app/logs/*.log 2>/dev/null || echo "⚠️ Some log files may not exist yet"
chmod 755 /app/scripts/*.py 2>/dev/null || true
chmod 755 /app/scripts/*.sh 2>/dev/null || true

# Final verification before starting supervisor
echo "🔍 Final verification:"
echo "  /app/logs directory exists: $(test -d /app/logs && echo "✅" || echo "❌")"
echo "  /app/logs is writable: $(test -w /app/logs && echo "✅" || echo "❌")"
echo "  supervisord.conf exists: $(test -f /etc/supervisor/supervisord.conf && echo "✅" || echo "❌")"
echo "  ai-search.conf exists: $(test -f /etc/supervisor/conf.d/ai-search.conf && echo "✅" || echo "❌")"

# Exit if critical paths don't exist
if [[ ! -d /app/logs ]] || [[ ! -w /app/logs ]]; then
    echo "❌ Critical error: /app/logs directory is not accessible!"
    echo "📋 Current directory structure:"
    ls -la /app/ || echo "Cannot list /app"
    exit 1
fi

# Verify supervisor configuration
echo "🔧 Checking supervisor configuration..."
if [[ ! -f /etc/supervisor/conf.d/ai-search.conf ]]; then
    echo "❌ Supervisor config not found at /etc/supervisor/conf.d/ai-search.conf!"
    echo "📁 Listing contents of /etc/supervisor/conf.d/:"
    ls -la /etc/supervisor/conf.d/ || echo "Directory not found"
    exit 1
fi

echo "✅ Found supervisor config file"
echo "📄 Config file contents:"
cat /etc/supervisor/conf.d/ai-search.conf

# Test configuration
echo "🧪 Testing supervisor configuration..."
supervisord -t -c /etc/supervisor/supervisord.conf || {
    echo "❌ Supervisor configuration test failed!"
    echo "📋 Full error details:"
    supervisord -t -c /etc/supervisor/supervisord.conf 2>&1
    exit 1
}

echo "✅ Pre-startup checks completed successfully"

# Start supervisor
echo "🎯 Starting services with supervisord..."
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
