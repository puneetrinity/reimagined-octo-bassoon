#!/usr/bin/env python3
"""
Fix API Result Format - Convert GraphState to dict in chat endpoint (RunPod Version)
This script patches the FastAPI chat endpoint to properly handle GraphState results
"""

import os
import sys

def patch_chat_api():
    """Patch the chat API to convert GraphState to dict format"""
    
    api_file = "/app/api/chat.py"
    
    print("🔧 PATCHING CHAT API RESULT FORMAT")
    print("=" * 50)
    
    if not os.path.exists(api_file):
        print(f"❌ File not found: {api_file}")
        return False
    
    # Read current content
    with open(api_file, 'r') as f:
        content = f.read()
    
    print(f"📖 Reading {api_file}")
    
    # Check if already patched
    if "Handle GraphState object result" in content:
        print("✅ Already patched! Skipping.")
        return True
    
    # Find and replace the result handling section
    if "if not result or not hasattr(result, 'final_response') or not result.final_response:" in content:
        print("✅ Found target pattern for replacement")
        
        old_pattern = """        if not result or not hasattr(result, 'final_response') or not result.final_response:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Model returned an empty or invalid response. This may be due to model initialization issues.",
                    "suggestions": [
                        "Try rephrasing your question.",
                        "Check model health and logs."
                    ]
                }
            )
        
        return ChatResponse(
            response=result.final_response,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat()
        )"""
        
        new_pattern = """        # Handle GraphState object result
        final_response = None
        if hasattr(result, 'final_response'):
            final_response = result.final_response
            logger.debug(f"Extracted final_response: {final_response}")
        elif isinstance(result, dict):
            final_response = result.get('final_response') or result.get('response')
            logger.debug(f"Dict result, extracted: {final_response}")
        else:
            logger.error(f"Unexpected result type: {type(result)}")
        
        if not final_response:
            logger.error(f"No final_response found in result: {result}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Model returned an empty or invalid response. This may be due to model initialization issues.",
                    "suggestions": [
                        "Try rephrasing your question.",
                        "Check model health and logs."
                    ]
                }
            )
        
        return ChatResponse(
            response=final_response,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat()
        )"""
        
        # Apply the patch
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            print("✅ Applied result format patch")
        else:
            print("⚠️  Exact pattern not found, searching for alternative...")
            
            # Try to find just the result check and response return
            import re
            
            # More flexible pattern matching
            pattern = r'(if not result.*?final_response.*?\n.*?raise HTTPException.*?}\s*\)\s*)(.*?return ChatResponse.*?final_response.*?\))'
            
            match = re.search(pattern, content, re.DOTALL)
            if match:
                replacement = """        # Handle GraphState object result
        final_response = None
        if hasattr(result, 'final_response'):
            final_response = result.final_response
            logger.debug(f"Extracted final_response: {final_response}")
        elif isinstance(result, dict):
            final_response = result.get('final_response') or result.get('response')
            logger.debug(f"Dict result, extracted: {final_response}")
        else:
            logger.error(f"Unexpected result type: {type(result)}")
        
        if not final_response:
            logger.error(f"No final_response found in result: {result}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Model returned an empty or invalid response. This may be due to model initialization issues.",
                    "suggestions": [
                        "Try rephrasing your question.",
                        "Check model health and logs."
                    ]
                }
            )
        
        return ChatResponse(
            response=final_response,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat()
        )"""
                
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                print("✅ Applied alternative patch")
            else:
                print("❌ Could not find pattern to patch")
                return False
    else:
        print("❌ Target pattern not found in file")
        return False
    
    # Write the patched content
    try:
        with open(api_file, 'w') as f:
            f.write(content)
        print(f"✅ Successfully patched {api_file}")
        return True
    except Exception as e:
        print(f"❌ Error writing patch: {e}")
        return False

def main():
    """Main execution"""
    print("🎯 FIXING API RESULT FORMAT (RUNPOD)")
    print("=" * 40)
    
    success = patch_chat_api()
    
    if success:
        print("\n✅ PATCH APPLIED SUCCESSFULLY")
        print("🔄 Restart FastAPI service with:")
        print("   supervisorctl restart ai-search-app")
    else:
        print("\n❌ PATCH FAILED")
        print("🔍 Check the error messages above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
