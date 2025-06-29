#!/usr/bin/env python3
"""
Comprehensive RunPod Fix - Find and patch API files anywhere
This script searches the entire filesystem for API files and applies fixes
"""

import os
import sys
import subprocess

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def find_api_files():
    """Search for API files using find command"""
    
    print("🔍 COMPREHENSIVE API FILE SEARCH")
    print("=" * 40)
    
    # Search for Python files containing 'chat' or in 'api' directories
    commands = [
        "find / -name 'chat.py' 2>/dev/null",
        "find / -path '*/api/*.py' 2>/dev/null | head -20",
        "find / -name '*.py' -exec grep -l 'ChatResponse\\|async def chat' {} \\; 2>/dev/null",
        "find /app -name '*.py' 2>/dev/null | head -10",
        "find /workspace -name '*.py' 2>/dev/null | head -10"
    ]
    
    found_files = []
    
    for cmd in commands:
        print(f"\n🔍 Running: {cmd}")
        stdout, stderr, code = run_command(cmd)
        
        if stdout.strip():
            lines = stdout.strip().split('\n')
            for line in lines:
                if line.strip() and line not in found_files:
                    found_files.append(line.strip())
                    print(f"✅ Found: {line.strip()}")
        else:
            print("❌ No results")
    
    return found_files

def check_file_for_chat_api(filepath):
    """Check if a file contains the chat API function"""
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Look for chat API indicators
        indicators = [
            'async def chat(',
            'ChatResponse',
            '/api/v1/chat/complete',
            'result.final_response'
        ]
        
        score = sum(1 for indicator in indicators if indicator in content)
        
        if score >= 2:
            print(f"✅ {filepath} - Strong match (score: {score})")
            return True, content
        elif score >= 1:
            print(f"⚠️  {filepath} - Possible match (score: {score})")
            return False, content
        else:
            print(f"❌ {filepath} - No match (score: {score})")
            return False, None
            
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return False, None

def patch_chat_api_content(content):
    """Apply the patch to file content"""
    
    # Check if already patched
    if "Handle GraphState object result" in content:
        print("✅ Already patched!")
        return content, True
    
    # Look for the problematic pattern
    if "result.final_response" not in content:
        print("❌ No result.final_response found - wrong file")
        return content, False
    
    print("✅ Found result.final_response - applying patch...")
    
    # Replace the result handling logic
    lines = content.split('\n')
    patched_lines = []
    i = 0
    patched = False
    
    while i < len(lines):
        line = lines[i]
        
        # Look for the result checking pattern
        if ("if not result" in line and ("final_response" in line or "hasattr" in line)) or \
           ("not result.final_response" in line):
            
            print(f"✅ Found result check at line {i+1}: {line.strip()}")
            
            # Skip until we find the HTTPException or return statement
            start_line = i
            while i < len(lines):
                if "HTTPException" in lines[i] or "return ChatResponse" in lines[i]:
                    break
                i += 1
            
            # Skip the entire old logic block
            if i < len(lines) and "HTTPException" in lines[i]:
                # Skip HTTPException block
                while i < len(lines) and ")" not in lines[i]:
                    i += 1
                i += 1  # Skip the closing parenthesis
            
            # Skip return ChatResponse block
            if i < len(lines) and "return ChatResponse" in lines[i]:
                while i < len(lines) and lines[i].strip() != ")":
                    i += 1
                i += 1  # Skip the closing parenthesis
            
            # Insert our new logic at the start position
            indent = "        "  # Assuming 8-space indentation
            new_lines = [
                f"{indent}# Handle GraphState object result",
                f"{indent}final_response = None",
                f"{indent}if hasattr(result, 'final_response'):",
                f"{indent}    final_response = result.final_response",
                f"{indent}    logger.debug(f\"Extracted final_response: {{final_response}}\")",
                f"{indent}elif isinstance(result, dict):",
                f"{indent}    final_response = result.get('final_response') or result.get('response')",
                f"{indent}    logger.debug(f\"Dict result, extracted: {{final_response}}\")",
                f"{indent}else:",
                f"{indent}    logger.error(f\"Unexpected result type: {{type(result)}}\")",
                f"{indent}",
                f"{indent}if not final_response:",
                f"{indent}    logger.error(f\"No final_response found in result: {{result}}\")",
                f"{indent}    raise HTTPException(",
                f"{indent}        status_code=500,",
                f"{indent}        detail={{",
                f"{indent}            \"error\": \"Model returned an empty or invalid response. This may be due to model initialization issues.\",",
                f"{indent}            \"suggestions\": [",
                f"{indent}                \"Try rephrasing your question.\",",
                f"{indent}                \"Check model health and logs.\"",
                f"{indent}            ]",
                f"{indent}        }}",
                f"{indent}    )",
                f"{indent}",
                f"{indent}return ChatResponse(",
                f"{indent}    response=final_response,",
                f"{indent}    session_id=session_id,",
                f"{indent}    timestamp=datetime.utcnow().isoformat()",
                f"{indent})"
            ]
            
            patched_lines.extend(new_lines)
            patched = True
            break
        else:
            patched_lines.append(line)
        
        i += 1
    
    if patched:
        print("✅ Patch applied successfully")
        return '\n'.join(patched_lines), True
    else:
        print("❌ Could not find pattern to patch")
        return content, False

def main():
    """Main execution"""
    print("🎯 COMPREHENSIVE RUNPOD API FIX")
    print("=" * 35)
    
    # First, find potential API files
    api_files = find_api_files()
    
    if not api_files:
        print("\n❌ NO API FILES FOUND")
        print("🔍 Let's check common locations manually...")
        
        # Manual check of common locations
        manual_paths = [
            "/app",
            "/workspace/app", 
            "/usr/src/app",
            "/code",
            "/src"
        ]
        
        for path in manual_paths:
            if os.path.exists(path):
                print(f"✅ {path} exists - exploring...")
                stdout, _, _ = run_command(f"find {path} -name '*.py' | head -10")
                if stdout.strip():
                    for line in stdout.strip().split('\n'):
                        api_files.append(line.strip())
        
        if not api_files:
            print("❌ Still no Python files found!")
            return False
    
    print(f"\n🔍 ANALYZING {len(api_files)} FILES FOR CHAT API")
    print("=" * 50)
    
    # Check each file for chat API content
    chat_api_file = None
    for filepath in api_files:
        print(f"\n📂 Checking: {filepath}")
        is_chat_api, content = check_file_for_chat_api(filepath)
        
        if is_chat_api:
            chat_api_file = filepath
            break
    
    if not chat_api_file:
        print("\n❌ NO CHAT API FILE FOUND")
        print("🔍 The chat API might be in a different format or location")
        return False
    
    print(f"\n🔧 PATCHING CHAT API: {chat_api_file}")
    print("=" * 50)
    
    # Read the file content
    try:
        with open(chat_api_file, 'r') as f:
            original_content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Apply the patch
    patched_content, success = patch_chat_api_content(original_content)
    
    if not success:
        print("❌ Patch failed")
        return False
    
    # Write the patched content
    try:
        with open(chat_api_file, 'w') as f:
            f.write(patched_content)
        print(f"✅ Successfully patched {chat_api_file}")
        
        print("\n🔄 NOW RESTART THE SERVICE:")
        print("   supervisorctl restart ai-search-app")
        print("\n🧪 THEN TEST:")
        print("   curl -X POST http://localhost:8000/api/v1/chat/complete \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"message\": \"Hello test\"}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing patched file: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
