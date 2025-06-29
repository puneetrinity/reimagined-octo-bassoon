#!/usr/bin/env python3
"""
Debug script to identify model manager initialization issues
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, '/app')
os.chdir('/app')

async def debug_initialization():
    print("🔍 Debugging Model Manager Initialization")
    print("=" * 50)
    
    try:
        # Test 1: Basic imports
        print("1. Testing imports...")
        from app.models.manager import ModelManager
        from app.models.ollama_client import OllamaClient
        from app.dependencies import get_model_manager, get_cache_manager
        print("✅ All imports successful")
        
        # Test 2: Check if singleton instances exist
        print("\n2. Checking dependency injection...")
        try:
            manager = get_model_manager()
            print(f"✅ Model manager from DI: {type(manager)} - {manager}")
        except Exception as e:
            print(f"❌ Model manager DI failed: {e}")
        
        try:
            cache = get_cache_manager()
            print(f"✅ Cache manager from DI: {type(cache)} - {cache}")
        except Exception as e:
            print(f"❌ Cache manager DI failed: {e}")
        
        # Test 3: Manual initialization
        print("\n3. Testing manual initialization...")
        ollama_client = OllamaClient(base_url="http://localhost:11434")
        await ollama_client.initialize()
        print("✅ OllamaClient initialized")
        
        model_manager = ModelManager(ollama_client)
        await model_manager.initialize()
        print("✅ ModelManager initialized manually")
        
        # Test 4: Test generation
        print("\n4. Testing generation...")
        result = await model_manager.generate(
            model_name="tinyllama:latest",
            prompt="Say hello",
            max_tokens=20
        )
        print(f"✅ Generation result: success={result.success}")
        if result.success:
            print(f"   Response: {result.text}")
        else:
            print(f"   Error: {result.error}")
        
        # Test 5: Check available models
        print("\n5. Checking available models...")
        available_models = await model_manager.get_available_models()
        print(f"✅ Available models: {available_models}")
        
        # Test 6: Check model stats
        print("\n6. Checking model stats...")
        try:
            stats = model_manager.get_model_stats()
            print(f"✅ Model stats: {stats}")
        except Exception as e:
            print(f"❌ Model stats failed: {e}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_initialization())
