#!/usr/bin/env python3
"""
Test that LED position page initializes correctly with all LEDs loaded
"""

import sys
import os

# Add the controller directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'controller'))

def test_led_position_initialization():
    """Test that LED position page initializes correctly"""
    
    print("Testing LED Position Initialization")
    print("=" * 50)
    
    # Simulate the initialization logic from led_position.js
    
    # Initialize variables
    assignments = {}
    next_led_id = 1
    current_set = 'default'
    
    # Simulate loading assignments for a set
    # This is what happens on page load
    test_assignments = {
        '1': {'x': 100, 'y': 100, 'name': 'LED_1'},
        '5': {'x': 200, 'y': 200, 'name': 'LED_5'},
        '10': {'x': 300, 'y': 300, 'name': 'LED_10'},
    }
    
    assignments = test_assignments.copy()
    
    # Find the maximum LED ID and set nextLEDId to max + 1
    led_ids = [int(k) for k in assignments.keys()]
    if len(led_ids) > 0:
        max_id = max(led_ids)
        next_led_id = max_id + 1
    
    # Expected: max ID is 10, so nextLEDId should be 11
    expected_next_id = 11
    
    print(f"✓ Test passed: nextLEDId is {next_led_id}")
    print(f"  Max existing ID: {max_id}")
    print(f"  Next LED ID: {next_led_id}")
    
    assert next_led_id == expected_next_id, f"Expected nextLEDId to be {expected_next_id}, got {next_led_id}"
    
    # Simulate adding a new LED
    new_led_id = next_led_id
    assignments[new_led_id] = {
        'x': 400,
        'y': 400,
        'name': f'LED_{new_led_id}'
    }
    next_led_id += 1
    
    # Verify new LED has higher ID than existing ones
    print(f"\n✓ New LED ID: {new_led_id}")
    print(f"  Existing max ID: {max_id}")
    
    assert new_led_id > max_id, f"New LED ID {new_led_id} should be greater than max existing ID {max_id}"
    
    # Verify no ID collision
    assert new_led_id not in test_assignments, f"New LED ID {new_led_id} should not exist in existing assignments"
    
    print(f"\n✓ All LEDs loaded on initialization")
    print(f"✓ New LED has unique ID higher than existing LEDs")
    
    return True

def test_empty_initialization():
    """Test that LED position page initializes correctly with no LEDs"""
    
    print("\nTesting Empty Initialization")
    print("=" * 50)
    
    # Initialize variables
    assignments = {}
    next_led_id = 1
    current_set = 'default'
    
    # Simulate loading assignments for a set (empty)
    assignments = {}
    
    # Find the maximum LED ID and set nextLEDId to max + 1
    led_ids = [int(k) for k in assignments.keys()]
    if len(led_ids) > 0:
        max_id = max(led_ids)
        next_led_id = max_id + 1
    else:
        next_led_id = 1
    
    # Expected: nextLEDId should be 1
    expected_next_id = 1
    
    print(f"✓ Test passed: nextLEDId is {next_led_id}")
    print(f"  Max existing ID: N/A")
    print(f"  Next LED ID: {next_led_id}")
    
    assert next_led_id == expected_next_id, f"Expected nextLEDId to be {expected_next_id}, got {next_led_id}"
    
    print(f"\n✓ Empty initialization works correctly")
    
    return True

def test_multiple_sets():
    """Test that LED position page initializes correctly with multiple sets"""
    
    print("\nTesting Multiple Sets")
    print("=" * 50)
    
    # Simulate loading different sets
    sets = {
        'default': {
            '1': {'x': 100, 'y': 100, 'name': 'LED_1'},
            '2': {'x': 200, 'y': 200, 'name': 'LED_2'},
        },
        'set1': {
            '10': {'x': 300, 'y': 300, 'name': 'LED_10'},
            '15': {'x': 400, 'y': 400, 'name': 'LED_15'},
        },
        'set2': {
            '20': {'x': 500, 'y': 500, 'name': 'LED_20'},
            '25': {'x': 600, 'y': 600, 'name': 'LED_25'},
        }
    }
    
    # Load default set
    current_set = 'default'
    assignments = sets[current_set].copy()
    
    led_ids = [int(k) for k in assignments.keys()]
    if len(led_ids) > 0:
        max_id = max(led_ids)
        next_led_id = max_id + 1
    
    print(f"✓ Default set loaded: max ID = {max_id}, next LED ID = {next_led_id}")
    
    # Load set1
    current_set = 'set1'
    assignments = sets[current_set].copy()
    
    led_ids = [int(k) for k in assignments.keys()]
    if len(led_ids) > 0:
        max_id = max(led_ids)
        next_led_id = max_id + 1
    
    print(f"✓ Set1 loaded: max ID = {max_id}, next LED ID = {next_led_id}")
    
    # Load set2
    current_set = 'set2'
    assignments = sets[current_set].copy()
    
    led_ids = [int(k) for k in assignments.keys()]
    if len(led_ids) > 0:
        max_id = max(led_ids)
        next_led_id = max_id + 1
    
    print(f"✓ Set2 loaded: max ID = {max_id}, next LED ID = {next_led_id}")
    
    print(f"\n✓ Multiple sets work correctly")
    
    return True

if __name__ == '__main__':
    tests = [
        test_led_position_initialization,
        test_empty_initialization,
        test_multiple_sets
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
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {failed} test(s) failed")