#!/bin/bash
# Deep diagnostic script to find the FastAPI issue
echo "🔍 Deep FastAPI Diagnostic"
echo "=========================="

echo "1. Checking FastAPI app logs..."
supervisorctl tail ai-search-app stderr | tail -20

echo ""
echo "2. Testing with detailed curl..."
curl -v -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","stream":false}' 2>&1 | tail -10

echo ""
echo "3. Check if the FastAPI app is using the right model..."
curl -s http://localhost:8000/health | jq '.' || echo "Health endpoint failed"

echo ""
echo "4. Check model manager status..."
curl -s http://localhost:8000/status | jq '.models' || echo "Status endpoint failed"

echo ""
echo "5. Testing with different request format..."
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello", 
    "stream": false,
    "quality_requirement": "minimal",
    "max_execution_time": 30
  }'

echo ""
echo "6. Check Python path and imports..."
cd /app && python3 -c "
import sys
print('Python path:')
for p in sys.path: print(f'  {p}')
print('\\nImport test:')
try:
    from app.models.manager import ModelManager
    print('✅ ModelManager import OK')
except Exception as e:
    print(f'❌ ModelManager import failed: {e}')
try:
    from app.models.ollama_client import OllamaClient
    print('✅ OllamaClient import OK')
except Exception as e:
    print(f'❌ OllamaClient import failed: {e}')
"

echo ""
echo "🎯 Analysis complete! Check the errors above."
