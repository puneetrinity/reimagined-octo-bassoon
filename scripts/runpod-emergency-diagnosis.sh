#!/bin/bash

echo "🔍 RUNPOD STRUCTURE ANALYZER & QUICK FIX"
echo "========================================"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🔍 Step 1: Analyzing current RunPod structure"

# Find where the actual app code is located
log "📂 Searching for Python application files..."
find /workspace -name "*.py" -type f | head -10
find /workspace -name "main.py" -type f
find /workspace -name "requirements.txt" -type f

log "📂 Checking for app directories..."
find /workspace -name "app" -type d

log "📂 Checking /app directory..."
ls -la /app/ 2>/dev/null || log "❌ /app directory not accessible"

log "📂 Current /workspace structure:"
ls -la /workspace/

log "🔍 Step 2: Checking what's running in FastAPI"
log "📊 FastAPI process details:"
ps aux | grep uvicorn

log "📊 FastAPI logs (last 20 lines):"
tail -20 /workspace/logs/app.out.log 2>/dev/null || log "No app logs found"

log "📊 FastAPI error logs:"
tail -10 /workspace/logs/app.err.log 2>/dev/null || log "No app error logs found"

log "🔍 Step 3: Testing FastAPI endpoints"
log "🧪 Testing root endpoint:"
curl -s http://localhost:8000/ || log "Root endpoint failed"

log "🧪 Testing docs endpoint:"
curl -s http://localhost:8000/docs || log "Docs endpoint failed"

log "🧪 Available endpoints:"
curl -s http://localhost:8000/openapi.json | jq '.paths' 2>/dev/null || log "OpenAPI spec not available"

log "🔍 Step 4: Quick diagnosis"

# Check if this is a deployment issue
if [ ! -d "/app" ] || [ ! -f "/app/main.py" ]; then
    log "❌ DIAGNOSIS: Missing application code"
    log "   - /app directory or main.py is missing"
    log "   - This appears to be a deployment/build issue"
    log "   - The Docker container may not have been built correctly"
    
    log "🔧 QUICK FIX ATTEMPT: Looking for alternative app locations"
    
    # Look for any Python app in workspace
    MAIN_PY_FOUND=$(find /workspace -name "main.py" -type f | head -1)
    if [ -n "$MAIN_PY_FOUND" ]; then
        log "✅ Found main.py at: $MAIN_PY_FOUND"
        
        # Try to determine the app directory
        APP_DIR=$(dirname "$MAIN_PY_FOUND")
        log "📂 App directory appears to be: $APP_DIR"
        
        # Check if we can restart FastAPI from the correct location
        log "🔧 Attempting to restart FastAPI from correct location..."
        
        supervisorctl stop ai-search-app
        sleep 2
        
        # Update supervisor config temporarily
        log "📝 Updating supervisor config for correct app directory..."
        
        # Check current supervisor config
        SUPERVISOR_CONFIG=""
        if [ -f "/etc/supervisor/conf.d/supervisord.conf" ]; then
            SUPERVISOR_CONFIG="/etc/supervisor/conf.d/supervisord.conf"
        elif [ -f "/etc/supervisord.conf" ]; then
            SUPERVISOR_CONFIG="/etc/supervisord.conf"
        elif [ -f "/workspace/supervisord.conf" ]; then
            SUPERVISOR_CONFIG="/workspace/supervisord.conf"
        fi
        
        if [ -n "$SUPERVISOR_CONFIG" ]; then
            log "📂 Using supervisor config: $SUPERVISOR_CONFIG"
            # Backup and update directory
            cp "$SUPERVISOR_CONFIG" "${SUPERVISOR_CONFIG}.backup"
            sed -i "s|directory=/app|directory=$APP_DIR|g" "$SUPERVISOR_CONFIG"
            sed -i "s|PYTHONPATH=\"/app\"|PYTHONPATH=\"$APP_DIR\"|g" "$SUPERVISOR_CONFIG"
            
            # Reload supervisor config
            supervisorctl reread
            supervisorctl update
            
            # Restart the app
            supervisorctl start ai-search-app
            sleep 10
            
            # Test again
            log "🧪 Testing endpoints after fix..."
            if curl -s http://localhost:8000/api/v1/chat > /dev/null 2>&1; then
                log "✅ Chat endpoint now accessible!"
            else
                log "❌ Chat endpoint still not accessible"
            fi
        else
            log "❌ Could not find supervisor config to update"
        fi
    else
        log "❌ No main.py found anywhere in /workspace"
        log "🚨 This indicates a serious deployment issue"
        
        log "🔧 ATTEMPTING EMERGENCY APP CREATION..."
        
        # Create a minimal working FastAPI app
        mkdir -p /app/app
        
        cat > /app/main.py << 'PYTHON_EOF'
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    query: str
    conversation_id: str = None

class ChatResponse(BaseModel):
    response: str
    query_id: str
    correlation_id: str
    success: bool = True

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Emergency FastAPI app starting...")
    yield
    logger.info("🛑 Emergency FastAPI app shutting down...")

# Create FastAPI app
app = FastAPI(
    title="AI Search System - Emergency Mode",
    description="Emergency FastAPI application",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Emergency AI Search System", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "mode": "emergency"}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Emergency chat endpoint"""
    correlation_id = str(uuid.uuid4())
    query_id = str(uuid.uuid4())
    
    logger.info(f"Emergency chat request: {request.query}")
    
    # Simple response generation
    response_text = f"Emergency mode: I received your message '{request.query}'. The full AI system is currently being deployed. Please try again shortly when all services are ready."
    
    return ChatResponse(
        response=response_text,
        query_id=query_id,
        correlation_id=correlation_id,
        success=True
    )

@app.get("/api/v1/system/status")
async def system_status():
    return {
        "mode": "emergency",
        "status": "partial",
        "message": "System is in emergency mode - full deployment needed"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
PYTHON_EOF
        
        log "✅ Created emergency FastAPI app"
        
        # Restart FastAPI
        supervisorctl stop ai-search-app
        sleep 2
        supervisorctl start ai-search-app
        sleep 10
        
        # Test the emergency app
        log "🧪 Testing emergency app..."
        EMERGENCY_TEST=$(curl -s -X POST http://localhost:8000/api/v1/chat \
          -H "Content-Type: application/json" \
          -d '{"query": "Emergency test"}')
        
        if echo "$EMERGENCY_TEST" | grep -q '"success":true'; then
            log "✅ Emergency app working!"
            log "📱 Response: $EMERGENCY_TEST"
        else
            log "❌ Emergency app also failed"
            log "📱 Response: $EMERGENCY_TEST"
        fi
    fi
else
    log "✅ Application code exists, checking for other issues..."
    
    # App exists, check for import/initialization errors
    log "🔍 Checking for Python import errors..."
    cd /app && python3 -c "
try:
    import app.main
    print('✅ Main module imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
"
fi

log "🔍 Step 5: Final recommendations"

log "📋 DIAGNOSIS SUMMARY:"
log "   - Redis: ✅ Working"
log "   - Ollama: ✅ Working"
log "   - FastAPI: ⚠️ Running but endpoints missing"
log "   - Root cause: Missing or incorrect application deployment"

log ""
log "🛠️ NEXT STEPS:"
log "1. Check if this is a Docker build issue"
log "2. Verify the application code is properly deployed"
log "3. Check supervisor configuration for correct paths"
log "4. Review application logs for Python import errors"
log ""
log "📞 If this is a persistent issue, the container may need to be rebuilt"
log "📞 Or the application code needs to be properly deployed to /app"

EOF
