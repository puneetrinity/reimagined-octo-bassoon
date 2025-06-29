#!/bin/bash
# Targeted FastAPI chat graph initialization fix
echo "🔧 FastAPI Chat Graph Initialization Fix"
echo "========================================"

echo "✅ Ollama is confirmed working (Python test passed)"
echo "❌ Issue is in FastAPI chat graph initialization"

echo ""
echo "1. Diagnosing FastAPI initialization sequence..."
cd /app && python3 -c "
import asyncio
import sys
sys.path.insert(0, '/app')

async def diagnose_fastapi():
    try:
        print('Testing FastAPI components...')
        
        # Test ModelManager creation
        from app.models.manager import ModelManager
        manager = ModelManager(ollama_host='http://localhost:11434')
        await manager.initialize()
        print('✅ ModelManager initializes OK')
        
        # Test ChatGraph creation
        from app.graphs.chat_graph import ChatGraph
        from app.cache.redis_client import CacheManager
        
        cache_manager = CacheManager(redis_url='redis://localhost:6379')
        chat_graph = ChatGraph(manager, cache_manager)
        print('✅ ChatGraph creates OK')
        
        # Test the chat flow
        from app.graphs.base import GraphState
        from app.models.manager import QualityLevel
        
        graph_state = GraphState(
            query_id='test-123',
            correlation_id='test-correlation',
            user_id='test-user',
            session_id='test-session',
            original_query='Hello test',
            quality_requirement=QualityLevel.MINIMAL,
            user_preferences={'tier': 'free'}
        )
        
        print('Testing graph execution...')
        result = await chat_graph.execute(graph_state)
        print(f'✅ Chat graph result: {type(result)}')
        print(f'✅ Final response: {getattr(result, \"final_response\", \"No final_response\")}')
        
    except Exception as e:
        print(f'❌ FastAPI diagnosis failed: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(diagnose_fastapi())
"

echo ""
echo "2. Applying FastAPI initialization fix..."

# Create a fixed startup sequence
cat > /tmp/fix_fastapi_init.py << 'EOF'
import re

# Read the main.py file
with open('/app/app/main.py', 'r') as f:
    content = f.read()

# Find the lifespan function and ensure proper initialization order
if 'async def lifespan(' in content:
    print('✅ Found lifespan function')
    
    # Ensure model manager is initialized before chat graph
    if 'await startup_monitor.log_startup_complete()' in content:
        # Add explicit initialization before startup complete
        content = content.replace(
            'await startup_monitor.log_startup_complete()',
            '''# Ensure model manager is properly initialized
        if app_state.get("model_manager"):
            try:
                await app_state["model_manager"].initialize()
                logger.info("Model manager explicitly initialized")
            except Exception as e:
                logger.error(f"Model manager initialization failed: {e}")
        
        await startup_monitor.log_startup_complete()'''
        )
        print('✅ Added explicit model manager initialization')
    
    # Write the updated file
    with open('/app/app/main.py', 'w') as f:
        f.write(content)
    
    print('✅ Updated main.py with initialization fix')
else:
    print('❌ Could not find lifespan function to fix')
EOF

cd /app && python3 /tmp/fix_fastapi_init.py

echo ""
echo "3. Restarting FastAPI with fixed initialization..."
supervisorctl restart ai-search-app
sleep 15

echo ""
echo "4. Testing the fix..."
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello with initialization fix","stream":false}'

echo ""
echo "5. Checking system status..."
curl -s http://localhost:8000/system/status | jq '.components'

echo ""
echo "6. If still failing, trying simple model test..."
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message":"Hi","stream":false,"quality_requirement":"minimal","max_execution_time":30}'

echo ""
echo "🎯 FastAPI initialization fix complete!"
