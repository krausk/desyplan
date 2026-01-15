import sys
import time
import signal
import argparse
from display_manager import DisplayManager
from animation import RandomTwinkle, ScanningChase, LarsonScanner, RelayTest

def signal_handler(sig, frame):
    print("\nGracefully shutting down...")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Relay Controller Master")
    parser.add_argument('--scan', action='store_true', help='Scan I2C bus for slaves')
    parser.add_argument('--test', action='store_true', help='Run diagnostic relay test')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    
    print("Initializing LED Matrix Controller (Relay Mode)...")
    try:
        dm = DisplayManager()
    except Exception as e:
        print(f"Failed to init DisplayManager: {e}")
        return

    if args.scan:
        dm.controller.scan_bus()
        return

    if args.test:
        print("Running Relay Diagnostic Test...")
        anim = RelayTest(dm)
        try:
            while True:
                anim.step()
        except KeyboardInterrupt:
            dm.close()
        return

    # Normal Animation Loop
    animations = [
        ("Scanning Chase", ScanningChase(dm, speed=0.08)),
        ("Random Twinkle", RandomTwinkle(dm, speed=0.1)),
        ("Larson Scanner", LarsonScanner(dm, speed=0.08))
    ]
    
    try:
        while True:
            for name, anim in animations:
                print(f"Running Animation: {name}")
                start_time = time.time()
                # Run each animation for 10 seconds
                while time.time() - start_time < 10:
                    anim.step()
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Turning off all LEDs.")
        dm.clear()
        dm.show()
        dm.close()

if __name__ == "__main__":
    main()
