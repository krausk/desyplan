#!/usr/bin/env python3
"""
Simple test script for 3-LED test environment.
Runs basic patterns to verify I2C communication and LED control.
"""

import sys
import time
import signal
from display_manager import DisplayManager
from config_loader import Config


def signal_handler(sig, frame):
    print("\nGracefully shutting down...")
    sys.exit(0)


class SimplePattern:
    """Simple patterns optimized for 3 LEDs."""

    def __init__(self, display_manager):
        self.dm = display_manager
        self.min_delay = display_manager.config.min_relay_delay

    def all_on(self, duration=2.0):
        """Turn all LEDs on."""
        print("Pattern: All ON")
        self.dm.clear()
        for i in range(self.dm.total_leds):
            self.dm.set_led(i, 1)
        self.dm.show()
        time.sleep(duration)

    def all_off(self, duration=2.0):
        """Turn all LEDs off."""
        print("Pattern: All OFF")
        self.dm.clear()
        self.dm.show()
        time.sleep(duration)

    def sequential(self, duration=0.5):
        """Light LEDs one by one."""
        print("Pattern: Sequential")
        for i in range(self.dm.total_leds):
            self.dm.clear()
            self.dm.set_led(i, 1)
            self.dm.show()
            time.sleep(max(duration, self.min_delay))

    def chase(self, cycles=3):
        """Chase pattern (Knight Rider style)."""
        print("Pattern: Chase")
        for _ in range(cycles):
            # Forward
            for i in range(self.dm.total_leds):
                self.dm.clear()
                self.dm.set_led(i, 1)
                self.dm.show()
                time.sleep(self.min_delay * 2)
            # Backward
            for i in range(self.dm.total_leds - 1, -1, -1):
                self.dm.clear()
                self.dm.set_led(i, 1)
                self.dm.show()
                time.sleep(self.min_delay * 2)

    def blink_all(self, cycles=5):
        """Blink all LEDs together."""
        print("Pattern: Blink All")
        for _ in range(cycles):
            self.all_on(duration=0.3)
            self.all_off(duration=0.3)

    def binary_count(self, max_count=8):
        """Display binary counting pattern."""
        print("Pattern: Binary Count")
        for count in range(min(max_count, 2**self.dm.total_leds)):
            self.dm.clear()
            for bit in range(self.dm.total_leds):
                if count & (1 << bit):
                    self.dm.set_led(bit, 1)
            self.dm.show()
            print(f"  Count: {count:03b}")
            time.sleep(max(0.5, self.min_delay))

    def alternating(self, cycles=5):
        """Alternating pattern."""
        print("Pattern: Alternating")
        for i in range(cycles):
            self.dm.clear()
            # Odd LEDs on
            for j in range(0, self.dm.total_leds, 2):
                self.dm.set_led(j, 1)
            self.dm.show()
            time.sleep(0.5)

            self.dm.clear()
            # Even LEDs on
            for j in range(1, self.dm.total_leds, 2):
                self.dm.set_led(j, 1)
            self.dm.show()
            time.sleep(0.5)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    # Load configuration
    config = Config()

    # Verify we're in test mode
    if config.environment != 'test':
        print("Warning: This script is optimized for 'test' environment (3 LEDs)")
        print(f"Current environment: {config.environment} ({config.total_leds} LEDs)")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return

    config.print_config()

    print("Initializing Simple Test Controller...")
    try:
        dm = DisplayManager(config)
    except Exception as e:
        print(f"Failed to init DisplayManager: {e}")
        return

    print("\nStarting LED test patterns...")
    print("Press Ctrl+C to stop\n")

    pattern = SimplePattern(dm)

    try:
        while True:
            pattern.all_off(duration=1.0)
            pattern.sequential(duration=0.5)
            pattern.all_off(duration=0.5)
            pattern.chase(cycles=2)
            pattern.all_off(duration=0.5)
            pattern.blink_all(cycles=3)
            pattern.all_off(duration=0.5)
            pattern.binary_count(max_count=8)
            pattern.all_off(duration=0.5)
            pattern.alternating(cycles=3)
            print("\n--- Cycle complete, repeating ---\n")

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        print("Turning off all LEDs")
        dm.clear()
        dm.show()
        dm.close()
        print("Done!")


if __name__ == '__main__':
    main()
