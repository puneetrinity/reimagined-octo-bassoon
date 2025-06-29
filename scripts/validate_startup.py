#!/usr/bin/env python3
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
        from app.models.manager import TaskType, QualityLevel
        optimal_model = model_manager.select_optimal_model(
            TaskType.CONVERSATION, 
            QualityLevel.MINIMAL
        )
        result = await model_manager.generate(
            model_name=optimal_model,
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
        print(f"\n❌ Validation failed with {len(errors)} errors:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        return False
    else:
        print("\n✅ All validation tests passed!")
        return True

if __name__ == "__main__":
    success = asyncio.run(validate_startup())
    sys.exit(0 if success else 1)
