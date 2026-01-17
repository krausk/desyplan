import sys
import os
import threading
import time
import logging

# Add controller dir to path
sys.path.append(os.path.join(os.getcwd(), 'controller'))

from relay_controller import RelayController
from display_manager import DisplayManager
from animation import CircleAnimation

def test_circle_animation():
    print("Testing CircleAnimation...")
    # Use mock mode for testing
    dm = DisplayManager()
    anim = CircleAnimation(dm, speed=0.01)
    
    # Run 10 steps
    for i in range(10):
        anim.step()
        # In mock mode, we just check if it runs without error
        # and if the position increments
        assert anim.position == (i + 1) % dm.total_leds
    
    print("CircleAnimation test passed!")

def test_thread_safety():
    print("Testing RelayController thread safety...")
    dm = DisplayManager()
    
    def rapid_updates():
        for _ in range(100):
            dm.show()
            time.sleep(0.001)
            
    threads = []
    for _ in range(5):
        t = threading.Thread(target=rapid_updates)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print("Thread safety test passed (no crashes)!")

def test_disconnect_handling():
    print("Testing disconnect handling...")
    dm = DisplayManager()
    
    # Initially all online
    stats = dm.get_slave_status()
    assert all(stats)
    
    # Simulate a write failure on the mock connection
    # Since we can't easily make MockSerial fail without modifying relay_controller.py 
    # (unless we inject a failing method), let's just manually set it offline to check UI/logic
    # Actually, let's inject a failing write to test the auto-skip logic.
    
    dm.controller.serial_connections[0].write = lambda x: (exec("raise Exception('Serial disconnected')"))
    
    # This should mark it offline
    dm.show()
    
    stats = dm.get_slave_status()
    assert stats[0] == False
    assert len(stats) == 1 # In test mode there's only 1 slave
    
    # Test Rescan
    print("Testing manual re-scan...")
    # Reset mock to work again
    dm.controller.serial_connections[0].write = lambda x: None
    dm.controller.scan_bus()
    
    stats = dm.get_slave_status()
    assert stats[0] == True
    
    print("Re-scan test passed!")

if __name__ == "__main__":
    # Setup logging for verification
    logging.basicConfig(level=logging.INFO)
    
    try:
        test_circle_animation()
        test_thread_safety()
        test_disconnect_handling()
        print("\nAll Phase 3 verifications passed!")
    except Exception as e:
        print(f"\nVerification failed: {e}")
        sys.exit(1)
