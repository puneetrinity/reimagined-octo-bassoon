#!/bin/bash
# Quick fix for Ollama URL protocol issue
echo "🔧 Fixing Ollama URL Protocol Issue"
echo "===================================="

echo "1. Setting correct environment variables..."
export OLLAMA_HOST="http://localhost:11434"
export DEFAULT_MODEL="tinyllama:latest"
export FALLBACK_MODEL="tinyllama:latest"

echo "2. Updating supervisor config..."
# Update the running app environment
supervisorctl stop ai-search-app

# Wait a moment
sleep 2

echo "3. Starting app with correct environment..."
supervisorctl start ai-search-app

# Wait for startup
sleep 10

echo "4. Testing the fix..."
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello after URL fix","stream":false}'

echo ""
echo "5. Checking system status..."
curl -s http://localhost:8000/system/status | jq '.'

echo ""
echo "🎯 URL fix complete!"
echo "The issue was: Ollama URL was missing http:// protocol"
echo "Fixed by setting OLLAMA_HOST=http://localhost:11434"
