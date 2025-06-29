#!/bin/bash
# Quick fix for the model manager bug on current RunPod instance

echo "🔧 Applying critical model manager bug fix..."

# Fix the _stats bug in the model manager
sed -i 's/_stats\[/base_stats[/g' /app/app/models/manager.py

echo "✅ Bug fix applied. Restarting FastAPI app..."

# Restart the FastAPI app to pick up the fix
supervisorctl restart ai-search-app 2>/dev/null

sleep 5

echo "🔍 Checking health status..."
curl -s https://tn2p581oxspb4b-8000.proxy.runpod.net/health | python3 -m json.tool

echo ""
echo "✅ Model manager fix complete!"
