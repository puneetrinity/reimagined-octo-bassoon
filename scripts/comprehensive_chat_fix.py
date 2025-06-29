#!/usr/bin/env python3
"""
Comprehensive fix for the 'Model returned an empty or invalid response' error.
This addresses the actual FastAPI integration issues found in the diagnostic.
"""

import asyncio
import subprocess
import sys
import time

# Add the app directory to Python path
sys.path.insert(0, '/app')

def restart_fastapi():
    """Restart the FastAPI service"""
    print("🔄 Restarting FastAPI service...")
    try:
        result = subprocess.run(
            ['supervisorctl', 'restart', 'ai-search-app'], 
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print("   ✅ FastAPI restarted successfully")
            return True
        else:
            print(f"   ⚠️ FastAPI restart warning: {result.stderr}")
            return True  # Often works even with warnings
    except Exception as e:
        print(f"   ❌ FastAPI restart failed: {e}")
        return False

async def test_chat_graph_correct():
    """Test ChatGraph with proper GraphState object"""
    print("🕸️ Testing ChatGraph with correct parameters...")
    
    try:
        from app.graphs.chat_graph import ChatGraph
        from app.graphs.base import GraphState
        from app.models.manager import ModelManager
        
        # Initialize dependencies
        model_manager = ModelManager()
        await model_manager.initialize()
        
        # Create chat graph
        chat_graph = ChatGraph(model_manager=model_manager)
        
        # Create proper GraphState
        state = GraphState()
        state.original_query = "Hello, please say: ChatGraph test successful"
        state.max_tokens = 30
        state.conversation_history = []
        
        print(f"   Testing with query: {state.original_query}")
        
        # Execute with correct parameters
        result = await chat_graph.execute(state)
        
        print(f"   ChatGraph result type: {type(result)}")
        print(f"   ChatGraph result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Check for expected response
        if isinstance(result, dict):
            response = result.get('final_response') or result.get('response', '')
            success = result.get('success', False)
            
            print(f"   Success: {success}")
            print(f"   Response: '{response}'")
            
            if success and response and response.strip():
                print("✅ ChatGraph working correctly!")
                return True
            else:
                print("❌ ChatGraph returned empty/invalid response")
                return False
        else:
            print(f"❌ ChatGraph returned unexpected type: {type(result)}")
            return False
            
    except Exception as e:
        print(f"❌ ChatGraph test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_fastapi_endpoint():
    """Test the FastAPI chat endpoint"""
    print("🌐 Testing FastAPI chat endpoint...")
    
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/chat/complete",
                json={
                    "message": "Hello, please say: FastAPI test successful",
                    "max_tokens": 30
                }
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Response: {result}")
                
                if result.get('success') and result.get('response', '').strip():
                    print("✅ FastAPI endpoint working!")
                    return True
                else:
                    print("❌ FastAPI returned empty/invalid response")
                    return False
            else:
                error_detail = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"   Error: {error_detail}")
                return False
                
    except Exception as e:
        print(f"❌ FastAPI test failed: {e}")
        return False

async def main():
    print("🎯 COMPREHENSIVE CHAT SYSTEM FIX")
    print("=================================")
    
    # Step 1: Test ChatGraph with correct parameters
    print("\n1️⃣ Testing ChatGraph...")
    chat_success = await test_chat_graph_correct()
    
    # Step 2: Test FastAPI endpoint
    print("\n2️⃣ Testing FastAPI endpoint...")
    api_success = await test_fastapi_endpoint()
    
    # Step 3: If FastAPI fails, restart and retest
    if chat_success and not api_success:
        print("\n3️⃣ ChatGraph works but FastAPI fails - restarting service...")
        if restart_fastapi():
            # Wait for service to come up
            print("   ⏳ Waiting for service startup...")
            time.sleep(5)
            
            print("   🔄 Re-testing FastAPI...")
            api_success = await test_fastapi_endpoint()
    
    print("\n📊 FINAL RESULTS")
    print("================")
    print(f"ChatGraph:     {'✅ PASS' if chat_success else '❌ FAIL'}")
    print(f"FastAPI:       {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if chat_success and api_success:
        print("\n🎉 SUCCESS! The chat system is now fully working!")
        print("🎯 The 'Model returned an empty or invalid response' error is resolved.")
        print("")
        print("📱 Test commands:")
        print("curl -X POST http://localhost:8000/api/v1/chat/complete \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{\"message\": \"Hello!\", \"max_tokens\": 50}'")
        return True
    elif chat_success and not api_success:
        print("\n⚠️ ChatGraph works but FastAPI still has issues.")
        print("🔍 Possible causes:")
        print("   - FastAPI service initialization problems")
        print("   - Graph state conversion issues in the API layer")
        print("   - Response format mismatch")
        print("\n💡 Manual debugging:")
        print("   supervisorctl tail ai-search-app")
        print("   supervisorctl restart ai-search-app")
        return False
    else:
        print("\n❌ Fundamental issues detected.")
        print("🔍 Check the specific error messages above.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
