import sys
import time
import signal
from display_manager import DisplayManager
from animation import RandomTwinkle, ScanningChase, LarsonScanner

def signal_handler(sig, frame):
    print("\nGracefully shutting down...")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Initializing LED Matrix Controller...")
    dm = DisplayManager()
    
    animations = [
        ("Scanning Chase", ScanningChase(dm)),
        ("Random Twinkle", RandomTwinkle(dm)),
        ("Larson Scanner", LarsonScanner(dm))
    ]
    
    try:
        while True:
            for name, anim in animations:
                print(f"Running Animation: {name}")
                start_time = time.time()
                # Run each animation for 5 seconds
                while time.time() - start_time < 5:
                    anim.step()
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Turning off all LEDs.")
        dm.close()

if __name__ == "__main__":
    main()
