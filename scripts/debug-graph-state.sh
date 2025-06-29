#!/bin/bash

echo "🔍 DETAILED GRAPH STATE DEBUGGER"
echo "================================"

# Create a comprehensive script to debug exactly what's happening in the chat graph
cat > /tmp/debug_graph_execution.py << 'EOF'
import asyncio
import sys
import logging
import json
sys.path.insert(0, '/app')

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_complete_flow():
    """Debug the complete chat flow step by step"""
    
    print("🚀 Starting comprehensive graph execution debug")
    
    try:
        # Step 1: Test ModelManager
        print("\n📋 Step 1: Testing ModelManager")
        from app.models.manager import ModelManager
        
        model_manager = ModelManager()
        await model_manager.initialize()
        
        models = await model_manager.get_available_models()
        print(f"✅ Available models: {models}")
        
        # Test direct model query
        test_query = "What is 2+2?"
        print(f"🧪 Testing direct model query: '{test_query}'")
        
        direct_response = await model_manager.generate_response(
            prompt=test_query,
            model_name="phi3:mini"
        )
        print(f"✅ Direct model response: {direct_response}")
        
        # Step 2: Test ChatGraph initialization
        print("\n📋 Step 2: Testing ChatGraph")
        from app.graphs.chat_graph import ChatGraph
        from app.graphs.base import GraphState
        
        chat_graph = ChatGraph(model_manager)
        print("✅ ChatGraph created successfully")
        
        # Step 3: Test graph state creation
        print("\n📋 Step 3: Testing GraphState creation")
        state = GraphState(
            query=test_query,
            query_id="debug-test-123",
            conversation_id="debug-conv-456"
        )
        print(f"✅ GraphState created: {state}")
        print(f"   - Query: {state.query}")
        print(f"   - Query ID: {state.query_id}")
        print(f"   - Conversation ID: {state.conversation_id}")
        
        # Step 4: Execute graph with detailed monitoring
        print("\n📋 Step 4: Executing ChatGraph with monitoring")
        
        # Add debug hooks to monitor execution
        class DebugChatGraph(ChatGraph):
            async def execute(self, state):
                print(f"🔄 Starting graph execution with state: {state}")
                
                # Call each node manually to see where it fails
                try:
                    # Node 1: Process Query
                    print("🔄 Node 1: Processing query...")
                    state = await self.process_query_node(state)
                    print(f"✅ Query processed. State: {state}")
                    
                    # Node 2: Generate Response
                    print("🔄 Node 2: Generating response...")
                    state = await self.generate_response_node(state)
                    print(f"✅ Response generated. State: {state}")
                    
                    # Node 3: Finalize
                    print("🔄 Node 3: Finalizing...")
                    state = await self.finalize_response_node(state)
                    print(f"✅ Response finalized. Final state: {state}")
                    
                    return state
                    
                except Exception as e:
                    print(f"❌ Error in graph execution: {e}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")
                    raise
        
        debug_graph = DebugChatGraph(model_manager)
        result = await debug_graph.execute(state)
        
        print(f"\n🎯 FINAL RESULT:")
        print(f"   - Type: {type(result)}")
        print(f"   - Attributes: {dir(result)}")
        
        if hasattr(result, 'final_response'):
            print(f"   - final_response: '{result.final_response}'")
        if hasattr(result, 'response'):
            print(f"   - response: '{result.response}'")
        if hasattr(result, '__dict__'):
            print(f"   - Full state: {result.__dict__}")
        
        # Step 5: Test the actual endpoint logic
        print("\n📋 Step 5: Testing endpoint response extraction")
        
        # Simulate what the endpoint does
        final_response = None
        
        if hasattr(result, 'final_response') and result.final_response:
            final_response = result.final_response
        elif hasattr(result, 'response') and result.response:
            final_response = result.response
        elif isinstance(result, dict) and 'final_response' in result:
            final_response = result['final_response']
        elif isinstance(result, dict) and 'response' in result:
            final_response = result['response']
        
        print(f"🎯 Extracted final_response: '{final_response}'")
        
        if not final_response or final_response.lower() in ['missing', 'none', '']:
            print("❌ Final response is empty or invalid!")
            print("🔧 This is the root cause of the 'Model returned an empty or invalid response' error")
        else:
            print("✅ Final response is valid and ready to return")
        
    except Exception as e:
        print(f"❌ Critical error in debug flow: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(debug_complete_flow())
EOF

echo "🧪 Running detailed graph execution debug..."
cd /app && python3 /tmp/debug_graph_execution.py

echo -e "\n🔍 Checking current graph implementations..."

# Check what's actually in the chat graph
echo "📂 Chat Graph Implementation:"
ls -la /app/app/graphs/
echo -e "\n📄 Chat Graph Content (first 50 lines):"
head -50 /app/app/graphs/chat_graph.py

echo -e "\n📄 Base Graph Content (first 30 lines):"
head -30 /app/app/graphs/base.py

echo -e "\n🔍 Current FastAPI logs (last 20 lines):"
tail -20 /workspace/logs/app.out.log

echo -e "\n✅ Graph state debug complete!"
EOF
