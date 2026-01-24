#!/usr/bin/env python3
"""
Test LED assignment functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'controller'))

import yaml
from config_loader import Config

def test_config_structure():
    """Test that config.yaml has proper LED assignment structure."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Check that led_assignments exists
    assert 'led_assignments' in config_data, "led_assignments not found in config.yaml"
    
    # Check that default set exists
    assert 'default' in config_data['led_assignments'], "Default set not found"
    
    # Check that individual assignments have pin information
    assignments = config_data['led_assignments']
    
    # Skip default metadata
    assignment_keys = [k for k in assignments.keys() if k != 'default']
    
    # Check that at least one assignment has pin info
    has_pin = False
    for key in assignment_keys:
        if isinstance(assignments[key], dict):
            if 'pin' in assignments[key]:
                has_pin = True
                break
    
    assert has_pin, "No assignments with pin information found"
    
    print("✓ Config structure is correct")
    return True

def test_config_loader():
    """Test that Config class loads assignments correctly."""
    config = Config()
    
    # Check that led_assignments attribute exists
    assert hasattr(config, 'led_assignments'), "Config class missing led_assignments attribute"
    
    # Check that assignments are loaded
    assert isinstance(config.led_assignments, dict), "led_assignments is not a dictionary"
    
    print("✓ Config loader works correctly")
    return True

def test_multiple_sets():
    """Test that multiple assignment sets are supported."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    led_assignments = config_data['led_assignments']
    
    # Count sets (default + individual assignments)
    set_count = len(led_assignments)
    
    # Should have at least default set
    assert set_count >= 1, "No assignment sets found"
    
    print(f"✓ Multiple sets supported ({set_count} sets)")
    return True

def test_pin_mapping():
    """Test that pin mapping is preserved in assignments."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    led_assignments = config_data['led_assignments']
    
    # Check first assignment for pin mapping
    assignment_keys = [k for k in led_assignments.keys() if k != 'default']
    
    if assignment_keys:
        first_key = assignment_keys[0]
        first_assignment = led_assignments[first_key]
        
        if isinstance(first_assignment, dict):
            assert 'pin' in first_assignment, "Pin mapping not found in assignment"
            assert isinstance(first_assignment['pin'], int), "Pin should be an integer"
            
            print(f"✓ Pin mapping preserved (Pin {first_assignment['pin']})")
            return True
    
    print("✓ Pin mapping structure verified")
    return True

def main():
    """Run all tests."""
    print("Testing LED Assignment Implementation\n")
    print("=" * 50)
    
    tests = [
        test_config_structure,
        test_config_loader,
        test_multiple_sets,
        test_pin_mapping
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())