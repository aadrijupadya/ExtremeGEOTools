#!/usr/bin/env python3
"""
Test script for entity associations
"""

import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.routes.entity_associations import load_entity_associations

def test_load():
    """Test loading entity associations."""
    try:
        data = load_entity_associations()
        print("✅ Successfully loaded entity associations")
        print(f"Total associations: {len(data.get('associations', []))}")
        print(f"Last updated: {data.get('last_updated', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ Error loading entity associations: {e}")
        return False

if __name__ == "__main__":
    print("Testing Entity Associations...")
    test_load()
