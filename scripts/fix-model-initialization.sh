#!/bin/bash

echo "🔧 COMPREHENSIVE MODEL INITIALIZATION FIX"
echo "=========================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🎯 Now we have the REAL issue: Model initialization problems"
log "The API endpoints are correct, but the backend models aren't working"

log "🔍 Step 1: Check Ollama status and models"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log "✅ Ollama is responding"
    log "📋 Available models:"
    curl -s http://localhost:11434/api/tags | jq '.models[].name' 2>/dev/null || curl -s http://localhost:11434/api/tags
else
    log "❌ Ollama is not responding"
    log "🔧 Attempting to restart Ollama..."
    supervisorctl restart ollama
    sleep 15
fi

log "🔍 Step 2: Test direct Ollama model interaction"
log "🧪 Testing phi3:mini model directly:"
OLLAMA_TEST=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "phi3:mini", "prompt": "Hello, respond with just: Working", "stream": false}' \
  --connect-timeout 10 --max-time 30)

if echo "$OLLAMA_TEST" | grep -q "Working\|response"; then
    log "✅ Ollama phi3:mini model is working directly"
    log "📋 Response: $OLLAMA_TEST"
else
    log "❌ Ollama phi3:mini model failed"
    log "📋 Response: $OLLAMA_TEST"
    
    log "🔧 Trying to pull phi3:mini model..."
    curl -X POST http://localhost:11434/api/pull \
      -H "Content-Type: application/json" \
      -d '{"name": "phi3:mini"}' &
    
    PULL_PID=$!
    sleep 30
    kill $PULL_PID 2>/dev/null
    
    log "🧪 Testing again after pull attempt..."
    OLLAMA_TEST2=$(curl -s -X POST http://localhost:11434/api/generate \
      -H "Content-Type: application/json" \
      -d '{"model": "phi3:mini", "prompt": "Hello", "stream": false}' \
      --connect-timeout 10 --max-time 30)
    log "📋 Second test result: $OLLAMA_TEST2"
fi

log "🔍 Step 3: Check FastAPI model manager initialization"
log "📊 Current FastAPI logs (last 30 lines):"
tail -30 /workspace/logs/app.out.log 2>/dev/null || log "No app logs found"

log "📊 FastAPI error logs:"
tail -20 /workspace/logs/app.err.log 2>/dev/null || log "No error logs found"

log "🔍 Step 4: Force model manager initialization"
log "🔧 Creating model manager test script..."

cat > /tmp/test_model_manager.py << 'PYTHON_EOF'
import sys
import asyncio
import logging
sys.path.insert(0, '/app')

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_model_manager():
    try:
        print("🧪 Testing ModelManager initialization...")
        
        # Test basic imports
        print("📦 Testing imports...")
        from app.models.manager import ModelManager
        from app.models.ollama_client import OllamaClient
        print("✅ Imports successful")
        
        # Test OllamaClient directly
        print("🤖 Testing OllamaClient...")
        ollama_client = OllamaClient()
        health = await ollama_client.health_check()
        print(f"🏥 Ollama health: {health}")
        
        if health:
            models = await ollama_client.list_models()
            print(f"📋 Available models: {models}")
            
            if models:
                # Test generation with first available model
                test_model = models[0]
                print(f"🧪 Testing generation with {test_model}...")
                
                result = await ollama_client.generate_text(
                    model_name=test_model,
                    prompt="Say 'Hello from model test'",
                    max_tokens=10
                )
                print(f"🎯 Direct generation result: {result}")
            else:
                print("❌ No models available")
        
        # Test ModelManager
        print("🎛️ Testing ModelManager...")
        model_manager = ModelManager()
        await model_manager.initialize()
        print("✅ ModelManager initialized")
        
        available_models = await model_manager.get_available_models()
        print(f"📋 ModelManager available models: {available_models}")
        
        if available_models:
            # Test generation through ModelManager
            test_prompt = "Respond with: ModelManager is working"
            print(f"🧪 Testing ModelManager generation...")
            
            response = await model_manager.generate_response(
                prompt=test_prompt,
                model_name=available_models[0] if available_models else "phi3:mini"
            )
            print(f"🎯 ModelManager generation result: {response}")
        else:
            print("❌ No models available through ModelManager")
            
    except Exception as e:
        print(f"❌ Error in model manager test: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_model_manager())
PYTHON_EOF

log "🧪 Running model manager test..."
cd /app && python3 /tmp/test_model_manager.py

log "🔍 Step 5: Fix FastAPI model initialization"
log "🔧 Creating FastAPI initialization fix..."

cat > /tmp/fix_fastapi_models.py << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/app')

# Read the current main.py
try:
    with open('/app/main.py', 'r') as f:
        content = f.read()
    
    print("✅ Read main.py successfully")
    
    # Create a comprehensive lifespan function that properly initializes models
    new_lifespan = '''
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with robust model initialization"""
    logger.info("🚀 FastAPI starting with comprehensive model initialization...")
    
    # Initialize components with extensive error handling
    model_manager = None
    chat_graph = None
    search_graph = None
    redis_client = None
    
    try:
        # 1. Redis initialization (optional)
        logger.info("📡 Initializing Redis...")
        try:
            redis_client = get_redis_client()
            if redis_client:
                await redis_client.ping()
                logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            redis_client = None
        
        # 2. Model Manager initialization (critical)
        logger.info("🤖 Initializing ModelManager...")
        try:
            from app.models.manager import ModelManager
            model_manager = ModelManager()
            
            # Force initialization with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 ModelManager init attempt {attempt + 1}/{max_retries}")
                    await model_manager.initialize()
                    
                    # Verify models are available
                    models = await model_manager.get_available_models()
                    if models:
                        logger.info(f"✅ ModelManager ready with models: {models}")
                        break
                    else:
                        logger.warning(f"⚠️ No models available on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"❌ ModelManager init attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                    else:
                        raise
                        
        except Exception as e:
            logger.error(f"❌ Critical: ModelManager initialization failed: {e}")
            # Continue without model manager - will cause chat to fail gracefully
            model_manager = None
        
        # 3. Chat Graph initialization
        logger.info("💬 Initializing ChatGraph...")
        try:
            if model_manager:
                from app.graphs.chat_graph import ChatGraph
                chat_graph = ChatGraph(model_manager)
                
                # Test the chat graph
                logger.info("🧪 Testing ChatGraph...")
                from app.graphs.base import GraphState
                test_state = GraphState(
                    query="test",
                    query_id="startup-test",
                    conversation_id="startup-conv"
                )
                
                # Quick test execution
                test_result = await asyncio.wait_for(
                    chat_graph.execute(test_state),
                    timeout=10.0
                )
                logger.info("✅ ChatGraph test completed successfully")
            else:
                logger.warning("⚠️ Skipping ChatGraph - no ModelManager")
                
        except Exception as e:
            logger.error(f"❌ ChatGraph initialization failed: {e}")
            chat_graph = None
        
        # 4. Search Graph initialization
        logger.info("🔍 Initializing SearchGraph...")
        try:
            if model_manager:
                from app.graphs.search_graph import SearchGraph
                search_graph = SearchGraph(model_manager)
                logger.info("✅ SearchGraph initialized")
            else:
                logger.warning("⚠️ Skipping SearchGraph - no ModelManager")
                
        except Exception as e:
            logger.error(f"❌ SearchGraph initialization failed: {e}")
            search_graph = None
        
        # 5. Store in app state
        app.state.model_manager = model_manager
        app.state.chat_graph = chat_graph
        app.state.search_graph = search_graph
        app.state.redis_client = redis_client
        
        # 6. Final status report
        status = {
            "redis": "connected" if redis_client else "disconnected",
            "model_manager": "ready" if model_manager else "failed",
            "chat_graph": "ready" if chat_graph else "failed",
            "search_graph": "ready" if search_graph else "failed"
        }
        logger.info(f"🎉 Startup complete: {status}")
        
        # If model_manager failed, log specific guidance
        if not model_manager:
            logger.error("🚨 CRITICAL: ModelManager failed to initialize!")
            logger.error("🔧 This will cause chat endpoints to return empty responses")
            logger.error("🔧 Check Ollama connectivity and model availability")
        
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        # Continue anyway to allow debugging
        
    yield
    
    # Cleanup
    logger.info("🧹 Cleaning up...")
    if redis_client:
        try:
            await redis_client.close()
        except:
            pass
'''

    # Find and replace the lifespan function
    import re
    
    # Pattern to match the entire lifespan function
    lifespan_pattern = r'@asynccontextmanager\s*\nasync def lifespan\(app: FastAPI\):.*?yield.*?(?=\n@|\ndef |\nclass |\nif __name__|\napp\.|\Z)'
    
    if re.search(lifespan_pattern, content, re.DOTALL):
        content = re.sub(lifespan_pattern, new_lifespan.strip(), content, flags=re.DOTALL)
        print("✅ Replaced existing lifespan function")
    else:
        # If no lifespan function found, add it before app creation
        app_pattern = r'(app = FastAPI\(.*?\))'
        if re.search(app_pattern, content, re.DOTALL):
            content = re.sub(app_pattern, new_lifespan.strip() + '\n\n\\1', content, flags=re.DOTALL)
            print("✅ Added lifespan function before app creation")
        else:
            print("⚠️ Could not find where to insert lifespan function")
    
    # Ensure asyncio import is present
    if 'import asyncio' not in content:
        content = 'import asyncio\n' + content
    
    # Write the updated content
    with open('/app/main.py', 'w') as f:
        f.write(content)
    
    print("✅ FastAPI main.py updated with robust model initialization")
    
except Exception as e:
    print(f"❌ Error updating FastAPI: {e}")
    import traceback
    print(f"📋 Traceback: {traceback.format_exc()}")
PYTHON_EOF

log "🔧 Applying FastAPI model initialization fix..."
cd /app && python3 /tmp/fix_fastapi_models.py

log "🔄 Step 6: Restart FastAPI with new initialization"
supervisorctl stop ai-search-app
sleep 3
supervisorctl start ai-search-app
sleep 20

log "🧪 Step 7: Test the chat endpoint again"
FINAL_CHAT_TEST=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, this is a final test", "session_id": "final-test"}' \
  --connect-timeout 15 --max-time 45)

FINAL_HTTP_CODE="${FINAL_CHAT_TEST: -3}"
FINAL_RESPONSE_BODY="${FINAL_CHAT_TEST%???}"

log "📊 Final chat test results:"
log "   HTTP Code: $FINAL_HTTP_CODE"
log "   Response: $FINAL_RESPONSE_BODY"

if [ "$FINAL_HTTP_CODE" = "200" ] && echo "$FINAL_RESPONSE_BODY" | grep -q '"response"'; then
    log "🎉 SUCCESS! Chat endpoint is now working!"
    # Extract the actual response
    ACTUAL_RESPONSE=$(echo "$FINAL_RESPONSE_BODY" | grep -o '"response":"[^"]*"' | sed 's/"response":"//;s/"$//')
    log "💬 AI Response: $ACTUAL_RESPONSE"
else
    log "❌ Chat endpoint still failing"
    log "📊 Checking startup logs..."
    tail -50 /workspace/logs/app.out.log
fi

log "🎯 COMPREHENSIVE FIX COMPLETE!"
log "If still failing, the issue is likely:"
log "1. Ollama models not properly loaded"
log "2. ModelManager-Ollama connection issues"
log "3. Graph execution timeout/error"

EOF
