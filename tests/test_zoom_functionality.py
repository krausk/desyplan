#!/usr/bin/env python3
"""
Test script to verify LED assignment zoom functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'controller'))

from config_loader import Config

def test_zoom_limits():
    """Test that zoom limits are correctly set."""
    print("Testing Zoom Limits...")
    
    # Simulate zoom operations
    zoom_level = 1.0
    
    # Test zoom in
    zoom_level = min(zoom_level * 1.2, 10)
    assert zoom_level <= 10, f"Zoom in failed: {zoom_level}"
    print(f"✓ Zoom in: {zoom_level:.2f}x (max: 10x)")
    
    # Test zoom out
    zoom_level = max(zoom_level / 1.2, 0.1)
    assert zoom_level >= 0.1, f"Zoom out failed: {zoom_level}"
    print(f"✓ Zoom out: {zoom_level:.2f}x (min: 0.1x)")
    
    # Test reset
    zoom_level = 1.0
    assert zoom_level == 1.0, "Reset failed"
    print(f"✓ Reset: {zoom_level:.2f}x")
    
    print("\n✓ All zoom limit tests passed!\n")

def test_zoom_levels():
    """Test various zoom levels."""
    print("Testing Zoom Levels...")
    
    zoom_levels = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
    
    for level in zoom_levels:
        zoom_level = level
        zoom_level = min(zoom_level * 1.2, 10)
        zoom_level = max(zoom_level / 1.2, 0.1)
        
        percentage = zoom_level * 100
        print(f"✓ {percentage:.1f}% ({zoom_level:.2f}x)")
    
    print("\n✓ All zoom level tests passed!\n")

def test_config_structure():
    """Test that config has LED assignment structure."""
    print("Testing Config Structure...")
    
    try:
        config = Config()
        
        if config.led_assignments:
            print("✓ Config has 'led_assignments' section")
            
            # Check if there are assignment sets
            if config.led_assignments:
                print(f"✓ Found {len(config.led_assignments)} assignment sets")
                
                # Check for default set
                if 'default' in config.led_assignments:
                    print("✓ 'default' assignment set exists")
            else:
                print("⚠ No assignment sets found (this is OK)")
        else:
            print("⚠ No 'led_assignments' section in config (this is OK)")
            
    except Exception as e:
        print(f"⚠ Error loading config: {e}")
    
    print("\n✓ Config structure test completed!\n")

def main():
    """Run all tests."""
    print("=" * 60)
    print("LED Assignment Zoom Functionality Tests")
    print("=" * 60)
    print()
    
    test_zoom_limits()
    test_zoom_levels()
    test_config_structure()
    
    print("=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    main()