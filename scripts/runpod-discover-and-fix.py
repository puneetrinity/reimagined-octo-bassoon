#!/usr/bin/env python3
"""
RunPod Path Discovery and API Fix
This script finds the correct paths and applies the API result format fix
"""

import os
import sys
import glob

def find_chat_api_file():
    """Find the chat.py file in the current setup"""
    
    possible_paths = [
        "/app/api/chat.py",
        "/workspace/app/api/chat.py", 
        "/workspace/api/chat.py",
        "/workspace/src/api/chat.py",
        "./app/api/chat.py",
        "./api/chat.py"
    ]
    
    print("🔍 SEARCHING FOR CHAT API FILE")
    print("=" * 40)
    
    for path in possible_paths:
        print(f"📂 Checking: {path}")
        if os.path.exists(path):
            print(f"✅ Found: {path}")
            return path
    
    # Use glob to search more broadly
    print("\n🔍 Searching with glob patterns...")
    patterns = [
        "**/api/chat.py",
        "**/chat.py",
        "app/**/chat.py"
    ]
    
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            print(f"✅ Found via pattern '{pattern}': {matches}")
            return matches[0]
    
    print("❌ Chat API file not found!")
    return None

def patch_chat_api(api_file):
    """Patch the chat API to convert GraphState to dict format"""
    
    print(f"\n🔧 PATCHING CHAT API: {api_file}")
    print("=" * 50)
    
    # Read current content
    with open(api_file, 'r') as f:
        content = f.read()
    
    print(f"📖 Reading {api_file} ({len(content)} characters)")
    
    # Check if already patched
    if "Handle GraphState object result" in content:
        print("✅ Already patched! Skipping.")
        return True
    
    # Look for the chat function
    if "async def chat(" not in content:
        print("❌ Chat function not found")
        return False
    
    print("✅ Found chat function")
    
    # Look for result handling
    if "result.final_response" in content:
        print("✅ Found result.final_response usage")
        
        # Find the exact pattern and replace it
        lines = content.split('\n')
        patched_lines = []
        i = 0
        patched = False
        
        while i < len(lines):
            line = lines[i]
            patched_lines.append(line)
            
            # Look for the result checking pattern
            if "if not result" in line and "final_response" in line:
                print("✅ Found result checking pattern at line", i+1)
                
                # Replace this section with our improved version
                # Skip the old result checking logic
                while i < len(lines) and "return ChatResponse(" not in lines[i]:
                    i += 1
                
                # Skip the old ChatResponse too
                while i < len(lines) and lines[i].strip() != ")":
                    i += 1
                
                # Insert our new logic
                patched_lines.pop()  # Remove the "if not result" line we just added
                patched_lines.extend([
                    "        # Handle GraphState object result",
                    "        final_response = None",
                    "        if hasattr(result, 'final_response'):",
                    "            final_response = result.final_response",
                    "            logger.debug(f\"Extracted final_response: {final_response}\")",
                    "        elif isinstance(result, dict):",
                    "            final_response = result.get('final_response') or result.get('response')",
                    "            logger.debug(f\"Dict result, extracted: {final_response}\")",
                    "        else:",
                    "            logger.error(f\"Unexpected result type: {type(result)}\")",
                    "",
                    "        if not final_response:",
                    "            logger.error(f\"No final_response found in result: {result}\")",
                    "            raise HTTPException(",
                    "                status_code=500,",
                    "                detail={",
                    "                    \"error\": \"Model returned an empty or invalid response. This may be due to model initialization issues.\",",
                    "                    \"suggestions\": [",
                    "                        \"Try rephrasing your question.\",",
                    "                        \"Check model health and logs.\"",
                    "                    ]",
                    "                }",
                    "            )",
                    "",
                    "        return ChatResponse(",
                    "            response=final_response,",
                    "            session_id=session_id,",
                    "            timestamp=datetime.utcnow().isoformat()",
                    "        )"
                ])
                patched = True
                break
            
            i += 1
        
        if patched:
            content = '\n'.join(patched_lines)
            print("✅ Applied patch successfully")
        else:
            print("❌ Could not find pattern to patch")
            return False
    else:
        print("❌ result.final_response not found in file")
        return False
    
    # Write the patched content
    try:
        with open(api_file, 'w') as f:
            f.write(content)
        print(f"✅ Successfully wrote patched content to {api_file}")
        return True
    except Exception as e:
        print(f"❌ Error writing patch: {e}")
        return False

def main():
    """Main execution"""
    print("🎯 RUNPOD PATH DISCOVERY AND API FIX")
    print("=" * 40)
    
    # Find the chat API file
    api_file = find_chat_api_file()
    
    if not api_file:
        print("\n❌ CHAT API FILE NOT FOUND")
        print("🔍 Please check your directory structure")
        print("📂 Current working directory:", os.getcwd())
        print("📁 Directory contents:")
        try:
            for item in os.listdir('.'):
                print(f"   {item}")
        except:
            pass
        return False
    
    # Apply the patch
    success = patch_chat_api(api_file)
    
    if success:
        print(f"\n✅ PATCH APPLIED SUCCESSFULLY to {api_file}")
        print("🔄 Now restart FastAPI service:")
        print("   supervisorctl restart ai-search-app")
    else:
        print(f"\n❌ PATCH FAILED for {api_file}")
        print("🔍 Check the error messages above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
