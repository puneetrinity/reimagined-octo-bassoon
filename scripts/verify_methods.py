#!/usr/bin/env python3
"""
Quick method verification script to ensure all generate methods are correctly named and accessible.
"""

import asyncio
import sys
import inspect

# Add the app directory to Python path
sys.path.insert(0, '/app')

async def verify_methods():
    print("🔍 METHOD VERIFICATION")
    print("======================")
    
    # Test 1: Verify OllamaClient methods
    print("\n1. 📋 OllamaClient methods:")
    try:
        from app.models.ollama_client import OllamaClient
        
        client = OllamaClient()
        methods = [method for method in dir(client) if not method.startswith('_') and callable(getattr(client, method))]
        
        generation_methods = [m for m in methods if 'generate' in m.lower()]
        print(f"   All methods: {len(methods)} total")
        print(f"   Generation methods: {generation_methods}")
        
        # Check if the correct method exists
        if hasattr(client, 'generate'):
            print("   ✅ client.generate() method exists")
            sig = inspect.signature(client.generate)
            print(f"   📝 Signature: generate{sig}")
        else:
            print("   ❌ client.generate() method NOT found")
            
        if hasattr(client, 'generate_text'):
            print("   ⚠️  client.generate_text() method exists (unexpected)")
        else:
            print("   ✅ client.generate_text() method does NOT exist (good)")
            
    except Exception as e:
        print(f"   ❌ Error importing OllamaClient: {e}")
    
    # Test 2: Verify ModelManager methods  
    print("\n2. 🎛️ ModelManager methods:")
    try:
        from app.models.manager import ModelManager
        
        manager = ModelManager()
        methods = [method for method in dir(manager) if not method.startswith('_') and callable(getattr(manager, method))]
        
        generation_methods = [m for m in methods if 'generate' in m.lower()]
        print(f"   All methods: {len(methods)} total")
        print(f"   Generation methods: {generation_methods}")
        
        # Check if the correct method exists
        if hasattr(manager, 'generate'):
            print("   ✅ manager.generate() method exists")
            sig = inspect.signature(manager.generate)
            print(f"   📝 Signature: generate{sig}")
        else:
            print("   ❌ manager.generate() method NOT found")
            
    except Exception as e:
        print(f"   ❌ Error importing ModelManager: {e}")
    
    # Test 3: Test method calls work
    print("\n3. 🧪 Testing method calls:")
    try:
        from app.models.ollama_client import OllamaClient
        from app.models.manager import ModelManager
        
        # Test OllamaClient
        print("   Testing OllamaClient.generate()...")
        client = OllamaClient(base_url="http://localhost:11434")
        await client.initialize()
        
        health = await client.health_check()
        if health:
            models = await client.list_models()
            if models:
                model_name = models[0]['name']
                result = await client.generate(
                    model_name=model_name,
                    prompt="Test",
                    max_tokens=5
                )
                print(f"   ✅ OllamaClient.generate() returned: {type(result).__name__}")
            else:
                print("   ⚠️  No models available for testing")
        else:
            print("   ⚠️  Ollama not healthy, skipping direct test")
        
        # Test ModelManager
        print("   Testing ModelManager.generate()...")
        manager = ModelManager()
        await manager.initialize()
        
        stats = manager.get_model_stats()
        if stats.get('total_models', 0) > 0:
            models = list(manager.models.keys())
            model_name = models[0]
            result = await manager.generate(
                model_name=model_name,
                prompt="Test",
                max_tokens=5
            )
            print(f"   ✅ ModelManager.generate() returned: {type(result).__name__}")
        else:
            print("   ⚠️  No models available in ModelManager")
            
    except Exception as e:
        print(f"   ❌ Error testing method calls: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Method verification complete!")

if __name__ == "__main__":
    asyncio.run(verify_methods())
