#!/usr/bin/env python3
"""
RunPod Directory Discovery
This script explores the directory structure to find the correct paths
"""

import os
import sys

def explore_directory(path="/workspace", max_depth=3, current_depth=0):
    """Recursively explore directory structure"""
    
    if current_depth > max_depth:
        return
    
    try:
        items = os.listdir(path)
        items.sort()
        
        for item in items:
            item_path = os.path.join(path, item)
            indent = "  " * current_depth
            
            if os.path.isdir(item_path):
                print(f"{indent}📁 {item}/")
                if item in ['app', 'api', 'src'] or current_depth < 2:
                    explore_directory(item_path, max_depth, current_depth + 1)
            else:
                if item.endswith('.py') and 'chat' in item.lower():
                    print(f"{indent}🐍 {item} ⭐")
                elif item.endswith(('.py', '.sh', '.conf')):
                    print(f"{indent}📄 {item}")
                else:
                    print(f"{indent}📄 {item}")
                    
    except PermissionError:
        print(f"{indent}❌ Permission denied")
    except Exception as e:
        print(f"{indent}❌ Error: {e}")

def find_chat_files():
    """Find all files with 'chat' in the name"""
    
    print("\n🔍 SEARCHING FOR CHAT-RELATED FILES")
    print("=" * 40)
    
    import glob
    
    patterns = [
        "**/chat.py",
        "**/chat_*.py", 
        "**/*chat*.py",
        "**/api/*.py"
    ]
    
    found_files = []
    
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        for match in matches:
            if match not in found_files:
                found_files.append(match)
                print(f"✅ Found: {match}")
    
    return found_files

def main():
    """Main execution"""
    print("🎯 RUNPOD DIRECTORY DISCOVERY")
    print("=" * 30)
    
    print(f"📂 Current working directory: {os.getcwd()}")
    print(f"🏠 Home directory: {os.path.expanduser('~')}")
    
    print("\n📁 DIRECTORY STRUCTURE")
    print("=" * 25)
    explore_directory()
    
    print("\n🔍 CHAT FILE SEARCH")
    print("=" * 20)
    chat_files = find_chat_files()
    
    if not chat_files:
        print("❌ No chat files found")
        print("\n🔍 Let's check some common locations manually:")
        
        common_paths = [
            "/workspace/app",
            "/workspace/src", 
            "/workspace/api",
            "/app",
            "/src"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                print(f"✅ {path} exists")
                try:
                    contents = os.listdir(path)
                    for item in contents:
                        if 'api' in item.lower() or 'chat' in item.lower():
                            print(f"   📁 {item}")
                except:
                    pass
            else:
                print(f"❌ {path} does not exist")
    
    print(f"\n🏁 Discovery completed!")

if __name__ == "__main__":
    main()
