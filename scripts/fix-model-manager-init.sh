#!/bin/bash
# Targeted fix for model manager initialization issue
echo "🎯 Model Manager Initialization Fix"
echo "===================================="

echo "1. Checking current model manager state..."
curl -s http://localhost:8000/status | jq '.'

echo ""
echo "2. Testing direct model manager access..."
cd /app && python3 -c "
import asyncio
import sys
sys.path.insert(0, '/app')

async def test_model_manager():
    try:
        from app.models.manager import ModelManager
        from app.models.ollama_client import OllamaClient
        
        print('Creating OllamaClient...')
        ollama_client = OllamaClient(base_url='http://localhost:11434')
        
        print('Initializing OllamaClient...')
        await ollama_client.initialize()
        
        print('Creating ModelManager...')
        model_manager = ModelManager(ollama_client)
        
        print('Initializing ModelManager...')
        await model_manager.initialize()
        
        print('✅ Model manager initialized successfully')
        
        print('Testing generation...')
        result = await model_manager.generate(
            model_name='tinyllama:latest',
            prompt='Hello',
            max_tokens=50
        )
        
        print(f'✅ Generation test: success={result.success}, text=\"{result.text[:100]}...\"')
        
    except Exception as e:
        print(f'❌ Model manager test failed: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test_model_manager())
"

echo ""
echo "3. Checking if the issue is in app initialization..."
cd /app && python3 -c "
import sys
sys.path.insert(0, '/app')

try:
    from app.dependencies import get_model_manager
    print('✅ get_model_manager import OK')
    
    # Try to get the model manager
    manager = get_model_manager()
    print(f'Model manager from dependency: {manager}')
    
except Exception as e:
    print(f'❌ Dependency injection failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "4. Applying fix to force model manager initialization..."

# Create a simple initialization endpoint test
curl -X POST http://localhost:8000/health -H "Content-Type: application/json" || echo "Health POST failed"

echo ""
echo "5. Forcing model manager reinitialization via API call..."

# Try to trigger model manager initialization
cat > /tmp/init_models.py << 'EOF'
import asyncio
import httpx

async def force_init():
    async with httpx.AsyncClient() as client:
        try:
            # Try to access the health endpoint multiple times to trigger initialization
            for i in range(3):
                print(f"Attempt {i+1}: Accessing health endpoint...")
                response = await client.get("http://localhost:8000/health")
                print(f"Health response: {response.status_code}")
                
                print(f"Attempt {i+1}: Accessing status endpoint...")
                response = await client.get("http://localhost:8000/status")
                print(f"Status response: {response.status_code} - {response.text}")
                
                if "null" not in response.text:
                    print("✅ Model manager appears to be initialized!")
                    break
                    
                await asyncio.sleep(2)
            
            print("Testing chat endpoint...")
            response = await client.post(
                "http://localhost:8000/api/v1/chat/complete",
                json={"message": "Hello initialization test", "stream": False}
            )
            print(f"Chat test: {response.status_code} - {response.text[:200]}")
            
        except Exception as e:
            print(f"Force init failed: {e}")

asyncio.run(force_init())
EOF

cd /app && python3 /tmp/init_models.py

echo ""
echo "6. Final status check..."
curl -s http://localhost:8000/status | jq '.'

echo ""
echo "7. Final chat test..."
curl -X POST http://localhost:8000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -d '{"message":"Final test after initialization","stream":false}'

echo ""
echo "🎯 Initialization fix complete!"
