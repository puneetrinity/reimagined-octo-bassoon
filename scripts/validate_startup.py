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
    """Validate basic component loading during startup."""
    print("🔍 Starting basic startup validation...")
    
    errors = []
    warnings = []
    
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
        return False  # Can't continue without imports
    
    # Test 2: Configuration loading
    try:
        settings = get_settings()
        print(f"✅ Configuration loaded (environment: {settings.environment})")
    except Exception as e:
        errors.append(f"Configuration error: {e}")
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test 3: Basic component creation (no initialization)
    try:
        model_manager = ModelManager(ollama_host=settings.ollama_host)
        print("✅ ModelManager instance created")
    except Exception as e:
        warnings.append(f"ModelManager creation warning: {e}")
        print(f"⚠️ ModelManager creation warning: {e}")
    
    try:
        cache_manager = CacheManager(
            redis_url=settings.redis_url,
            max_connections=settings.redis_max_connections
        )
        print("✅ CacheManager instance created")
    except Exception as e:
        warnings.append(f"CacheManager creation warning: {e}")
        print(f"⚠️ CacheManager creation warning: {e}")
    
    # Test 4: Check environment variables
    import os
    required_vars = ["OLLAMA_HOST", "REDIS_URL", "AI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        warnings.append(f"Missing environment variables: {', '.join(missing_vars)}")
        print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
    else:
        print("✅ All required environment variables present")
    
    # Test 5: Basic file system checks
    try:
        from pathlib import Path
        required_dirs = ["app", "app/api", "app/models", "app/graphs"]
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                warnings.append(f"Missing directory: {dir_path}")
            else:
                print(f"✅ Directory exists: {dir_path}")
    except Exception as e:
        warnings.append(f"File system check error: {e}")
        print(f"⚠️ File system check error: {e}")
    
    # Summary
    if errors:
        print(f"\n❌ Validation failed with {len(errors)} errors:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        return False
    elif warnings:
        print(f"\n⚠️ Validation completed with {len(warnings)} warnings:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
        print("\nProceeding with startup (warnings are non-fatal)...")
        return True
    else:
        print("\n✅ All validation tests passed!")
        return True

if __name__ == "__main__":
    success = asyncio.run(validate_startup())
    sys.exit(0 if success else 1)
