#!/bin/bash
# Final definitive fix for Ollama connection
echo "🎯 FINAL DEFINITIVE OLLAMA FIX"
echo "============================="

echo "1. Current status check..."
echo "Ollama direct test:"
curl -s http://localhost:11434/api/version
echo ""

echo "Environment variable issue detected:"
echo "OLLAMA_HOST should be http://localhost:11434"
echo "But showing: $(printenv OLLAMA_HOST)"

echo ""
echo "2. Fixing supervisor config directly..."
# Update the supervisor config to use localhost instead of 0.0.0.0
if [ -f /workspace/docker/supervisor.conf ]; then
    CONFIG_FILE="/workspace/docker/supervisor.conf"
elif [ -f /app/docker/supervisor.conf ]; then
    CONFIG_FILE="/app/docker/supervisor.conf"
else
    echo "❌ Could not find supervisor.conf"
    CONFIG_FILE=""
fi

if [ -n "$CONFIG_FILE" ]; then
    echo "Updating $CONFIG_FILE"
    sed -i 's|OLLAMA_HOST="0.0.0.0:11434"|OLLAMA_HOST="http://localhost:11434"|g' "$CONFIG_FILE"
    sed -i 's|OLLAMA_HOST="http://localhost:11434"|OLLAMA_HOST="http://localhost:11434"|g' "$CONFIG_FILE"
    echo "✅ Updated supervisor config"
fi

echo ""
echo "3. Restarting supervisor to reload config..."
supervisorctl reread
supervisorctl update

echo ""
echo "4. Restarting all services..."
supervisorctl restart all
sleep 20

echo ""
echo "5. Setting runtime environment variables..."
export OLLAMA_HOST="http://localhost:11434"
export DEFAULT_MODEL="tinyllama:latest"
export FALLBACK_MODEL="tinyllama:latest"

echo ""
echo "6. Testing Ollama connection from Python..."
cd /app && python3 -c "
import os
print(f'Environment OLLAMA_HOST: {os.getenv(\"OLLAMA_HOST\")}')

# Test direct connection
import asyncio
import httpx

async def test_ollama():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get('http://localhost:11434/api/version')
            print(f'✅ Ollama responds: {response.json()}')
            
            # Test generation
            response = await client.post('http://localhost:11434/api/generate', 
                json={'model': 'tinyllama:latest', 'prompt': 'Hello', 'stream': False})
            result = response.json()
            print(f'✅ Generation test: {result.get(\"response\", \"No response\")}')
            
    except Exception as e:
        print(f'❌ Ollama test failed: {e}')

asyncio.run(test_ollama())
"

echo ""
echo "7. Final test of chat endpoint..."
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message":"Final definitive test","stream":false}'

echo ""
echo "8. System status check..."
curl -s http://localhost:8000/system/status | jq '.components'

echo ""
echo "🎯 FINAL FIX COMPLETE!"
echo "If this doesn't work, the issue is deeper in the FastAPI application layer."
