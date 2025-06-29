#!/bin/bash

echo "🔍 FINAL COMPREHENSIVE DIAGNOSIS & FIX"
echo "======================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🎯 The method names are correct - let's verify everything works end-to-end"

log "📊 Step 1: Check all services status"
supervisorctl status

log "🔍 Step 2: Verify Ollama is running and has models"
curl -s http://localhost:11434/api/tags | jq '.'

log "🧪 Step 3: Test direct Ollama API call"
curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini",
    "prompt": "Say exactly: Direct Ollama test successful",
    "stream": false
  }' | jq '.'

log "🐍 Step 4: Test Python OllamaClient directly"
cat > /tmp/test_ollama_client.py << 'PYTHON_EOF'
import asyncio
import sys
sys.path.insert(0, '/app')

async def test_ollama_client():
    try:
        from app.models.ollama_client import OllamaClient
        
        print("🔧 Creating OllamaClient...")
        client = OllamaClient(base_url="http://localhost:11434")
        
        print("🔧 Initializing client...")
        await client.initialize()
        
        print("🔧 Health check...")
        health = await client.health_check()
        print(f"   Health: {health}")
        
        if health:
            print("🔧 Listing models...")
            models = await client.list_models()
            print(f"   Models: {[m['name'] for m in models]}")
            
            if models:
                model_name = models[0]['name']
                print(f"🔧 Testing generate() with {model_name}...")
                result = await client.generate(
                    model_name=model_name,
                    prompt="Say exactly: OllamaClient test successful",
                    max_tokens=20
                )
                print(f"   Success: {result.success}")
                print(f"   Text: {result.text}")
                print(f"   Error: {result.error}")
                
                if result.success:
                    print("✅ OllamaClient.generate() works correctly!")
                    return True
                else:
                    print("❌ OllamaClient.generate() failed")
                    return False
            else:
                print("❌ No models available")
                return False
        else:
            print("❌ Ollama health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_ollama_client())
    sys.exit(0 if result else 1)
PYTHON_EOF

cd /app && python3 /tmp/test_ollama_client.py
OLLAMA_CLIENT_RESULT=$?

log "🎛️ Step 5: Test ModelManager"
cat > /tmp/test_model_manager.py << 'PYTHON_EOF'
import asyncio
import sys
sys.path.insert(0, '/app')

async def test_model_manager():
    try:
        from app.models.manager import ModelManager
        
        print("🔧 Creating ModelManager...")
        manager = ModelManager()
        
        print("🔧 Initializing ModelManager...")
        await manager.initialize()
        
        print("🔧 Getting available models...")
        stats = manager.get_model_stats()
        print(f"   Model stats: {stats}")
        
        if stats.get('total_models', 0) > 0:
            # Get first available model
            models = list(manager.models.keys())
            model_name = models[0]
            print(f"🔧 Testing generate() with {model_name}...")
            
            result = await manager.generate(
                model_name=model_name,
                prompt="Say exactly: ModelManager test successful",
                max_tokens=20
            )
            print(f"   Success: {result.success}")
            print(f"   Text: {result.text}")
            print(f"   Error: {result.error}")
            
            if result.success:
                print("✅ ModelManager.generate() works correctly!")
                return True
            else:
                print("❌ ModelManager.generate() failed")
                return False
        else:
            print("❌ No models available in ModelManager")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_model_manager())
    sys.exit(0 if result else 1)
PYTHON_EOF

cd /app && python3 /tmp/test_model_manager.py
MODEL_MANAGER_RESULT=$?

log "🌐 Step 6: Test FastAPI endpoint directly"
curl -s -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Say exactly: FastAPI chat endpoint test successful",
    "max_tokens": 20
  }' | jq '.'

log "🚀 Step 7: Test through frontend/JavaScript simulation"
cat > /tmp/test_frontend.js << 'JS_EOF'
const fetch = require('node-fetch');

async function testChatAPI() {
    try {
        console.log('🔧 Testing chat API from frontend perspective...');
        
        const response = await fetch('http://localhost:8000/api/v1/chat/complete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                message: "Say exactly: Frontend chat test successful",
                max_tokens: 20
            })
        });
        
        const result = await response.json();
        console.log('   Response status:', response.status);
        console.log('   Response body:', JSON.stringify(result, null, 2));
        
        if (response.ok && result.success && result.response) {
            console.log('✅ Frontend chat API test successful!');
            return true;
        } else {
            console.log('❌ Frontend chat API test failed');
            return false;
        }
        
    } catch (error) {
        console.log('❌ Error:', error.message);
        return false;
    }
}

testChatAPI().then(success => {
    process.exit(success ? 0 : 1);
});
JS_EOF

# Install node-fetch if needed and run test
cd /app && npm list node-fetch >/dev/null 2>&1 || npm install node-fetch >/dev/null 2>&1
cd /app && node /tmp/test_frontend.js
FRONTEND_RESULT=$?

log "📊 FINAL RESULTS SUMMARY"
log "========================"
log "Ollama Client Test: $([ $OLLAMA_CLIENT_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
log "Model Manager Test: $([ $MODEL_MANAGER_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
log "Frontend API Test: $([ $FRONTEND_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"

if [ $OLLAMA_CLIENT_RESULT -eq 0 ] && [ $MODEL_MANAGER_RESULT -eq 0 ] && [ $FRONTEND_RESULT -eq 0 ]; then
    log "🎉 ALL TESTS PASSED! The chat system is working correctly!"
    log "🎯 The 'Model returned an empty or invalid response' error should be resolved."
    
    log "🔧 Final service restart to ensure clean state..."
    supervisorctl restart fastapi
    sleep 3
    
    log "✅ SYSTEM READY FOR USE!"
    log "📱 You can now test the chat functionality from the frontend."
    
else
    log "⚠️  Some tests failed. Let's diagnose further..."
    
    if [ $OLLAMA_CLIENT_RESULT -ne 0 ]; then
        log "🔍 OllamaClient failed - checking Ollama service..."
        curl -s http://localhost:11434/api/tags
    fi
    
    if [ $MODEL_MANAGER_RESULT -ne 0 ]; then
        log "🔍 ModelManager failed - checking initialization..."
        cat /app/logs/app.log | tail -20
    fi
    
    if [ $FRONTEND_RESULT -ne 0 ]; then
        log "🔍 Frontend API failed - checking FastAPI logs..."
        supervisorctl tail fastapi
    fi
fi

log "🏁 Comprehensive diagnosis complete."
