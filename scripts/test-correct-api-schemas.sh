#!/bin/bash

echo "🎯 TESTING WITH CORRECT API SCHEMAS"
echo "=================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🔍 Testing endpoints with correct field names based on schema validation..."

log "🧪 Testing chat endpoint with 'message' field (not 'query'):"
CHAT_RESULT=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you today?", "session_id": "test-session"}' \
  --connect-timeout 15 --max-time 45)

HTTP_CODE="${CHAT_RESULT: -3}"
RESPONSE_BODY="${CHAT_RESULT%???}"

log "📊 Chat endpoint results:"
log "   HTTP Code: $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    log "✅ Chat endpoint: SUCCESS!"
    log "   Response: $RESPONSE_BODY" | head -c 200
    echo "..."
else
    log "❌ Chat endpoint failed"
    log "   Full Response: $RESPONSE_BODY"
fi

log "🧪 Testing research endpoint with 'research_question' field:"
RESEARCH_RESULT=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/v1/research/deep-dive \
  -H "Content-Type: application/json" \
  -d '{"research_question": "What are the latest developments in AI technology?", "depth": "basic"}' \
  --connect-timeout 15 --max-time 45)

RESEARCH_HTTP_CODE="${RESEARCH_RESULT: -3}"
RESEARCH_RESPONSE_BODY="${RESEARCH_RESULT%???}"

log "📊 Research endpoint results:"
log "   HTTP Code: $RESEARCH_HTTP_CODE"
if [ "$RESEARCH_HTTP_CODE" = "200" ]; then
    log "✅ Research endpoint: SUCCESS!"
    log "   Response: $RESEARCH_RESPONSE_BODY" | head -c 200
    echo "..."
else
    log "❌ Research endpoint failed"
    log "   Full Response: $RESEARCH_RESPONSE_BODY"
fi

log "🧪 Testing search endpoint (already working):"
SEARCH_RESULT=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/v1/search/basic \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence trends 2025", "max_results": 3}' \
  --connect-timeout 15 --max-time 45)

SEARCH_HTTP_CODE="${SEARCH_RESULT: -3}"
SEARCH_RESPONSE_BODY="${SEARCH_RESULT%???}"

log "📊 Search endpoint results:"
log "   HTTP Code: $SEARCH_HTTP_CODE"
if [ "$SEARCH_HTTP_CODE" = "200" ]; then
    log "✅ Search endpoint: SUCCESS!"
    log "   Response: $SEARCH_RESPONSE_BODY" | head -c 200
    echo "..."
else
    log "❌ Search endpoint failed"
    log "   Full Response: $SEARCH_RESPONSE_BODY"
fi

log "🧪 Testing chat streaming endpoint:"
STREAM_RESULT=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me a short joke", "session_id": "test-stream", "stream": true}' \
  --connect-timeout 15 --max-time 45)

STREAM_HTTP_CODE="${STREAM_RESULT: -3}"
STREAM_RESPONSE_BODY="${STREAM_RESULT%???}"

log "📊 Chat streaming endpoint results:"
log "   HTTP Code: $STREAM_HTTP_CODE"
if [ "$STREAM_HTTP_CODE" = "200" ]; then
    log "✅ Chat streaming: SUCCESS!"
    log "   Response: $STREAM_RESPONSE_BODY" | head -c 200
    echo "..."
else
    log "❌ Chat streaming failed"
    log "   Response: $STREAM_RESPONSE_BODY"
fi

log "🧪 Testing advanced search:"
ADV_SEARCH_RESULT=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/v1/search/advanced \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning applications", "max_results": 5, "search_type": "comprehensive"}' \
  --connect-timeout 15 --max-time 45)

ADV_SEARCH_HTTP_CODE="${ADV_SEARCH_RESULT: -3}"
ADV_SEARCH_RESPONSE_BODY="${ADV_SEARCH_RESULT%???}"

log "📊 Advanced search results:"
log "   HTTP Code: $ADV_SEARCH_HTTP_CODE"
if [ "$ADV_SEARCH_HTTP_CODE" = "200" ]; then
    log "✅ Advanced search: SUCCESS!"
    log "   Response: $ADV_SEARCH_RESPONSE_BODY" | head -c 200
    echo "..."
else
    log "❌ Advanced search failed"
    log "   Response: $ADV_SEARCH_RESPONSE_BODY"
fi

log "🎉 COMPREHENSIVE TEST SUMMARY:"
log "================================"

if [ "$HTTP_CODE" = "200" ]; then
    log "✅ Chat Complete: WORKING"
else
    log "❌ Chat Complete: FAILED (HTTP $HTTP_CODE)"
fi

if [ "$RESEARCH_HTTP_CODE" = "200" ]; then
    log "✅ Research Deep Dive: WORKING"
else
    log "❌ Research Deep Dive: FAILED (HTTP $RESEARCH_HTTP_CODE)"
fi

if [ "$SEARCH_HTTP_CODE" = "200" ]; then
    log "✅ Basic Search: WORKING"
else
    log "❌ Basic Search: FAILED (HTTP $SEARCH_HTTP_CODE)"
fi

if [ "$STREAM_HTTP_CODE" = "200" ]; then
    log "✅ Chat Streaming: WORKING"
else
    log "❌ Chat Streaming: FAILED (HTTP $STREAM_HTTP_CODE)"
fi

if [ "$ADV_SEARCH_HTTP_CODE" = "200" ]; then
    log "✅ Advanced Search: WORKING"
else
    log "❌ Advanced Search: FAILED (HTTP $ADV_SEARCH_HTTP_CODE)"
fi

log ""
log "🚀 WORKING EXAMPLE COMMANDS:"
log "============================"
log ""
log "💬 Chat:"
log 'curl -X POST http://localhost:8000/api/v1/chat/complete \'
log '  -H "Content-Type: application/json" \'
log '  -d '"'"'{"message": "Hello, how are you?", "session_id": "my-session"}'"'"
log ""
log "🔍 Search:"
log 'curl -X POST http://localhost:8000/api/v1/search/basic \'
log '  -H "Content-Type: application/json" \'
log '  -d '"'"'{"query": "AI trends", "max_results": 5}'"'"
log ""
log "📚 Research:"
log 'curl -X POST http://localhost:8000/api/v1/research/deep-dive \'
log '  -H "Content-Type: application/json" \'
log '  -d '"'"'{"research_question": "What is machine learning?", "depth": "basic"}'"'"
log ""
log "🌊 Streaming Chat:"
log 'curl -X POST http://localhost:8000/api/v1/chat/stream \'
log '  -H "Content-Type: application/json" \'
log '  -d '"'"'{"message": "Tell me about AI", "session_id": "stream-test", "stream": true}'"'"

EOF
