#!/bin/bash
# Emergency CORS fix script - Run this in RunPod terminal or file manager
# This script updates the supervisor config and restarts the FastAPI service

echo "🚨 Emergency CORS Fix - Starting..."

# Backup current config
cp /app/docker/supervisor.conf /app/docker/supervisor.conf.backup
echo "✅ Config backed up"

# Update supervisor config with CORS fix
cat > /app/docker/supervisor.conf << 'EOF'
# Program definitions for AI Search System services
# This file is included by the main supervisord.conf

[program:redis]
command=redis-server --bind 0.0.0.0 --port 6379 --save 60 1000 --appendonly yes
directory=/workspace
autostart=true
autorestart=true
stderr_logfile=/workspace/logs/redis.err.log
stdout_logfile=/workspace/logs/redis.out.log
user=root
priority=50
startsecs=5
startretries=3

[program:ollama]
command=/usr/local/bin/ollama serve
directory=/workspace
autostart=true
autorestart=true
stderr_logfile=/workspace/logs/ollama.err.log
stdout_logfile=/workspace/logs/ollama.out.log
user=root
environment=OLLAMA_HOST="0.0.0.0:11434",CUDA_VISIBLE_DEVICES="0",OLLAMA_MODELS="/root/.ollama/models"
priority=100
startsecs=10
startretries=3

[program:ai-search-app]
command=python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info
directory=/app
autostart=true
autorestart=true
stderr_logfile=/workspace/logs/app.err.log
stdout_logfile=/workspace/logs/app.out.log
user=root
environment=REDIS_URL="redis://localhost:6379",OLLAMA_HOST="http://localhost:11434",PYTHONPATH="/app",ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000,https://feb7cb5f-ab08-463c-86a3-8fc7230da68e-00-3ruaw352aa5oh.kirk.replit.dev"
priority=300
startsecs=15
startretries=3

[program:model-init]
command=/app/init-models.sh
directory=/app
autostart=false
autorestart=false
startsecs=0
stderr_logfile=/workspace/logs/model-init.err.log
stdout_logfile=/workspace/logs/model-init.out.log
user=root
priority=400
exitcodes=0
stopsignal=TERM

[program:service-readiness]
command=/app/scripts/wait-for-services.sh
directory=/app
autostart=true
autorestart=false
startsecs=0
stderr_logfile=/workspace/logs/readiness.err.log
stdout_logfile=/workspace/logs/readiness.out.log
user=root
priority=500
exitcodes=0
EOF

echo "✅ Supervisor config updated with CORS fix"

# Copy to workspace if it exists there too
if [ -f /workspace/docker/supervisor.conf ]; then
    cp /app/docker/supervisor.conf /workspace/docker/supervisor.conf
    echo "✅ Workspace config also updated"
fi

# Restart the FastAPI service
echo "🔄 Restarting AI Search App service..."
supervisorctl stop ai-search-app
sleep 3
supervisorctl start ai-search-app

# Check status
echo "📊 Current service status:"
supervisorctl status

echo ""
echo "🎯 CORS Fix Applied!"
echo "✅ Your Replit frontend should now be able to connect"
echo "🌐 Allowed origins now include: https://feb7cb5f-ab08-463c-86a3-8fc7230da68e-00-3ruaw352aa5oh.kirk.replit.dev"
echo ""
echo "Test your frontend now - the CORS error should be resolved!"
