#!/bin/bash

echo "🔧 QUICK FIX FOR METHOD NAME ISSUE"
echo "=================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🎯 I can see the issue! The OllamaClient method is wrong"
log "Let's check the actual method names and test the chat endpoint"

log "🔍 Step 1: Check OllamaClient methods"
cat > /tmp/check_ollama_methods.py << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/app')

try:
    from app.models.ollama_client import OllamaClient
    
    print("📋 OllamaClient methods:")
    client = OllamaClient()
    methods = [method for method in dir(client) if not method.startswith('_') and callable(getattr(client, method))]
    for method in methods:
        print(f"  - {method}")
    
    print("\n🔍 Looking for generation methods:")
    generation_methods = [method for method in methods if 'generate' in method.lower()]
    for method in generation_methods:
        print(f"  ✅ {method}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    print(traceback.format_exc())
PYTHON_EOF

log "🧪 Running method check..."
cd /app && python3 /tmp/check_ollama_methods.py

log "🔍 Step 2: Test the correct generation method"
cat > /tmp/test_correct_generation.py << 'PYTHON_EOF'
import sys
import asyncio
sys.path.insert(0, '/app')

async def test_generation():
    try:
        from app.models.ollama_client import OllamaClient
        
        client = OllamaClient()
        
        # Test health first
        health = await client.health_check()
        print(f"🏥 Health: {health}")
        
        if health:
            # List models
            models = await client.list_models()
            print(f"📋 Models: {[m['name'] for m in models] if models else 'No models'}")
            
            if models:
                model_name = "phi3:mini"
                print(f"🧪 Testing generation with {model_name}...")
                
                # Try different method names that might exist
                test_methods = [
                    'generate',
                    'generate_response', 
                    'generate_text',
                    'generate_completion'
                ]
                
                for method_name in test_methods:
                    if hasattr(client, method_name):
                        print(f"  ✅ Found method: {method_name}")
                        try:
                            method = getattr(client, method_name)
                            if method_name == 'generate':
                                result = await method(
                                    model_name=model_name,
                                    prompt="Say hello",
                                    max_tokens=10
                                )
                            else:
                                result = await method(
                                    prompt="Say hello",
                                    model_name=model_name
                                )
                            print(f"  🎯 Result: {result}")
                            break
                        except Exception as e:
                            print(f"  ❌ Method {method_name} failed: {e}")
                    else:
                        print(f"  ❌ Method {method_name} not found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())

asyncio.run(test_generation())
PYTHON_EOF

log "🧪 Testing correct generation method..."
cd /app && python3 /tmp/test_correct_generation.py

log "🔍 Step 3: Wait for FastAPI to restart and test chat endpoint"
log "⏳ Waiting for FastAPI to fully restart..."
sleep 10

# Check if FastAPI restarted successfully
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log "✅ FastAPI is responding"
    
    log "🧪 Testing chat endpoint after restart..."
    CHAT_TEST=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/complete \
      -H "Content-Type: application/json" \
      -d '{"message": "Hello, are you working now?", "session_id": "restart-test"}' \
      --connect-timeout 15 --max-time 60)
    
    HTTP_CODE="${CHAT_TEST: -3}"
    RESPONSE_BODY="${CHAT_TEST%???}"
    
    log "📊 Chat test after restart:"
    log "   HTTP Code: $HTTP_CODE"
    log "   Response: $RESPONSE_BODY"
    
    if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | grep -q '"response"'; then
        log "🎉 SUCCESS! Chat endpoint is now working!"
        # Extract the AI response
        AI_RESPONSE=$(echo "$RESPONSE_BODY" | grep -o '"response":"[^"]*"' | sed 's/"response":"//;s/"$//')
        log "🤖 AI says: $AI_RESPONSE"
    else
        log "❌ Still having issues. Let's check the latest logs..."
        log "📊 Latest FastAPI logs:"
        tail -20 /workspace/logs/app.out.log
    fi
else
    log "❌ FastAPI is not responding. Let's restart it manually..."
    supervisorctl restart ai-search-app
    sleep 15
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ FastAPI is now responding after manual restart"
    else
        log "❌ FastAPI still not responding. Check logs:"
        tail -20 /workspace/logs/app.err.log
    fi
fi

log "🔍 Step 4: Final system status"
STATUS=$(curl -s http://localhost:8000/system/status 2>/dev/null)
if [ $? -eq 0 ]; then
    log "📊 System Status:"
    echo "$STATUS" | jq '.' 2>/dev/null || echo "$STATUS"
else
    log "❌ System status not available"
fi

log "🎯 ANALYSIS COMPLETE!"
log "The models are working, so if chat is still failing, it's likely:"
log "1. Method name mismatch in OllamaClient"
log "2. ChatGraph not properly using the models" 
log "3. Response extraction issues in the graph"

EOF
