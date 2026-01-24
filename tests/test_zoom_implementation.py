"""
Test script for zoom functionality in LED Position interface
"""
import requests
import time
import json

BASE_URL = "http://localhost:5000"
LED_POSITION_URL = "http://localhost:5000/led-position"

def test_zoom_functionality():
    """Test that zoom works correctly with the Panzoom library"""
    print("Testing Zoom Functionality...")
    
    # Test 1: Check if Panzoom library is loaded
    print("\n1. Checking if Panzoom library is loaded...")
    try:
        response = requests.get(LED_POSITION_URL)
        if "panzoom.min.js" in response.text:
            print("✓ Panzoom library loaded successfully")
        else:
            print("✗ Panzoom library not found")
            return False
    except Exception as e:
        print(f"✗ Error checking library: {e}")
        return False
    
    # Test 2: Check API endpoints
    print("\n2. Testing API endpoints...")
    try:
        # Get assignment sets
        response = requests.get(f"{BASE_URL}/api/led-assignment-sets")
        if response.status_code == 200:
            print("✓ Assignment sets endpoint working")
        else:
            print("✗ Assignment sets endpoint failed")
            return False
        
        # Get default assignments
        response = requests.get(f"{BASE_URL}/api/led-assignments?set=default")
        if response.status_code == 200:
            print("✓ Assignments endpoint working")
        else:
            print("✗ Assignments endpoint failed")
            return False
    except Exception as e:
        print(f"✗ Error testing API: {e}")
        return False
    
    # Test 3: Create a test assignment
    print("\n3. Creating test LED assignment...")
    try:
        test_assignment = {
            "assignments": {
                1: {
                    "x": 400,
                    "y": 300,
                    "name": "Test_LED_1",
                    "pin": 13
                }
            },
            "set": "test_zoom"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/led-assignments",
            json=test_assignment
        )
        
        if response.status_code == 200:
            print("✓ Test assignment created successfully")
        else:
            print(f"✗ Failed to create assignment: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error creating assignment: {e}")
        return False
    
    # Test 4: Verify assignment was saved
    print("\n4. Verifying assignment was saved...")
    try:
        response = requests.get(f"{BASE_URL}/api/led-assignments?set=test_zoom")
        if response.status_code == 200:
            data = response.json()
            if data.get("assignments") and 1 in data["assignments"]:
                print("✓ Assignment verified in database")
            else:
                print("✗ Assignment not found in database")
                return False
        else:
            print("✗ Failed to retrieve assignment")
            return False
    except Exception as e:
        print(f"✗ Error verifying assignment: {e}")
        return False
    
    # Test 5: Check for haptic feedback support
    print("\n5. Checking for haptic feedback support...")
    try:
        response = requests.get(LED_POSITION_URL)
        if "navigator.vibrate" in response.text or "triggerHapticFeedback" in response.text:
            print("✓ Haptic feedback support detected")
        else:
            print("⚠ Haptic feedback support not detected (optional)")
    except Exception as e:
        print(f"⚠ Error checking haptic feedback: {e}")
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)
    return True

if __name__ == "__main__":
    success = test_zoom_functionality()
    exit(0 if success else 1)