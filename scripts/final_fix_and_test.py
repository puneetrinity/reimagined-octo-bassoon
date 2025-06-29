#!/usr/bin/env python3
"""
Final comprehensive fix for the "Model returned an empty or invalid response" error.
This script will diagnose the issue and apply fixes as needed.
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/app')

def run_command(cmd, shell=True):
    """Run a shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

async def test_ollama_direct():
    """Test Ollama directly via curl"""
    print("🔧 Testing Ollama API directly...")
    
    # Test health
    success, stdout, stderr = run_command('curl -s http://localhost:11434/api/tags')
    if not success:
        print(f"   ❌ Ollama not responding: {stderr}")
        return False
    
    try:
        models_data = json.loads(stdout)
        models = [m['name'] for m in models_data.get('models', [])]
        print(f"   📋 Available models: {models}")
        
        if not models:
            print("   ❌ No models available")
            return False
        
        # Test generation
        model_name = models[0]
        test_data = {
            "model": model_name,
            "prompt": "Say exactly: Direct Ollama works",
            "stream": False
        }
        
        cmd = f'curl -s -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" -d \'{json.dumps(test_data)}\''
        success, stdout, stderr = run_command(cmd)
        
        if success:
            response = json.loads(stdout)
            if response.get('response'):
                print(f"   ✅ Direct Ollama test: '{response['response']}'")
                return True
            else:
                print(f"   ❌ Direct Ollama empty response: {response}")
                return False
        else:
            print(f"   ❌ Direct Ollama failed: {stderr}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON from Ollama: {e}")
        return False

async def test_python_stack():
    """Test the Python stack (OllamaClient -> ModelManager -> ChatGraph)"""
    print("🐍 Testing Python stack...")
    
    try:
        # Test OllamaClient
        from app.models.ollama_client import OllamaClient
        
        client = OllamaClient(base_url="http://localhost:11434")
        await client.initialize()
        
        health = await client.health_check()
        if not health:
            print("   ❌ OllamaClient health check failed")
            return False
        
        models = await client.list_models()
        if not models:
            print("   ❌ No models in OllamaClient")
            return False
        
        # Test generation
        model_name = models[0]['name']
        result = await client.generate(
            model_name=model_name,
            prompt="Say exactly: Python OllamaClient works",
            max_tokens=20
        )
        
        if not result.success or not result.text.strip():
            print(f"   ❌ OllamaClient generation failed: {result.error}")
            return False
        
        print(f"   ✅ OllamaClient: '{result.text}'")
        
        # Test ModelManager
        from app.models.manager import ModelManager
        
        manager = ModelManager()
        await manager.initialize()
        
        result = await manager.generate(
            model_name=model_name,
            prompt="Say exactly: ModelManager works",
            max_tokens=20
        )
        
        if not result.success or not result.text.strip():
            print(f"   ❌ ModelManager generation failed: {result.error}")
            return False
        
        print(f"   ✅ ModelManager: '{result.text}'")
        
        # Test ChatGraph
        from app.graphs.chat_graph import ChatGraph
        
        chat_graph = ChatGraph(model_manager=manager)
        graph_result = await chat_graph.execute(
            query="Say exactly: ChatGraph works",
            max_tokens=20
        )
        
        if not graph_result.get('success') or not graph_result.get('response', '').strip():
            print(f"   ❌ ChatGraph failed: {graph_result}")
            return False
        
        print(f"   ✅ ChatGraph: '{graph_result['response']}'")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Python stack exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fastapi_endpoint():
    """Test the FastAPI endpoint"""
    print("🌐 Testing FastAPI endpoint...")
    
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/chat/complete",
                json={
                    "message": "Say exactly: FastAPI endpoint works",
                    "max_tokens": 20
                }
            )
            
            if response.status_code != 200:
                print(f"   ❌ HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            if not result.get('success') or not result.get('response', '').strip():
                print(f"   ❌ FastAPI invalid response: {result}")
                return False
            
            print(f"   ✅ FastAPI: '{result['response']}'")
            return True
            
    except Exception as e:
        print(f"   ❌ FastAPI test exception: {e}")
        return False

async def restart_services():
    """Restart services if needed"""
    print("🔄 Restarting services...")
    
    # Restart FastAPI
    success, stdout, stderr = run_command('supervisorctl restart ai-search-app')
    if success:
        print("   ✅ FastAPI restarted")
    else:
        print(f"   ⚠️  FastAPI restart issue: {stderr}")
    
    # Wait for startup
    time.sleep(3)
    
    # Check status
    success, stdout, stderr = run_command('supervisorctl status')
    if success:
        print("   📊 Service status:")
        for line in stdout.strip().split('\n'):
            if 'RUNNING' in line:
                print(f"      ✅ {line}")
            else:
                print(f"      ⚠️  {line}")

async def main():
    print("🎯 FINAL AI CHAT SYSTEM FIX")
    print("============================")
    
    # Step 1: Test Ollama directly
    ollama_direct = await test_ollama_direct()
    
    # Step 2: Test Python stack
    python_stack = await test_python_stack()
    
    # Step 3: Test FastAPI
    fastapi_test = await test_fastapi_endpoint()
    
    print("\n📊 DIAGNOSIS RESULTS")
    print("===================")
    print(f"Direct Ollama: {'✅ PASS' if ollama_direct else '❌ FAIL'}")
    print(f"Python Stack:  {'✅ PASS' if python_stack else '❌ FAIL'}")
    print(f"FastAPI API:   {'✅ PASS' if fastapi_test else '❌ FAIL'}")
    
    if ollama_direct and python_stack and fastapi_test:
        print("\n🎉 ALL TESTS PASSED!")
        print("🎯 The chat system is working correctly.")
        print("💡 The 'Model returned an empty or invalid response' error should be resolved.")
        print("📱 Try testing the chat functionality from your frontend now.")
        return True
    
    elif ollama_direct and python_stack and not fastapi_test:
        print("\n🔧 FastAPI issue detected. Restarting services...")
        await restart_services()
        
        # Re-test FastAPI
        print("🔄 Re-testing FastAPI after restart...")
        time.sleep(2)
        fastapi_retest = await test_fastapi_endpoint()
        
        if fastapi_retest:
            print("✅ FastAPI working after restart!")
            return True
        else:
            print("❌ FastAPI still failing after restart.")
            print("🔍 Check FastAPI logs: supervisorctl tail ai-search-app")
            return False
    
    elif ollama_direct and not python_stack:
        print("\n❌ Python stack issue detected.")
        print("🔍 This suggests a problem with OllamaClient or ModelManager initialization.")
        print("💡 Check the specific error messages above.")
        return False
    
    elif not ollama_direct:
        print("\n❌ Ollama service issue detected.")
        print("🔍 Ollama is not responding correctly.")
        print("💡 Check Ollama service: supervisorctl status ollama")
        return False
    
    else:
        print("\n❌ Multiple issues detected.")
        print("🔍 Check all error messages above for specific problems.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print("\n🚀 SYSTEM READY!")
    else:
        print("\n⚠️  ISSUES DETECTED - See messages above for troubleshooting.")
    sys.exit(0 if result else 1)
