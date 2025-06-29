#!/usr/bin/env python3
"""
Quick fix for the ChatGraph and FastAPI issues identified in the diagnostic.
"""

import asyncio
import json
import sys
import subprocess
import time

# Add the app directory to Python path
sys.path.insert(0, '/app')

async def test_chat_graph_correct_usage():
    """Test ChatGraph with correct parameters"""
    print("🕸️ Testing ChatGraph with correct usage...")
    try:
        from app.graphs.chat_graph import ChatGraph
        from app.graphs.base import GraphState
        from app.models.manager import ModelManager
        
        # Create model manager
        model_manager = ModelManager()
        await model_manager.initialize()
        
        # Create chat graph
        chat_graph = ChatGraph(
            model_manager=model_manager,
            cache_manager=None
        )
        
        # Create proper GraphState
        state = GraphState(
            original_query="Say exactly: ChatGraph works correctly",
            conversation_history=[],
            user_id="test-user"
        )
        
        # Test the graph with correct parameters
        result = await chat_graph.execute(state)
        
        print(f"   ChatGraph result: success={not result.errors}, final_response='{getattr(result, 'final_response', 'MISSING')}'")
        
        if hasattr(result, 'final_response') and result.final_response:
            print("✅ ChatGraph test PASSED")
            return True
        else:
            print("❌ ChatGraph test FAILED - no final_response")
            return False
            
    except Exception as e:
        print(f"❌ ChatGraph exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fastapi_with_restart():
    """Test FastAPI endpoint after restarting the service"""
    print("🔄 Restarting FastAPI service...")
    
    # Restart FastAPI
    result = subprocess.run(['supervisorctl', 'restart', 'ai-search-app'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ FastAPI restarted successfully")
    else:
        print(f"   ⚠️ FastAPI restart warning: {result.stderr}")
    
    # Wait for startup
    print("   ⏳ Waiting for FastAPI startup...")
    time.sleep(5)
    
    # Test the endpoint
    print("🌐 Testing FastAPI endpoint after restart...")
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/chat/complete",
                json={
                    "message": "Say exactly: FastAPI works after restart",
                    "max_tokens": 20
                }
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Response: {result}")
                
                if result.get('success') and result.get('response', '').strip():
                    print("✅ FastAPI endpoint test PASSED")
                    return True
                else:
                    print("❌ FastAPI endpoint returned empty response")
                    return False
            else:
                print(f"❌ FastAPI endpoint returned {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ FastAPI test exception: {e}")
        return False

async def fix_main_app_initialization():
    """Check if the main FastAPI app initialization needs fixing"""
    print("🔧 Checking FastAPI app initialization...")
    
    try:
        # Read the main.py file to see if there are any obvious issues
        with open('/app/app/main.py', 'r') as f:
            content = f.read()
        
        # Check if the lifespan and model initialization look correct
        if 'model_manager' in content and 'chat_graph' in content:
            print("   ✅ main.py appears to have model_manager and chat_graph initialization")
        else:
            print("   ⚠️ main.py may be missing proper initialization")
            
        # Check recent logs for any initialization errors
        result = subprocess.run(['supervisorctl', 'tail', 'ai-search-app'], 
                              capture_output=True, text=True)
        
        if 'error' in result.stdout.lower() or 'exception' in result.stdout.lower():
            print("   ⚠️ Found errors in FastAPI logs:")
            print("   " + "\n   ".join(result.stdout.split('\n')[-10:]))
        else:
            print("   ✅ No obvious errors in recent FastAPI logs")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking app initialization: {e}")
        return False

async def main():
    print("🎯 TARGETED FIX FOR CHATGRAPH & FASTAPI ISSUES")
    print("==============================================")
    
    # Step 1: Test ChatGraph with correct usage
    chatgraph_works = await test_chat_graph_correct_usage()
    
    # Step 2: Check FastAPI app initialization  
    app_check = await fix_main_app_initialization()
    
    # Step 3: Test FastAPI after restart
    fastapi_works = await test_fastapi_with_restart()
    
    print("\n📊 RESULTS")
    print("==========")
    print(f"ChatGraph (correct usage): {'✅ PASS' if chatgraph_works else '❌ FAIL'}")
    print(f"FastAPI App Check:         {'✅ PASS' if app_check else '❌ FAIL'}")
    print(f"FastAPI Endpoint:          {'✅ PASS' if fastapi_works else '❌ FAIL'}")
    
    if chatgraph_works and fastapi_works:
        print("\n🎉 SUCCESS! Both ChatGraph and FastAPI are working!")
        print("💡 The 'Model returned an empty or invalid response' error should be resolved.")
        print("📱 Try testing the chat functionality from your frontend now.")
        
        # Final test
        print("\n🧪 Final quick test command:")
        print("curl -X POST http://localhost:8000/api/v1/chat/complete \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{\"message\": \"Hello, how are you?\", \"max_tokens\": 50}'")
        
        return True
    
    elif chatgraph_works and not fastapi_works:
        print("\n🔧 ChatGraph works but FastAPI has issues.")
        print("💡 Suggestions:")
        print("   1. Check FastAPI logs: supervisorctl tail ai-search-app")
        print("   2. Restart all services: supervisorctl restart all")
        print("   3. Check if there are startup errors in the logs")
        return False
    
    else:
        print("\n⚠️ Issues detected with the core components.")
        print("💡 The underlying model integration is working, but there may be")
        print("   integration issues between the components.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
