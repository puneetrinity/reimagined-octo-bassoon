#!/bin/bash
# Comprehensive System Status Check
# This script checks all components of the AI Search System

set -e

echo "🔍 COMPREHENSIVE SYSTEM STATUS CHECK"
echo "===================================="

cd /workspace/ubiquitous-octo-invention

echo "📊 1. SUPERVISOR SERVICE STATUS"
echo "------------------------------"
supervisorctl status
echo ""

echo "🔧 2. OLLAMA MODEL STATUS"
echo "------------------------"
curl -s http://localhost:11434/api/tags | jq '.' || echo "❌ Ollama not responding"
echo ""

echo "🏥 3. FASTAPI HEALTH CHECK"
echo "-------------------------"
curl -s http://localhost:8000/health | jq '.' || echo "❌ FastAPI not responding"
echo ""

echo "🔗 4. REDIS CONNECTION"
echo "----------------------"
redis-cli ping || echo "❌ Redis not responding"
echo ""

echo "🧪 5. API ENDPOINTS CHECK"
echo "-------------------------"

# Test health endpoint
echo "📍 Testing /health"
curl -s -w "HTTP %{http_code}\n" http://localhost:8000/health | head -1

# Test model endpoints
echo "📍 Testing /api/v1/models"
curl -s -w "HTTP %{http_code}\n" http://localhost:8000/api/v1/models | head -1

# Test chat endpoint
echo "📍 Testing /api/v1/chat/complete"
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message": "Test"}' \
  -s -w "HTTP %{http_code}\n" | tail -1

echo ""
echo "📋 6. RECENT FASTAPI LOGS"
echo "-------------------------"
echo "Last 20 lines from FastAPI logs:"
supervisorctl tail ai-search-app | tail -20

echo ""
echo "🏁 STATUS CHECK COMPLETED!"
echo "=========================="
echo ""
echo "✅ Green items are working correctly"
echo "❌ Red items need attention"
echo ""
echo "For real-time logs: supervisorctl tail -f ai-search-app"
