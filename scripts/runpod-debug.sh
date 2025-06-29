#!/bin/bash
# RunPod Debug Script - Diagnose container startup issues

echo "🔍 RunPod Container Diagnostic Script"
echo "======================================"

echo "📁 Checking directory structure:"
echo "  /app exists: $(test -d /app && echo "✅ YES" || echo "❌ NO")"
echo "  /app/logs exists: $(test -d /app/logs && echo "✅ YES" || echo "❌ NO")"
echo "  /etc/supervisor/conf.d exists: $(test -d /etc/supervisor/conf.d && echo "✅ YES" || echo "❌ NO")"

echo -e "\n📄 Files in /etc/supervisor/conf.d/:"
ls -la /etc/supervisor/conf.d/ 2>/dev/null || echo "Directory not accessible"

echo -e "\n📄 Files in /app/logs/:"
ls -la /app/logs/ 2>/dev/null || echo "Directory not accessible"

echo -e "\n🔧 Supervisor configuration files:"
find /etc/supervisor -name "*.conf" -exec echo "  {}" \; 2>/dev/null

echo -e "\n📋 Environment variables:"
echo "  RUNPOD_POD_ID: ${RUNPOD_POD_ID:-NOT_SET}"
echo "  RUNPOD_TCP_PORT_8000: ${RUNPOD_TCP_PORT_8000:-NOT_SET}"
echo "  OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-NOT_SET}"
echo "  ENVIRONMENT: ${ENVIRONMENT:-NOT_SET}"

echo -e "\n🧪 Testing supervisor configuration:"
supervisord -t -c /etc/supervisor/supervisord.conf 2>&1

echo -e "\n📖 Contents of ai-search.conf (if exists):"
if [[ -f /etc/supervisor/conf.d/ai-search.conf ]]; then
    cat /etc/supervisor/conf.d/ai-search.conf
else
    echo "❌ File not found"
fi

echo -e "\n📖 Contents of supervisord.conf:"
if [[ -f /etc/supervisor/supervisord.conf ]]; then
    cat /etc/supervisor/supervisord.conf
else
    echo "❌ Main supervisor config not found"
fi

echo -e "\n✅ Diagnostic complete"
