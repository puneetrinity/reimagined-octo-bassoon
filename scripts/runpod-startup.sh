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
mkdir -p /app/logs /var/log/supervisor /root/.ollama/models /app/cache

# Create all log files that supervisor expects
echo "📝 Creating log files..."
touch /app/logs/api.log
touch /app/logs/redis.err.log /app/logs/redis.out.log
touch /app/logs/ollama.err.log /app/logs/ollama.out.log
touch /app/logs/model-init.err.log /app/logs/model-init.out.log
touch /app/logs/health.err.log /app/logs/health.out.log

# Set proper permissions
chmod 666 /app/logs/*.log
chmod 755 /app/scripts/*.py 2>/dev/null || true
chmod 755 /app/scripts/*.sh 2>/dev/null || true

# Verify supervisor configuration
echo "🔧 Checking supervisor configuration..."
if [[ ! -f /etc/supervisor/conf.d/ai-search.conf ]]; then
    echo "❌ Supervisor config not found!"
    exit 1
fi

# Test configuration
supervisord -t -c /etc/supervisor/supervisord.conf || {
    echo "❌ Supervisor configuration test failed!"
    exit 1
}

echo "✅ Pre-startup checks completed successfully"

# Start supervisor
echo "🎯 Starting services with supervisord..."
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
