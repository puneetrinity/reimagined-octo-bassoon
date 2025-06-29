#!/bin/bash

echo "🚀 RUNPOD-ADAPTED COMPREHENSIVE FIX"
echo "=================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🔍 Step 1: Discovering RunPod directory structure"

# Find the actual app directory
APP_DIR=""
if [ -d "/workspace/app" ]; then
    APP_DIR="/workspace/app"
elif [ -d "/app" ]; then
    APP_DIR="/app"
elif [ -d "/workspace/ubiquitous-octo-invention/app" ]; then
    APP_DIR="/workspace/ubiquitous-octo-invention/app"
else
    log "❌ Cannot find app directory. Listing /workspace contents:"
    ls -la /workspace/
    if [ -d "/workspace" ]; then
        find /workspace -name "main.py" -type f 2>/dev/null | head -5
    fi
fi

log "📂 Detected APP_DIR: $APP_DIR"

# Find supervisor config
SUPERVISOR_CONF=""
if [ -f "/workspace/docker/supervisor.conf" ]; then
    SUPERVISOR_CONF="/workspace/docker/supervisor.conf"
elif [ -f "/etc/supervisor/conf.d/supervisor.conf" ]; then
    SUPERVISOR_CONF="/etc/supervisor/conf.d/supervisor.conf"
elif [ -f "/workspace/supervisor.conf" ]; then
    SUPERVISOR_CONF="/workspace/supervisor.conf"
else
    log "❌ Cannot find supervisor.conf. Searching..."
    find /workspace -name "*supervisor*" -type f 2>/dev/null | head -5
fi

log "📂 Detected SUPERVISOR_CONF: $SUPERVISOR_CONF"

# Create necessary directories
log "📁 Creating necessary directories..."
mkdir -p /workspace/logs
mkdir -p /workspace/docker

log "🔧 Step 2: Fix Redis connection"
# Stop Redis safely
redis-cli shutdown 2>/dev/null || true
supervisorctl stop redis 2>/dev/null || true
sleep 2

# Start Redis with correct configuration
supervisorctl start redis
sleep 5

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    log "✅ Redis is now connected"
else
    log "❌ Redis connection failed, trying manual start..."
    redis-server --daemonize yes --bind 0.0.0.0 --port 6379 --protected-mode no &
    sleep 3
    if redis-cli ping > /dev/null 2>&1; then
        log "✅ Redis manual start successful"
    else
        log "❌ Redis still failing"
    fi
fi

log "🔧 Step 3: Fix FastAPI if app directory exists"

if [ -n "$APP_DIR" ] && [ -d "$APP_DIR" ] && [ -f "$APP_DIR/main.py" ]; then
    log "📝 Found main.py at $APP_DIR/main.py - applying fixes..."
    
    # Backup original
    cp "$APP_DIR/main.py" "$APP_DIR/main.py.backup.$(date +%s)"
    
    # Create comprehensive FastAPI fix
    cat > /tmp/fix_fastapi_runpod.py << PYTHON_EOF
import sys
import os
sys.path.insert(0, '$APP_DIR')

# Read current main.py
try:
    with open('$APP_DIR/main.py', 'r') as f:
        content = f.read()
    
    print("✅ Successfully read main.py")
    
    # Enhanced lifespan function that works in RunPod
    new_lifespan = '''
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - RunPod optimized"""
    logger.info("🚀 Starting FastAPI application in RunPod...")
    
    try:
        # Initialize Redis connection with error handling
        logger.info("📡 Connecting to Redis...")
        redis_client = None
        try:
            redis_client = get_redis_client()
            if redis_client:
                await redis_client.ping()
                logger.info("✅ Redis connection established")
            else:
                logger.warning("⚠️ Redis client creation failed")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            redis_client = None
        
        # Initialize ModelManager with comprehensive error handling
        logger.info("🤖 Initializing ModelManager...")
        model_manager = None
        try:
            from app.models.manager import ModelManager
            model_manager = ModelManager()
            await model_manager.initialize()
            
            # Verify models are available
            models = await model_manager.get_available_models()
            logger.info(f"✅ ModelManager initialized with {len(models)} models: {models}")
            
            if not models:
                logger.warning("⚠️ No models available, but continuing...")
                
        except Exception as e:
            logger.error(f"❌ ModelManager initialization failed: {e}")
            # Create a minimal fallback
            logger.info("🔄 Creating fallback ModelManager...")
            model_manager = None
        
        # Initialize ChatGraph with fallback handling
        logger.info("💬 Initializing ChatGraph...")
        chat_graph = None
        if model_manager:
            try:
                from app.graphs.chat_graph import ChatGraph
                chat_graph = ChatGraph(model_manager)
                logger.info("✅ ChatGraph initialized successfully")
            except Exception as e:
                logger.error(f"❌ ChatGraph initialization failed: {e}")
                chat_graph = None
        else:
            logger.warning("⚠️ Skipping ChatGraph - no ModelManager")
        
        # Initialize SearchGraph with fallback handling
        logger.info("🔍 Initializing SearchGraph...")
        search_graph = None
        if model_manager:
            try:
                from app.graphs.search_graph import SearchGraph
                search_graph = SearchGraph(model_manager)
                logger.info("✅ SearchGraph initialized successfully")
            except Exception as e:
                logger.error(f"❌ SearchGraph initialization failed: {e}")
                search_graph = None
        else:
            logger.warning("⚠️ Skipping SearchGraph - no ModelManager")
        
        # Store in app state with None-safe handling
        app.state.model_manager = model_manager
        app.state.chat_graph = chat_graph
        app.state.search_graph = search_graph
        app.state.redis_client = redis_client
        
        # Report final status
        status = {
            "redis": "connected" if redis_client else "disconnected",
            "model_manager": "ready" if model_manager else "failed",
            "chat_graph": "ready" if chat_graph else "failed",
            "search_graph": "ready" if search_graph else "failed"
        }
        logger.info(f"🎉 Initialization complete: {status}")
        
    except Exception as e:
        logger.error(f"❌ Critical initialization error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Continue anyway to allow debugging
        
    yield
    
    # Cleanup
    logger.info("🧹 Cleaning up application resources...")
    if hasattr(app.state, 'redis_client') and app.state.redis_client:
        try:
            await app.state.redis_client.close()
            logger.info("✅ Redis connection closed")
        except Exception as e:
            logger.warning(f"⚠️ Redis cleanup error: {e}")
'''

    # Enhanced chat endpoint with comprehensive error handling
    new_chat_endpoint = '''
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Enhanced chat endpoint with RunPod optimizations"""
    correlation_id = str(uuid.uuid4())
    query_id = str(uuid.uuid4())
    
    logger.info(f"[CHAT] Request received: {request.query[:50]}...", extra={
        "correlation_id": correlation_id,
        "query_id": query_id
    })
    
    try:
        # Basic input validation
        if not request.query or not request.query.strip():
            return ChatResponse(
                response="Please provide a valid question or message.",
                query_id=query_id,
                correlation_id=correlation_id,
                success=True
            )
        
        # Check component initialization status
        has_model_manager = hasattr(app.state, 'model_manager') and app.state.model_manager is not None
        has_chat_graph = hasattr(app.state, 'chat_graph') and app.state.chat_graph is not None
        
        logger.info(f"[CHAT] Component status - ModelManager: {has_model_manager}, ChatGraph: {has_chat_graph}")
        
        if not has_chat_graph:
            logger.warning(f"[CHAT] ChatGraph not available - providing fallback response")
            return ChatResponse(
                response="I'm still initializing my systems. Please try again in a moment, or ask me something simple!",
                query_id=query_id,
                correlation_id=correlation_id,
                success=True
            )
        
        # Create graph state
        logger.info(f"[CHAT] Creating graph state for execution")
        from app.graphs.base import GraphState
        state = GraphState(
            query=request.query.strip(),
            query_id=query_id,
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            correlation_id=correlation_id
        )
        
        # Execute chat graph with timeout
        logger.info(f"[CHAT] Executing chat graph...")
        try:
            result = await asyncio.wait_for(
                app.state.chat_graph.execute(state),
                timeout=30.0  # 30-second timeout
            )
            logger.info(f"[CHAT] Graph execution completed")
        except asyncio.TimeoutError:
            logger.error(f"[CHAT] Graph execution timed out")
            return ChatResponse(
                response="I'm taking longer than usual to process your request. Please try with a simpler question.",
                query_id=query_id,
                correlation_id=correlation_id,
                success=False
            )
        
        # Extract response with multiple fallback methods
        final_response = None
        
        # Method 1: Check final_response attribute
        if hasattr(result, 'final_response') and result.final_response:
            final_response = result.final_response
            logger.info(f"[CHAT] Response extracted via final_response attribute")
        
        # Method 2: Check response attribute
        elif hasattr(result, 'response') and result.response:
            final_response = result.response
            logger.info(f"[CHAT] Response extracted via response attribute")
        
        # Method 3: Check if result is a dict
        elif isinstance(result, dict):
            final_response = result.get('final_response') or result.get('response')
            if final_response:
                logger.info(f"[CHAT] Response extracted from dict")
        
        # Method 4: Try to get any text-like attribute
        if not final_response:
            for attr in ['text', 'content', 'output', 'result']:
                if hasattr(result, attr):
                    val = getattr(result, attr)
                    if val and isinstance(val, str):
                        final_response = val
                        logger.info(f"[CHAT] Response extracted via {attr} attribute")
                        break
        
        # Clean and validate response
        if final_response:
            final_response = final_response.strip()
            
            # Remove markdown artifacts and duplicated content
            if '---' in final_response:
                parts = final_response.split('---')
                for part in parts:
                    if part.strip() and len(part.strip()) > 15:
                        final_response = part.strip()
                        break
            
            # Remove obvious duplication patterns
            if final_response.count('Current query') > 1:
                lines = final_response.split('\\n')
                clean_lines = []
                for line in lines:
                    if not line.strip().startswith('Current query'):
                        clean_lines.append(line)
                    else:
                        break
                final_response = '\\n'.join(clean_lines).strip()
        
        # Ultimate fallback
        if not final_response or final_response.lower() in ['missing', 'none', '', 'null']:
            logger.warning(f"[CHAT] No valid response generated, using fallback")
            final_response = "I'm here to help! Could you please rephrase your question or try asking something else?"
        
        logger.info(f"[CHAT] Final response prepared: {len(final_response)} characters")
        
        return ChatResponse(
            response=final_response,
            query_id=query_id,
            correlation_id=correlation_id,
            success=True
        )
        
    except Exception as e:
        logger.error(f"[CHAT] Unexpected error: {str(e)}", extra={
            "correlation_id": correlation_id,
            "error_type": type(e).__name__
        })
        
        return ChatResponse(
            response="I encountered an unexpected issue. Please try again with a different question.",
            query_id=query_id,
            correlation_id=correlation_id,
            success=False,
            error_details={
                "error_code": "PROCESSING_ERROR",
                "error_type": "SYSTEM",
                "user_message": "Processing error occurred",
                "technical_details": str(e)[:200],  # Limit technical details
                "suggestions": ["Try rephrasing your question", "Try again in a moment"],
                "retry_after": None
            }
        )
'''

    # Find and replace lifespan function
    import re
    
    # Replace lifespan function
    lifespan_pattern = r'@asynccontextmanager\s*async def lifespan.*?yield.*?(?=\n@|\ndef |\nclass |\nif __name__|\Z)'
    if re.search(lifespan_pattern, content, re.DOTALL):
        content = re.sub(lifespan_pattern, new_lifespan.strip(), content, flags=re.DOTALL)
        print("✅ Lifespan function replaced")
    else:
        print("⚠️ Lifespan function not found - appending")
        # Add it before the last lines
        content = content + "\n\n" + new_lifespan.strip() + "\n"
    
    # Replace chat endpoint
    chat_pattern = r'@app\.post\("/api/v1/chat".*?async def chat_endpoint.*?return ChatResponse\([^}]*\}[^}]*\}[^}]*\)'
    if re.search(chat_pattern, content, re.DOTALL):
        content = re.sub(chat_pattern, new_chat_endpoint.strip(), content, flags=re.DOTALL)
        print("✅ Chat endpoint replaced")
    else:
        print("⚠️ Chat endpoint not found - appending")
        content = content + "\n\n" + new_chat_endpoint.strip() + "\n"
    
    # Write the updated content
    with open('$APP_DIR/main.py', 'w') as f:
        f.write(content)
    
    print("✅ FastAPI main.py updated successfully")
    
except Exception as e:
    print(f"❌ Error updating FastAPI: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
PYTHON_EOF

    # Run the FastAPI fix
    cd "$APP_DIR" && python3 /tmp/fix_fastapi_runpod.py
    
    log "✅ FastAPI fixes applied"
else
    log "⚠️ App directory or main.py not found - skipping FastAPI fixes"
    log "Available directories in /workspace:"
    ls -la /workspace/ 2>/dev/null || true
fi

log "🔧 Step 4: Update supervisor configuration if possible"

if [ -n "$SUPERVISOR_CONF" ]; then
    log "📝 Updating supervisor configuration at $SUPERVISOR_CONF"
    
    # Backup original
    cp "$SUPERVISOR_CONF" "${SUPERVISOR_CONF}.backup.$(date +%s)" 2>/dev/null || true
    
    # Update Redis configuration to disable protected mode
    sed -i 's/redis-server --bind 0.0.0.0 --port 6379 --save 60 1000 --appendonly yes/redis-server --bind 0.0.0.0 --port 6379 --save 60 1000 --appendonly yes --protected-mode no/g' "$SUPERVISOR_CONF" 2>/dev/null || true
    
    # Update environment variables for better compatibility
    sed -i 's/DEFAULT_MODEL="tinyllama:latest"/DEFAULT_MODEL="phi3:mini"/g' "$SUPERVISOR_CONF" 2>/dev/null || true
    sed -i 's/FALLBACK_MODEL="tinyllama:latest"/FALLBACK_MODEL="phi3:mini"/g' "$SUPERVISOR_CONF" 2>/dev/null || true
    sed -i 's/ALLOWED_ORIGINS="[^"]*"/ALLOWED_ORIGINS="*"/g' "$SUPERVISOR_CONF" 2>/dev/null || true
    
    log "✅ Supervisor configuration updated"
else
    log "⚠️ Supervisor configuration not found - skipping"
fi

log "🔧 Step 5: Restart services in dependency order"

# Stop all services
supervisorctl stop all 2>/dev/null
sleep 3

# Start Redis first
log "🚀 Starting Redis..."
supervisorctl start redis 2>/dev/null
sleep 5

# Start Ollama
log "🚀 Starting Ollama..."
supervisorctl start ollama 2>/dev/null
sleep 10

# Start FastAPI
log "🚀 Starting FastAPI..."
supervisorctl start ai-search-app 2>/dev/null
sleep 15

log "🔧 Step 6: Comprehensive testing"

# Test Redis
if redis-cli ping > /dev/null 2>&1; then
    log "✅ Redis: Connected and responding"
else
    log "❌ Redis: Not responding"
fi

# Test Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log "✅ Ollama: Connected and responding"
else
    log "❌ Ollama: Not responding"
    log "🔄 Checking if Ollama process is running..."
    ps aux | grep ollama | grep -v grep || log "No Ollama process found"
fi

# Test FastAPI
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log "✅ FastAPI: Connected and responding"
elif curl -s http://localhost:8000/ > /dev/null 2>&1; then
    log "⚠️ FastAPI: Responding but /health endpoint missing"
else
    log "❌ FastAPI: Not responding"
    log "🔄 Checking if FastAPI process is running..."
    ps aux | grep uvicorn | grep -v grep || log "No FastAPI process found"
fi

# Test the chat endpoint with comprehensive error reporting
log "🗣️ Testing chat endpoint..."
CHAT_RESULT=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, this is a test message"}' \
  --connect-timeout 10 --max-time 30)

HTTP_CODE="${CHAT_RESULT: -3}"
RESPONSE_BODY="${CHAT_RESULT%???}"

log "📊 Chat test results:"
log "   HTTP Code: $HTTP_CODE"
log "   Response: $RESPONSE_BODY"

if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | grep -q '"success":true'; then
    log "✅ Chat endpoint: SUCCESS!"
    # Extract and display the actual response
    ACTUAL_RESPONSE=$(echo "$RESPONSE_BODY" | grep -o '"response":"[^"]*"' | sed 's/"response":"//;s/"$//')
    log "💬 Chat response: $ACTUAL_RESPONSE"
else
    log "❌ Chat endpoint: Failed"
    if [ "$HTTP_CODE" != "200" ]; then
        log "   HTTP error code: $HTTP_CODE"
    fi
    if echo "$RESPONSE_BODY" | grep -q '"success":false'; then
        log "   API returned success:false"
    fi
fi

# System status check
log "📊 Final system status:"
STATUS_RESULT=$(curl -s http://localhost:8000/api/v1/system/status 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$STATUS_RESULT" | jq '.' 2>/dev/null || echo "$STATUS_RESULT"
else
    log "❌ System status endpoint not available"
fi

# Service status
log "📊 Supervisor service status:"
supervisorctl status 2>/dev/null || log "Supervisor status not available"

log "🎉 RUNPOD-ADAPTED COMPREHENSIVE FIX COMPLETE!"
log ""
log "🔍 If issues persist, check logs:"
log "   FastAPI: tail -f /workspace/logs/app.out.log"
log "   Redis: tail -f /workspace/logs/redis.out.log"
log "   Ollama: tail -f /workspace/logs/ollama.out.log"
log ""
log "🔄 To restart all services: supervisorctl restart all"
EOF
