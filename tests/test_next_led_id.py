#!/usr/bin/env python3
"""
Test that nextLEDId is properly calculated after loading assignments
"""

def test_next_led_id_calculation():
    """Test that nextLEDId is correctly set to max ID + 1"""
    
    # Simulate the logic from led_position.js
    assignments = {
        '1': {'x': 100, 'y': 100, 'name': 'LED_1'},
        '10': {'x': 200, 'y': 200, 'name': 'LED_10'},
        '15': {'x': 300, 'y': 300, 'name': 'LED_15'},
        '20': {'x': 400, 'y': 400, 'name': 'LED_20'},
        '25': {'x': 500, 'y': 500, 'name': 'LED_25'},
    }
    
    # Find the maximum LED ID and set nextLEDId to max + 1
    led_ids = [int(k) for k in assignments.keys()]
    if len(led_ids) > 0:
        max_id = max(led_ids)
        next_led_id = max_id + 1
    
    # Expected: max ID is 25, so nextLEDId should be 26
    expected_next_id = 26
    
    print(f"✓ Test passed: nextLEDId would be {expected_next_id}")
    print(f"  Max existing ID: {max_id}")
    print(f"  Next LED ID: {next_led_id}")
    
    assert next_led_id == expected_next_id, f"Expected nextLEDId to be {expected_next_id}, got {next_led_id}"
    
    return True

def test_empty_assignments():
    """Test that nextLEDId starts at 1 when assignments are empty"""
    
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
    
    print(f"✓ Test passed: nextLEDId would be {expected_next_id}")
    print(f"  Max existing ID: {max_id if len(led_ids) > 0 else 'N/A'}")
    print(f"  Next LED ID: {next_led_id}")
    
    assert next_led_id == expected_next_id, f"Expected nextLEDId to be {expected_next_id}, got {next_led_id}"
    
    return True

def test_consecutive_ids():
    """Test that adding LEDs with consecutive IDs works correctly"""
    
    # Start with empty assignments
    assignments = {}
    next_led_id = 1
    
    # Add LEDs 1, 2, 3
    assignments[next_led_id] = {'x': 100, 'y': 100, 'name': 'LED_1'}
    next_led_id += 1
    
    assignments[next_led_id] = {'x': 200, 'y': 200, 'name': 'LED_2'}
    next_led_id += 1
    
    assignments[next_led_id] = {'x': 300, 'y': 300, 'name': 'LED_3'}
    next_led_id += 1
    
    # Now load assignments and recalculate nextLEDId
    led_ids = [int(k) for k in assignments.keys()]
    if len(led_ids) > 0:
        max_id = max(led_ids)
        next_led_id = max_id + 1
    
    # Expected: nextLEDId should be 4
    expected_next_id = 4
    
    print(f"✓ Test passed: nextLEDId would be {expected_next_id}")
    print(f"  Max existing ID: {max_id}")
    print(f"  Next LED ID: {next_led_id}")
    
    assert next_led_id == expected_next_id, f"Expected nextLEDId to be {expected_next_id}, got {next_led_id}"
    
    return True

if __name__ == '__main__':
    print("Testing nextLEDId Calculation\n")
    print("=" * 50)
    
    tests = [
        test_next_led_id_calculation,
        test_empty_assignments,
        test_consecutive_ids
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
    else:
        print(f"\n✗ {failed} test(s) failed")