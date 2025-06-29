#!/bin/bash
# Direct fix for Ollama connection issue
echo "🚨 Direct Ollama Connection Fix"
echo "==============================="

echo "1. Checking current Ollama status..."
curl -s http://localhost:11434/api/version || echo "❌ Ollama not accessible"

echo ""
echo "2. Checking config values in app..."
cd /app && python3 -c "
import os
from app.core.config import get_settings
settings = get_settings()
print(f'OLLAMA_HOST from env: {os.getenv(\"OLLAMA_HOST\")}')
print(f'OLLAMA_HOST from settings: {settings.ollama_host}')
print(f'Settings debug: {settings.debug}')
print(f'Settings environment: {settings.environment}')
"

echo ""
echo "3. Force updating the config file directly..."
cd /app && python3 -c "
# Update the config default
import re

with open('/app/app/core/config.py', 'r') as f:
    content = f.read()

# Find and replace the ollama_host default
old_pattern = r'ollama_host: str = Field\(\s*default_factory=lambda: os\.getenv\(\"OLLAMA_HOST\", \"[^\"]*\"\)\s*\)'
new_pattern = 'ollama_host: str = Field(default_factory=lambda: os.getenv(\"OLLAMA_HOST\", \"http://localhost:11434\"))'

if 'ollama_host: str = Field(' in content:
    content = re.sub(old_pattern, new_pattern, content)
    print('✅ Updated ollama_host default in config.py')
else:
    print('❌ Could not find ollama_host field to update')

with open('/app/app/core/config.py', 'w') as f:
    f.write(content)

print('Config file updated')
"

echo ""
echo "4. Updating supervisor environment inline..."
# Update the supervisor config file directly
sed -i 's|OLLAMA_HOST=\"http://localhost:11434\"|OLLAMA_HOST=\"http://localhost:11434\"|g' /app/docker/supervisor.conf

echo ""
echo "5. Restarting the FastAPI app..."
supervisorctl restart ai-search-app
sleep 15

echo ""
echo "6. Testing after restart..."
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello direct fix","stream":false}'

echo ""
echo "7. Checking system status..."
curl -s http://localhost:8000/system/status | jq '.components'

echo ""
echo "8. If still failing, trying nuclear restart..."
if curl -s http://localhost:8000/system/status | grep -q '"ollama": "disconnected"'; then
    echo "Still disconnected, doing nuclear restart..."
    supervisorctl restart all
    sleep 20
    
    echo "Testing after nuclear restart..."
    curl -X POST http://localhost:8000/api/v1/chat/complete \
      -H "Content-Type: application/json" \
      -d '{"message":"Hello after nuclear restart","stream":false}'
fi

echo ""
echo "🎯 Direct fix complete!"
