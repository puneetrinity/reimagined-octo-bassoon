#!/usr/bin/env python3
"""
Quick fix for ChatGraph.execute() parameter issue.
The diagnostic showed that ChatGraph expects a GraphState object, not keyword arguments.
"""

import asyncio
import sys
import traceback

# Add the app directory to Python path
sys.path.insert(0, '/app')

async def test_corrected_chat_graph():
    """Test ChatGraph with correct parameters"""
    print("🔧 Testing ChatGraph with correct GraphState...")
    
    try:
        from app.graphs.chat_graph import ChatGraph
        from app.graphs.base import GraphState
        from app.models.manager import ModelManager
        
        # Create model manager
        model_manager = ModelManager()
        await model_manager.initialize()
        
        # Create chat graph
        chat_graph = ChatGraph(model_manager=model_manager)
        
        # Create proper GraphState object
        state = GraphState()
        state.original_query = "Say exactly: ChatGraph works correctly"
        state.max_tokens = 20
        state.conversation_history = []
        
        print(f"   Created GraphState with query: {state.original_query}")
        
        # Test the graph with correct parameters
        result = await chat_graph.execute(state)
        
        print(f"   ChatGraph result: {result}")
        
        if result.get('success') and result.get('response'):
            print("✅ ChatGraph test PASSED with correct parameters!")
            return True
        else:
            print("❌ ChatGraph test still failing")
            return False
            
    except Exception as e:
        print(f"❌ ChatGraph exception: {e}")
        traceback.print_exc()
        return False

async def test_fastapi_after_fix():
    """Test FastAPI endpoint after the fix"""
    print("🌐 Re-testing FastAPI endpoint...")
    
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/chat/complete",
                json={
                    "message": "Say exactly: FastAPI fixed and working",
                    "max_tokens": 20
                }
            )
            
            print(f"   Response status: {response.status_code}")
            result = response.json()
            print(f"   Response body: {result}")
            
            if response.status_code == 200 and result.get('success') and result.get('response'):
                print("✅ FastAPI endpoint test PASSED!")
                return True
            else:
                print("❌ FastAPI endpoint still failing")
                return False
                
    except Exception as e:
        print(f"❌ FastAPI endpoint exception: {e}")
        return False

async def main():
    print("🎯 QUICK FIX FOR CHATGRAPH PARAMETERS")
    print("====================================")
    
    # Test ChatGraph with correct parameters
    chat_success = await test_corrected_chat_graph()
    
    # Test FastAPI endpoint
    api_success = await test_fastapi_after_fix()
    
    print("\n📊 RESULTS AFTER FIX")
    print("===================")
    print(f"ChatGraph (corrected): {'✅ PASS' if chat_success else '❌ FAIL'}")
    print(f"FastAPI Endpoint:      {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if chat_success and api_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("🎯 The chat system is now working correctly!")
    elif chat_success and not api_success:
        print("\n🔧 ChatGraph is working, but FastAPI still has issues.")
        print("💡 The FastAPI endpoint may need to be restarted or there's a different issue.")
        print("🔄 Try: supervisorctl restart ai-search-app")
    else:
        print("\n⚠️ Issues still exist. Check the error messages above.")
    
    return chat_success and api_success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
