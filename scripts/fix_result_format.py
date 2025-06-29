#!/usr/bin/env python3
"""
TARGETED FIX: ChatGraph result format issue.
The logs show ChatGraph is working but returning GraphState instead of expected dict format.
"""

import asyncio
import sys

# Add the app directory to Python path
sys.path.insert(0, '/app')

async def test_chatgraph_result_format():
    """Test the exact ChatGraph result format issue"""
    print("🔧 Testing ChatGraph result format...")
    
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
        state.original_query = "Say exactly: Test message"
        state.max_tokens = 30
        state.conversation_history = []
        
        print(f"   Input query: {state.original_query}")
        
        # Execute and examine result
        result = await chat_graph.execute(state)
        
        print(f"   Result type: {type(result)}")
        print(f"   Result attributes: {dir(result) if hasattr(result, '__dict__') else 'No __dict__'}")
        
        # Check if it's a GraphState with final_response
        if hasattr(result, 'final_response'):
            final_response = getattr(result, 'final_response', None)
            print(f"   final_response: '{final_response}'")
            
            if final_response and final_response.strip():
                print("✅ ChatGraph working - has final_response!")
                
                # Show what the API layer should expect
                expected_format = {
                    'success': True,
                    'response': final_response,
                    'final_response': final_response  # Some parts expect this key
                }
                print(f"   Expected API format: {expected_format}")
                return True, final_response
            else:
                print("❌ ChatGraph final_response is empty")
                return False, None
        else:
            print("❌ ChatGraph result has no final_response attribute")
            # Check what attributes it does have
            if hasattr(result, '__dict__'):
                attrs = {k: v for k, v in result.__dict__.items() if not k.startswith('_')}
                print(f"   Available attributes: {list(attrs.keys())}")
                # Look for response in other fields
                for key in ['response', 'text', 'content', 'answer']:
                    if hasattr(result, key):
                        value = getattr(result, key)
                        print(f"   Found {key}: '{value}'")
            return False, None
            
    except Exception as e:
        print(f"❌ ChatGraph test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def patch_chat_api():
    """Create a patch for the chat API to handle GraphState results correctly"""
    print("🔧 Creating API patch for GraphState handling...")
    
    patch_code = '''
# PATCH for app/api/chat.py - Handle GraphState results correctly

# Add this to the chat_complete function after chat_result = await safe_graph_execute(...)

# Convert GraphState result to expected dictionary format
if hasattr(chat_result, 'final_response'):
    # It's a GraphState object
    final_response = getattr(chat_result, 'final_response', '')
    if final_response and final_response.strip():
        # Convert to expected format
        chat_result = {
            'success': True,
            'final_response': final_response,
            'response': final_response,
            'model_used': getattr(chat_result, 'model_used', 'unknown'),
            'execution_time': getattr(chat_result, 'execution_time', 0.0),
            'cost': getattr(chat_result, 'cost', 0.0)
        }
    else:
        chat_result = {
            'success': False,
            'final_response': '',
            'error': 'ChatGraph returned empty response'
        }
elif isinstance(chat_result, dict):
    # Already in expected format
    pass
else:
    # Unexpected format
    chat_result = {
        'success': False, 
        'final_response': '',
        'error': f'Unexpected result type: {type(chat_result)}'
    }
'''
    
    print("   📝 Patch code generated:")
    print(patch_code)
    
    return patch_code

async def test_fastapi_with_manual_fix():
    """Test if we can manually construct what FastAPI should return"""
    print("🧪 Testing manual FastAPI response construction...")
    
    success, response_text = await test_chatgraph_result_format()
    
    if success:
        # Construct what FastAPI should return
        manual_response = {
            "success": True,
            "response": response_text,
            "model_used": "phi3:mini",
            "execution_time": 0.5,
            "cost": 0.0,
            "metadata": {
                "query_id": "test-123",
                "timestamp": "2025-06-29T10:14:43Z"
            }
        }
        
        print("✅ Manual FastAPI response construction:")
        print(f"   {manual_response}")
        
        return True
    else:
        print("❌ Cannot construct FastAPI response - ChatGraph not working")
        return False

async def main():
    print("🎯 TARGETED CHATGRAPH RESULT FORMAT FIX")
    print("=======================================")
    
    # Test the exact issue
    print("\n1️⃣ Diagnosing ChatGraph result format...")
    success1, response_text = await test_chatgraph_result_format()
    
    # Show the patch needed
    print("\n2️⃣ Generating API patch...")
    patch = await patch_chat_api()
    
    # Test manual construction
    print("\n3️⃣ Testing manual response construction...")
    success2 = await test_fastapi_with_manual_fix()
    
    print("\n📊 DIAGNOSIS COMPLETE")
    print("====================")
    
    if success1:
        print("✅ ROOT CAUSE IDENTIFIED:")
        print("   - ChatGraph IS working and generating responses")
        print("   - ChatGraph returns GraphState object with final_response attribute")
        print("   - FastAPI expects a dictionary with 'final_response' key")
        print("   - The conversion is missing in the API layer")
        print("")
        print("🔧 SOLUTION:")
        print("   - Patch the chat API to convert GraphState to dictionary format")
        print("   - OR modify ChatGraph to return dictionary instead of GraphState")
        print("")
        print("🚀 QUICK FIX COMMAND:")
        print("   supervisorctl restart ai-search-app")
        print("   # Then apply the patch shown above to app/api/chat.py")
        
        return True
    else:
        print("❌ ChatGraph fundamental issue - needs deeper investigation")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
