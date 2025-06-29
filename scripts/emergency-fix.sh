#!/bin/bash
# Emergency fix script for RunPod deployment

echo "🔧 Emergency fix for supervisor config..."

# Create the config file manually with the correct content
cat > /etc/supervisor/conf.d/ai-search.conf << 'EOF'
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
environment=REDIS_URL="redis://localhost:6379",OLLAMA_HOST="http://localhost:11434",PYTHONPATH="/app"
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

echo "✅ Config file created. Reloading supervisor..."

# Reload supervisor
supervisorctl reread 2>/dev/null
supervisorctl update 2>/dev/null

echo "🔍 Checking services..."
supervisorctl status 2>/dev/null

echo "🚀 Starting services..."
supervisorctl start redis 2>/dev/null
supervisorctl start ollama 2>/dev/null
supervisorctl start ai-search-app 2>/dev/null
supervisorctl start service-readiness 2>/dev/null

echo "✅ Fix complete! Check status with: supervisorctl status 2>/dev/null"
