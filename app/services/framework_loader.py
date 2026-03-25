"""
Global Framework Loader - Avoids circular imports
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

# Global variable to store the framework data
GLOBAL_FRAMEWORK: Dict[str, Any] = {}


def load_global_framework() -> Dict[str, Any]:
    """Load global framework data from JSON file."""
    global GLOBAL_FRAMEWORK
    
    if GLOBAL_FRAMEWORK:
        return GLOBAL_FRAMEWORK
    
    try:
        framework_path = Path("global_framework.json")
        if framework_path.exists():
            with open(framework_path, 'r', encoding='utf-8') as f:
                GLOBAL_FRAMEWORK = json.load(f)
            print(f"✅ Global framework loaded successfully: {GLOBAL_FRAMEWORK.get('process_name', 'Unknown')}")
        else:
            print("❌ Global framework file not found")
            GLOBAL_FRAMEWORK = {}
    except Exception as e:
        print(f"❌ Error loading global framework: {e}")
        GLOBAL_FRAMEWORK = {}
    
    return GLOBAL_FRAMEWORK


def get_global_framework() -> Dict[str, Any]:
    """Get the loaded global framework data."""
    return GLOBAL_FRAMEWORK


def is_framework_loaded() -> bool:
    """Check if global framework is loaded."""
    return bool(GLOBAL_FRAMEWORK)
