#!/usr/bin/env python3
"""
Debug script to fix model discovery
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from app.models.manager import ModelManager, ModelStatus

async def debug_model_discovery():
    print("🔍 Debugging model discovery...")
    
    # Create model manager
    manager = ModelManager()
    await manager.initialize()
    
    # Check what models we actually have
    print(f"📊 Models discovered: {len(manager.models)}")
    for name, info in manager.models.items():
        print(f"  📖 {name}: status={info.status}, tier={info.tier}")
    
    # Test with Ollama directly
    print("\n🔍 Testing Ollama client directly...")
    models_data = await manager.ollama_client.list_models()
    print(f"Raw Ollama response: {models_data}")
    
    for model_data in models_data:
        print(f"Model data: {model_data} (type: {type(model_data)})")
        if isinstance(model_data, dict):
            name = model_data.get("name", "")
            print(f"  Extracted name: '{name}'")

if __name__ == "__main__":
    asyncio.run(debug_model_discovery())
