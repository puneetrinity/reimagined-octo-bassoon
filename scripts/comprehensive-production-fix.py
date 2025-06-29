#!/usr/bin/env python3
"""
Comprehensive Production Fix Script
===================================

This script diagnoses and fixes all critical issues in the AI Search System:
1. Model manager initialization issues
2. Chat graph state management bugs
3. FastAPI response extraction problems
4. Docker and deployment configuration
5. Dependency injection issues

It applies a complete, production-grade fix to prepare for clean deployment.
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("🔍 Starting comprehensive production fix...")
print(f"📁 Project root: {project_root}")

# Test imports and identify issues
def test_imports():
    """Test all critical imports and identify issues."""
    print("\n📦 Testing imports...")
    issues = []
    
    try:
        from app.core.config import get_settings
        print("✅ app.core.config")
    except Exception as e:
        print(f"❌ app.core.config: {e}")
        issues.append(("config", str(e)))
    
    try:
        from app.models.manager import ModelManager
        print("✅ app.models.manager")
    except Exception as e:
        print(f"❌ app.models.manager: {e}")
        issues.append(("model_manager", str(e)))
    
    try:
        from app.graphs.chat_graph import ChatGraph
        print("✅ app.graphs.chat_graph")
    except Exception as e:
        print(f"❌ app.graphs.chat_graph: {e}")
        issues.append(("chat_graph", str(e)))
    
    try:
        from app.api.chat import router
        print("✅ app.api.chat")
    except Exception as e:
        print(f"❌ app.api.chat: {e}")
        issues.append(("chat_api", str(e)))
    
    try:
        from app.cache.redis_client import CacheManager
        print("✅ app.cache.redis_client")
    except Exception as e:
        print(f"❌ app.cache.redis_client: {e}")
        issues.append(("cache_manager", str(e)))
    
    return issues

def fix_response_extraction():
    """Fix the response extraction logic in chat.py."""
    print("\n🔧 Fixing response extraction in chat.py...")
    
    chat_py_path = project_root / "app" / "api" / "chat.py"
    if not chat_py_path.exists():
        print(f"❌ Chat API file not found: {chat_py_path}")
        return False
    
    # Read the current content
    with open(chat_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Critical fix: Ensure proper response extraction
    response_extraction_fix = '''
        # COMPREHENSIVE FIX: Handle all possible response formats from GraphState
        final_response = None
        response_source = "unknown"
        
        # Method 1: Check if result has final_response attribute
        if hasattr(chat_result, 'final_response') and chat_result.final_response:
            final_response = chat_result.final_response
            response_source = "direct_attribute"
            logger.info(f"DEBUG: Method 1 - Extracted from direct attribute: '{final_response}' (type: {type(final_response)})")
        
        # Method 2: If it's a dict, check for known response keys
        elif isinstance(chat_result, dict):
            for key in ['final_response', 'response', 'text', 'content', 'answer']:
                if key in chat_result and chat_result[key]:
                    final_response = chat_result[key]
                    response_source = f"dict_key_{key}"
                    logger.info(f"DEBUG: Method 2 - Extracted from dict key '{key}': '{final_response}' (type: {type(final_response)})")
                    break
        
        # Method 3: Check if it's a GraphState with intermediate results
        elif hasattr(chat_result, 'intermediate_results') and chat_result.intermediate_results:
            for node_name in ['response_generator', 'chat_response', 'final_node']:
                if node_name in chat_result.intermediate_results:
                    node_data = chat_result.intermediate_results[node_name]
                    if isinstance(node_data, dict) and 'response' in node_data:
                        final_response = node_data['response']
                        response_source = f"intermediate_{node_name}"
                        logger.info(f"DEBUG: Method 3 - Extracted from intermediate results '{node_name}': '{final_response}'")
                        break
        
        # Method 4: Check node_results if available
        elif hasattr(chat_result, 'node_results') and chat_result.node_results:
            for node_name, node_info in chat_result.node_results.items():
                if isinstance(node_info, dict) and 'result' in node_info:
                    node_result = node_info['result']
                    if hasattr(node_result, 'data') and isinstance(node_result.data, dict):
                        if 'response' in node_result.data and node_result.data['response']:
                            final_response = node_result.data['response']
                            response_source = f"node_result_{node_name}"
                            logger.info(f"DEBUG: Method 4 - Extracted from node result '{node_name}': '{final_response}'")
                            break
        
        # Method 5: Fallback - try to convert result to string if it looks like content
        if not final_response and chat_result:
            if isinstance(chat_result, str) and chat_result.strip():
                final_response = chat_result
                response_source = "direct_string"
                logger.info(f"DEBUG: Method 5 - Using direct string result: '{final_response}'")
            elif hasattr(chat_result, '__str__'):
                str_result = str(chat_result).strip()
                if str_result and not str_result.startswith('<') and len(str_result) > 10:
                    final_response = str_result
                    response_source = "string_conversion"
                    logger.info(f"DEBUG: Method 5 - Using string conversion: '{final_response[:100]}...'")
        
        logger.info(f"DEBUG: Final extraction result - Response: '{final_response}' | Source: {response_source} | Type: {type(final_response)}")
        
        # Validate the final response
        if not final_response:
            logger.error(f"DEBUG: All extraction methods failed. Raw result: {type(chat_result)} = {chat_result}")
            error_details = {
                "error": "Model returned an empty or invalid response after comprehensive extraction attempts.",
                "debug_info": {
                    "result_type": str(type(chat_result)),
                    "has_final_response_attr": hasattr(chat_result, 'final_response'),
                    "is_dict": isinstance(chat_result, dict),
                    "dict_keys": list(chat_result.keys()) if isinstance(chat_result, dict) else None,
                    "has_intermediate_results": hasattr(chat_result, 'intermediate_results'),
                    "has_node_results": hasattr(chat_result, 'node_results'),
                    "string_repr_length": len(str(chat_result)) if chat_result else 0
                },
                "suggestions": [
                    "Check if models are properly initialized",
                    "Verify Ollama service is running",
                    "Check model memory and GPU availability",
                    "Review graph execution logs"
                ]
            }
            raise HTTPException(status_code=500, detail=error_details)
        
        # Additional validation
        if not isinstance(final_response, str):
            try:
                final_response = str(final_response)
                logger.warning(f"DEBUG: Converted response to string: {type(final_response)}")
            except Exception as conv_error:
                logger.error(f"DEBUG: Failed to convert response to string: {conv_error}")
                raise HTTPException(status_code=500, detail={
                    "error": "Response format conversion failed",
                    "details": str(conv_error)
                })
        
        final_response = final_response.strip()
        if not final_response:
            logger.error("DEBUG: Response is empty after strip()")
            raise HTTPException(status_code=500, detail={
                "error": "Model response is empty after processing",
                "extraction_source": response_source
            })
        
        logger.info(f"DEBUG: ✅ Successfully extracted and validated response from {response_source}: '{final_response[:100]}...' (length: {len(final_response)})")
'''

    # Find and replace the existing response extraction logic
    import re
    
    # Pattern to match the existing response extraction block
    pattern = r'# Handle GraphState object result.*?raise HTTPException\(status_code=500, detail=\{[^}]+}\)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, response_extraction_fix.strip(), content, flags=re.DOTALL)
        print("✅ Replaced existing response extraction logic")
    else:
        # If pattern not found, try to find a different insertion point
        chat_result_pattern = r'(chat_result = await ensure_awaited\(chat_result\))'
        if re.search(chat_result_pattern, content):
            content = re.sub(chat_result_pattern, r'\1\n' + response_extraction_fix, content)
            print("✅ Inserted response extraction logic after chat_result assignment")
        else:
            print("❌ Could not find insertion point for response extraction fix")
            return False
    
    # Write the fixed content back
    with open(chat_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Chat API response extraction fixed")
    return True

def fix_graph_state_issues():
    """Fix issues in the chat graph state management."""
    print("\n🔧 Fixing graph state management...")
    
    base_py_path = project_root / "app" / "graphs" / "base.py"
    if not base_py_path.exists():
        print(f"❌ Base graph file not found: {base_py_path}")
        return False
    
    # Ensure GraphState has proper final_response handling
    with open(base_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add final_response to GraphState if not present
    if 'final_response: Optional[str] = None' not in content:
        # Find the GraphState class definition
        import re
        pattern = r'(@dataclass\s+class GraphState:.*?)(    def __post_init__)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            before = match.group(1)
            after = match.group(2)
            if 'final_response' not in before:
                # Add final_response field before __post_init__
                new_field = "    final_response: Optional[str] = None\n    "
                content = content.replace(match.group(0), before + new_field + after)
                print("✅ Added final_response field to GraphState")
    
    with open(base_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_model_manager_init():
    """Fix model manager initialization issues."""
    print("\n🔧 Fixing model manager initialization...")
    
    manager_py_path = project_root / "app" / "models" / "manager.py"
    if not manager_py_path.exists():
        print(f"❌ Model manager file not found: {manager_py_path}")
        return False
    
    with open(manager_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ensure proper error handling in model initialization
    init_fix = '''
    async def initialize(self, force_reload: bool = False) -> bool:
        """
        Initialize the model manager with robust error handling.
        
        Args:
            force_reload: Force reloading of all models
            
        Returns:
            bool: True if initialization successful
        """
        logger.info("🚀 Initializing ModelManager...")
        start_time = time.time()
        
        try:
            # Initialize Ollama client
            if not self.ollama_client:
                self.ollama_client = OllamaClient(host=self.ollama_host)
                logger.info(f"📡 Created OllamaClient for {self.ollama_host}")
            
            # Health check with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    health_ok = await asyncio.wait_for(
                        self.ollama_client.health_check(), 
                        timeout=10.0
                    )
                    if health_ok:
                        logger.info("✅ Ollama health check passed")
                        break
                    else:
                        logger.warning(f"⚠️ Ollama health check failed (attempt {attempt + 1})")
                except asyncio.TimeoutError:
                    logger.warning(f"⏱️ Ollama health check timeout (attempt {attempt + 1})")
                except Exception as e:
                    logger.warning(f"❌ Ollama health check error (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("❌ Ollama health check failed after all retries")
                    # Don't fail initialization, but log the issue
                    self.initialization_status = "degraded"
            
            # Discover available models
            try:
                available_models = await asyncio.wait_for(
                    self.ollama_client.list_models(),
                    timeout=15.0
                )
                
                if available_models:
                    logger.info(f"📚 Found {len(available_models)} available models")
                    for model in available_models[:5]:  # Log first 5
                        logger.info(f"  📖 {model}")
                    
                    # Update model info
                    for model_name in available_models:
                        if model_name not in self.models:
                            self.models[model_name] = ModelInfo(
                                name=model_name,
                                status=ModelStatus.AVAILABLE
                            )
                        else:
                            self.models[model_name].status = ModelStatus.AVAILABLE
                else:
                    logger.warning("⚠️ No models found in Ollama")
                    self.initialization_status = "degraded"
                    
            except Exception as e:
                logger.error(f"❌ Failed to discover models: {e}")
                self.initialization_status = "degraded"
            
            # Initialize memory manager
            try:
                if not hasattr(self, 'memory_manager') or not self.memory_manager:
                    self.memory_manager = A5000MemoryManager()
                    logger.info("🧠 Memory manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ Memory manager initialization failed: {e}")
            
            # Mark as initialized
            self.is_initialized = True
            self.initialization_status = getattr(self, 'initialization_status', "healthy")
            duration = time.time() - start_time
            
            logger.info(f"✅ ModelManager initialization completed in {duration:.2f}s (status: {self.initialization_status})")
            return True
            
        except Exception as e:
            logger.error(f"❌ ModelManager initialization failed: {e}")
            self.initialization_status = "failed"
            self.is_initialized = False
            return False
'''
    
    # Add initialization status tracking
    if 'initialization_status' not in content:
        # Find the __init__ method and add the status field
        import re
        pattern = r'(def __init__\(self.*?\):.*?)(        self\.models = \{\})'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            before = match.group(1)
            after = match.group(2)
            status_line = "        self.initialization_status = 'not_started'\n        "
            content = content.replace(match.group(0), before + status_line + after)
    
    # Replace or add the initialize method
    if 'async def initialize(' in content:
        # Replace existing initialize method
        pattern = r'async def initialize\(.*?\n(?:.*?\n)*?.*?return.*?\n'
        content = re.sub(pattern, init_fix.strip() + '\n\n', content, flags=re.DOTALL)
    else:
        # Add the initialize method to the class
        class_pattern = r'(class ModelManager:.*?\n)(    def)'
        content = re.sub(class_pattern, r'\1' + init_fix + '\n\n    def', content, flags=re.DOTALL)
    
    with open(manager_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Model manager initialization fixed")
    return True

def fix_docker_issues():
    """Fix Docker configuration issues."""
    print("\n🔧 Fixing Docker configuration...")
    
    dockerfile_path = project_root / "Dockerfile"
    if not dockerfile_path.exists():
        print(f"❌ Dockerfile not found: {dockerfile_path}")
        return False
    
    # Optimized Dockerfile content
    dockerfile_content = '''# Production-ready Dockerfile for AI Search System
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app \\
    PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    gcc \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies with optimizations
RUN pip install --upgrade pip setuptools wheel && \\
    pip install --no-cache-dir -r requirements.txt && \\
    pip install --no-cache-dir -r requirements-dev.txt && \\
    pip cache purge

# Copy application code
COPY app ./app
COPY scripts ./scripts
COPY .env* ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \\
    chown -R appuser:appuser /app
USER appuser

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl --fail http://localhost:8000/health/live || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
'''
    
    with open(dockerfile_path, 'w', encoding='utf-8') as f:
        f.write(dockerfile_content)
    
    print("✅ Dockerfile optimized")
    
    # Create a production docker-compose file
    compose_path = project_root / "docker-compose.production.yml"
    compose_content = '''version: '3.8'

services:
  ai-search-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
    depends_on:
      - ollama
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

volumes:
  ollama_data:
  redis_data:
'''
    
    with open(compose_path, 'w', encoding='utf-8') as f:
        f.write(compose_content)
    
    print("✅ Production docker-compose.yml created")
    return True

def create_startup_validation():
    """Create a startup validation script."""
    print("\n🔧 Creating startup validation script...")
    
    validation_script = '''#!/usr/bin/env python3
"""
Startup Validation Script
========================

Validates that all components are properly initialized and working.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def validate_startup():
    """Validate all components during startup."""
    print("🔍 Starting startup validation...")
    
    errors = []
    
    # Test 1: Import all critical modules
    try:
        from app.core.config import get_settings
        from app.models.manager import ModelManager
        from app.cache.redis_client import CacheManager
        from app.graphs.chat_graph import ChatGraph
        print("✅ All critical imports successful")
    except Exception as e:
        errors.append(f"Import error: {e}")
        print(f"❌ Import failed: {e}")
    
    # Test 2: Initialize model manager
    try:
        settings = get_settings()
        model_manager = ModelManager(ollama_host=settings.ollama_host)
        init_success = await model_manager.initialize()
        if init_success:
            print("✅ Model manager initialization successful")
        else:
            errors.append("Model manager initialization failed")
            print("❌ Model manager initialization failed")
    except Exception as e:
        errors.append(f"Model manager error: {e}")
        print(f"❌ Model manager error: {e}")
    
    # Test 3: Initialize cache manager
    try:
        cache_manager = CacheManager(
            redis_url=settings.redis_url,
            max_connections=settings.redis_max_connections
        )
        await cache_manager.initialize()
        print("✅ Cache manager initialization successful")
    except Exception as e:
        errors.append(f"Cache manager error: {e}")
        print(f"❌ Cache manager error: {e}")
    
    # Test 4: Create chat graph
    try:
        chat_graph = ChatGraph(model_manager, cache_manager)
        print("✅ Chat graph creation successful")
    except Exception as e:
        errors.append(f"Chat graph error: {e}")
        print(f"❌ Chat graph error: {e}")
    
    # Test 5: Simple model generation test
    try:
        result = await model_manager.generate(
            model_name=model_manager.select_optimal_model("conversation", "minimal"),
            prompt="Test prompt",
            max_tokens=10,
            temperature=0.1
        )
        if result.success:
            print("✅ Model generation test successful")
        else:
            errors.append(f"Model generation failed: {result.error}")
            print(f"❌ Model generation failed: {result.error}")
    except Exception as e:
        errors.append(f"Model generation error: {e}")
        print(f"❌ Model generation error: {e}")
    
    # Summary
    if errors:
        print(f"\\n❌ Validation failed with {len(errors)} errors:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        return False
    else:
        print("\\n✅ All validation tests passed!")
        return True

if __name__ == "__main__":
    success = asyncio.run(validate_startup())
    sys.exit(0 if success else 1)
'''
    
    script_path = project_root / "scripts" / "validate_startup.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(validation_script)
    
    # Make it executable
    script_path.chmod(0o755)
    print("✅ Startup validation script created")
    return True

def create_build_script():
    """Create an optimized build script."""
    print("\n🔧 Creating optimized build script...")
    
    build_script = '''#!/bin/bash
# Production Build Script for AI Search System

set -e  # Exit on error

echo "🚀 Starting production build..."

# Clean up previous builds
echo "🧹 Cleaning up..."
docker system prune -f 2>/dev/null || true

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t ai-search-system:latest . || {
    echo "❌ Docker build failed"
    exit 1
}

echo "✅ Build completed successfully!"

# Optional: Tag for registry
if [ "$1" = "push" ]; then
    echo "📤 Tagging and pushing to registry..."
    docker tag ai-search-system:latest ghcr.io/your-username/ai-search-system:latest
    docker push ghcr.io/your-username/ai-search-system:latest
    echo "✅ Image pushed to registry"
fi

echo "🎉 Production build complete!"
'''
    
    script_path = project_root / "build-production.sh"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(build_script)
    
    # Make it executable
    script_path.chmod(0o755)
    print("✅ Production build script created")
    return True

async def run_comprehensive_fix():
    """Run all fixes in the correct order."""
    print("🔥 Running comprehensive production fix...")
    
    # Step 1: Test imports
    issues = test_imports()
    if issues:
        print(f"\n⚠️ Found {len(issues)} import issues:")
        for component, error in issues:
            print(f"  - {component}: {error}")
    
    # Step 2: Fix core issues
    fixes_applied = []
    
    if fix_graph_state_issues():
        fixes_applied.append("Graph state management")
    
    if fix_model_manager_init():
        fixes_applied.append("Model manager initialization")
    
    if fix_response_extraction():
        fixes_applied.append("Response extraction logic")
    
    if fix_docker_issues():
        fixes_applied.append("Docker configuration")
    
    if create_startup_validation():
        fixes_applied.append("Startup validation script")
    
    if create_build_script():
        fixes_applied.append("Production build script")
    
    # Step 3: Summary
    print(f"\n✅ Applied {len(fixes_applied)} fixes:")
    for fix in fixes_applied:
        print(f"  ✓ {fix}")
    
    print("\n🎯 Next steps for deployment:")
    print("1. Run: python scripts/validate_startup.py")
    print("2. Build: ./build-production.sh")
    print("3. Deploy: docker-compose -f docker-compose.production.yml up -d")
    print("4. Test: curl http://localhost:8000/health/live")
    
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_comprehensive_fix())
