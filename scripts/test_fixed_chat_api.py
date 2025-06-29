#!/usr/bin/env python3
"""
Test Chat API After Result Format Fix
This script tests the chat endpoint after applying the result format patch
"""

import requests
import json
import time

def test_chat_endpoint():
    """Test the chat endpoint with proper request format"""
    
    url = "http://localhost:8000/api/v1/chat/complete"
    
    test_cases = [
        {"message": "Hello, how are you?"},
        {"message": "What is artificial intelligence?"},
        {"message": "Explain Python programming"},
    ]
    
    print("🧪 TESTING CHAT ENDPOINT AFTER FIX")
    print("=" * 45)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📤 Test {i}: {test_case['message']}")
        
        try:
            response = requests.post(
                url,
                json=test_case,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Success! Response: {data.get('response', 'No response field')[:100]}...")
                    if 'session_id' in data:
                        print(f"🆔 Session ID: {data['session_id']}")
                    if 'timestamp' in data:
                        print(f"⏰ Timestamp: {data['timestamp']}")
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response: {response.text[:200]}")
            else:
                print(f"❌ Error: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        # Small delay between requests
        if i < len(test_cases):
            time.sleep(2)
    
    print(f"\n🏁 Test completed!")

def main():
    """Main execution"""
    print("🎯 TESTING FIXED CHAT API")
    print("=" * 30)
    
    test_chat_endpoint()

if __name__ == "__main__":
    main()
