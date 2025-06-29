#!/usr/bin/env python3
"""
Minimal test to reproduce the model discovery issue
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.manager import ModelInfo, ModelStatus
from app.core.config import PRIORITY_TIERS

def test_model_info_creation():
    print("🔍 Testing ModelInfo creation...")
    
    try:
        # Test creating a ModelInfo with enum
        model_info = ModelInfo(
            name="test-model",
            status=ModelStatus.READY,
            tier="T2"
        )
        print(f"✅ ModelInfo created successfully: {model_info}")
        
        # Test dictionary storage
        models = {}
        models["test-model"] = model_info
        print(f"✅ Dictionary storage works: {list(models.keys())}")
        
        # Test priority tiers iteration
        print(f"Priority tiers: {PRIORITY_TIERS}")
        for tier_name, tier_models in PRIORITY_TIERS.items():
            print(f"  {tier_name}: {tier_models}")
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_info_creation()
