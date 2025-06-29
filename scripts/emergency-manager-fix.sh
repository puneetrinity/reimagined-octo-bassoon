#!/bin/bash
# Quick fix for the ModelManager initialization bug
echo "🚨 Emergency ModelManager Bug Fix"
echo "================================="

echo "1. The issue is in our test script - let's test the real endpoints..."

# Test the correct status endpoint
echo "Testing /system/status endpoint..."
curl -s http://localhost:8000/system/status

echo ""
echo "2. Testing the real problem - let's check what's in the dependencies..."

cd /app && python3 -c "
import sys
sys.path.insert(0, '/app')

try:
    from app.dependencies import get_model_manager
    from app.core.config import get_settings
    
    print('Getting settings...')
    settings = get_settings()
    print(f'Ollama host from settings: {settings.ollama_host}')
    
    print('Getting model manager...')
    manager = get_model_manager()
    print(f'Model manager: {manager}')
    print(f'Model manager ollama_client: {manager.ollama_client}')
    print(f'Model manager base_url: {manager.ollama_client.base_url}')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "3. Let's try to actually use the FastAPI app's model manager..."

cd /app && python3 -c "
import asyncio
import sys
sys.path.insert(0, '/app')

async def test_real_manager():
    try:
        from app.dependencies import get_model_manager
        
        manager = get_model_manager()
        print(f'Got manager: {manager}')
        
        # Initialize it
        await manager.initialize()
        print('Manager initialized successfully')
        
        # Try generation
        result = await manager.generate(
            model_name='tinyllama:latest',
            prompt='Hello',
            max_tokens=20
        )
        
        print(f'Generation result: success={result.success}')
        if result.success:
            print(f'Response: {result.text}')
        else:
            print(f'Error: {result.error}')
            
    except Exception as e:
        print(f'Real manager test failed: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test_real_manager())
"

echo ""
echo "4. Force restart FastAPI to clear any cached bad state..."
supervisorctl restart ai-search-app
sleep 10

echo ""
echo "5. Test the chat endpoint after restart..."
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello after manager fix","stream":false}'

echo ""
echo "🎯 Bug fix attempt complete!"
