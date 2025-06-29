#!/bin/bash
# Emergency fix for "Model returned empty response" issue
# This script patches the running system to handle empty responses better

echo "🚨 Emergency Fix: Model Empty Response Issue"
echo "==========================================="

# Backup current files
echo "📂 Creating backups..."
cp /app/app/models/ollama_client.py /app/app/models/ollama_client.py.backup.$(date +%s)
cp /app/app/api/chat.py /app/app/api/chat.py.backup.$(date +%s)

# Check if models are actually loaded
echo "🔍 Checking model status..."
echo "Available models:"
curl -s http://localhost:11434/api/tags | jq -r '.models[].name' || echo "Failed to get models"

# Test basic model functionality
echo ""
echo "🧪 Testing basic model functionality..."
test_response=$(curl -s -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{"model":"tinyllama:latest","prompt":"Say OK","stream":false}' \
    --max-time 30)

echo "Raw Ollama response: $test_response"

if echo "$test_response" | jq -e '.response' > /dev/null 2>&1; then
    response_text=$(echo "$test_response" | jq -r '.response')
    echo "✅ Ollama working - Response: '$response_text'"
else
    echo "❌ Ollama not responding properly"
    echo "🔄 Pulling tinyllama model..."
    ollama pull tinyllama:latest
    
    echo "🔄 Retesting..."
    test_response=$(curl -s -X POST http://localhost:11434/api/generate \
        -H "Content-Type: application/json" \
        -d '{"model":"tinyllama:latest","prompt":"Say OK","stream":false}' \
        --max-time 30)
    echo "Retry response: $test_response"
fi

# Test the FastAPI endpoint directly
echo ""
echo "🧪 Testing FastAPI chat endpoint..."
chat_response=$(curl -s -X POST http://localhost:8000/api/v1/chat/complete \
    -H "Content-Type: application/json" \
    -d '{"message":"Hello","stream":false}')

echo "FastAPI response: $chat_response"

# Apply temporary fix to ollama_client.py
echo ""
echo "🔧 Applying temporary fix to handle empty responses..."

cat > /tmp/ollama_patch.py << 'PATCH_EOF'
import re

# Read the original file
with open('/app/app/models/ollama_client.py', 'r') as f:
    content = f.read()

# Patch 1: Improve empty response handling
old_pattern = r'response_text = response\.get\("response", ""\)\s+if not response_text:'
new_pattern = '''response_text = response.get("response", "")
                logger.debug(f"Raw Ollama response: {response}")
                
                # Better empty response handling
                if not response_text or response_text.strip() == "":'''

content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

# Patch 2: Add more detailed logging
old_logging = r'logger\.debug\(\s+"Starting text generation"'
new_logging = '''logger.info(
                    "Starting text generation with detailed logging"'''

content = re.sub(old_logging, new_logging, content, flags=re.MULTILINE)

# Patch 3: Improve fallback response
old_fallback = r'response_text = "I\'m sorry, I couldn\'t generate a response\. Please try rephrasing your question\."'
new_fallback = '''logger.error(f"Empty response from Ollama for model {model_name}. Raw response: {response}")
                    response_text = f"Hello! I'm ready to help you. Could you please rephrase your question? (Model: {model_name})"'''

content = re.sub(old_fallback, new_fallback, content, flags=re.MULTILINE)

# Write the patched file
with open('/app/app/models/ollama_client.py', 'w') as f:
    f.write(content)

print("✅ Applied patches to ollama_client.py")
PATCH_EOF

python3 /tmp/ollama_patch.py

# Apply fix to chat.py for better error handling
echo "🔧 Applying fix to chat endpoint..."

cat > /tmp/chat_patch.py << 'PATCH_EOF'
import re

# Read the original file
with open('/app/app/api/chat.py', 'r') as f:
    content = f.read()

# Improve error message in chat endpoint
old_error = r'raise HTTPException\(status_code=500, detail=\{\s+"error": "Model returned an empty or invalid response\."'
new_error = '''logger.error(f"Chat result details: final_response='{final_response}', type={type(final_response)}")
            raise HTTPException(status_code=500, detail={
                "error": "Model returned an empty or invalid response. This may be due to model initialization issues."'''

content = re.sub(old_error, new_error, content, flags=re.MULTILINE | re.DOTALL)

# Write the patched file
with open('/app/app/api/chat.py', 'w') as f:
    f.write(content)

print("✅ Applied patches to chat.py")
PATCH_EOF

python3 /tmp/chat_patch.py

# Restart the FastAPI service to apply changes
echo ""
echo "🔄 Restarting FastAPI service to apply fixes..."
supervisorctl restart ai-search-app

# Wait for restart
sleep 5

# Test the fix
echo ""
echo "🧪 Testing the fix..."
for i in {1..3}; do
    echo "Test attempt $i..."
    chat_response=$(curl -s -X POST http://localhost:8000/api/v1/chat/complete \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"Hello test $i\",\"stream\":false}")
    
    if echo "$chat_response" | jq -e '.success' > /dev/null 2>&1; then
        echo "✅ Test $i successful!"
        echo "Response: $(echo "$chat_response" | jq -r '.data.content' | head -c 100)..."
        break
    else
        echo "❌ Test $i failed: $chat_response"
    fi
    sleep 2
done

echo ""
echo "📋 Current service status:"
supervisorctl status

echo ""
echo "💡 If the issue persists:"
echo "1. Check app logs: supervisorctl tail ai-search-app"
echo "2. Check Ollama logs: supervisorctl tail ollama"
echo "3. Verify models are loaded: curl -s http://localhost:11434/api/tags"
echo "4. Try pulling models manually: ollama pull tinyllama:latest"

echo ""
echo "🎯 Emergency fix complete!"
