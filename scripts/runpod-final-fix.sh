#!/bin/bash
# Final API Fix and Test Script for RunPod (Fixed Path)
# This script applies the final result format patch and tests the chat endpoint

set -e

echo "🎯 FINAL API FIX AND TEST (RUNPOD FIXED)"
echo "======================================="

# Use the correct workspace directory
cd /workspace

echo "🔧 Step 1: Apply API result format patch"

# Download and run the fix script directly
curl -s https://raw.githubusercontent.com/puneetrinity/ubiquitous-octo-invention/main/scripts/fix_api_result_format.py | python3

echo ""
echo "🔄 Step 2: Restart FastAPI service"
supervisorctl restart ai-search-app

echo ""
echo "⏳ Step 3: Wait for service to start"
sleep 5

echo ""
echo "🏥 Step 4: Check service health"
supervisorctl status

echo ""
echo "🧪 Step 5: Test chat endpoint with curl"

# Test with a simple message
echo "📤 Testing with: 'Hello, how are you?'"
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}' \
  --connect-timeout 30 \
  --max-time 60 \
  -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" || echo "❌ Request failed"

echo ""
echo "📤 Testing with: 'What is AI?'"
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message": "What is AI?"}' \
  --connect-timeout 30 \
  --max-time 60 \
  -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" || echo "❌ Request failed"

echo ""
echo "🏁 FINAL TEST COMPLETED!"
echo "========================"
echo ""
echo "If you see valid JSON responses above with 'response' fields,"
echo "then the AI Search System is now fully operational! 🎉"
echo ""
echo "If you still see errors, check the FastAPI logs:"
echo "  supervisorctl tail -f ai-search-app"
