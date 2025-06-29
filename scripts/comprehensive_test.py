#!/usr/bin/env python3
"""
Final diagnostic and fix script for the AI chat system.
This script tests the entire chain from Ollama to the FastAPI endpoint.
"""

import asyncio
import json
import sys
import time
import traceback
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/app')

async def test_ollama_client():
    """Test the OllamaClient directly"""
    print("🔧 Testing OllamaClient...")
    try:
        from app.models.ollama_client import OllamaClient
        
        client = OllamaClient(base_url="http://localhost:11434")
        await client.initialize()
        
        # Health check
        health = await client.health_check()
        print(f"   Health: {health}")
        
        if not health:
            print("❌ Ollama health check failed")
            return False
            
        # List models
        models = await client.list_models()
        print(f"   Available models: {[m['name'] for m in models]}")
        
        if not models:
            print("❌ No models available")
            return False
            
        # Test generation
        model_name = models[0]['name']
        print(f"   Testing generation with {model_name}...")
        
        result = await client.generate(
            model_name=model_name,
            prompt="Say exactly: OllamaClient works",
            max_tokens=10
        )
        
        print(f"   Result: success={result.success}, text='{result.text}', error={result.error}")
        
        if result.success and result.text.strip():
            print("✅ OllamaClient test PASSED")
            return True
        else:
            print("❌ OllamaClient test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ OllamaClient exception: {e}")
        traceback.print_exc()
        return False

async def test_model_manager():
    """Test the ModelManager"""
    print("🎛️ Testing ModelManager...")
    try:
        from app.models.manager import ModelManager
        
        manager = ModelManager()
        await manager.initialize()
        
        stats = manager.get_model_stats()
        print(f"   Model stats: {stats}")
        
        if stats.get('total_models', 0) == 0:
            print("❌ No models in ModelManager")
            return False
            
        # Test generation
        models = list(manager.models.keys())
        model_name = models[0]
        print(f"   Testing generation with {model_name}...")
        
        result = await manager.generate(
            model_name=model_name,
            prompt="Say exactly: ModelManager works",
            max_tokens=10
        )
        
        print(f"   Result: success={result.success}, text='{result.text}', error={result.error}")
        
        if result.success and result.text.strip():
            print("✅ ModelManager test PASSED")
            return True
        else:
            print("❌ ModelManager test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ ModelManager exception: {e}")
        traceback.print_exc()
        return False

async def test_chat_graph():
    """Test the ChatGraph"""
    print("🕸️ Testing ChatGraph...")
    try:
        from app.graphs.chat_graph import ChatGraph
        from app.models.manager import ModelManager
        
        # Create model manager
        model_manager = ModelManager()
        await model_manager.initialize()
        
        # Create chat graph
        chat_graph = ChatGraph(
            model_manager=model_manager,
            cache_manager=None
        )
        
        # Test the graph
        result = await chat_graph.execute(
            query="Say exactly: ChatGraph works",
            max_tokens=10
        )
        
        print(f"   ChatGraph result: {result}")
        
        if result.get('success') and result.get('response'):
            print("✅ ChatGraph test PASSED")
            return True
        else:
            print("❌ ChatGraph test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ ChatGraph exception: {e}")
        traceback.print_exc()
        return False

async def test_api_endpoint():
    """Test the FastAPI endpoint"""
    print("🌐 Testing FastAPI endpoint...")
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/chat/complete",
                json={
                    "message": "Say exactly: FastAPI works",
                    "max_tokens": 10
                }
            )
            
            print(f"   Response status: {response.status_code}")
            result = response.json()
            print(f"   Response body: {result}")
            
            if response.status_code == 200 and result.get('success') and result.get('response'):
                print("✅ FastAPI endpoint test PASSED")
                return True
            else:
                print("❌ FastAPI endpoint test FAILED")
                return False
                
    except Exception as e:
        print(f"❌ FastAPI endpoint exception: {e}")
        traceback.print_exc()
        return False

async def main():
    print("🔍 COMPREHENSIVE AI CHAT SYSTEM TEST")
    print("====================================")
    
    tests = [
        ("OllamaClient", test_ollama_client),
        ("ModelManager", test_model_manager),
        ("ChatGraph", test_chat_graph),
        ("FastAPI Endpoint", test_api_endpoint)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
        
        time.sleep(1)  # Brief pause between tests
    
    print("\n📊 FINAL RESULTS")
    print("================")
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("🎯 The chat system should be working correctly now.")
        print("💡 Try testing the chat endpoint from your frontend.")
    else:
        print("\n⚠️ Some tests failed.")
        print("🔍 Check the specific error messages above for troubleshooting.")
    
    return all_passed

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
