import time
import random
import abc
import logging

logger = logging.getLogger(__name__)

class Animation(abc.ABC):
    def __init__(self, display_manager):
        self.dm = display_manager
        self.last_update_time = 0
        # Get minimum delay from config
        self.min_relay_delay = display_manager.config.min_relay_delay

    @abc.abstractmethod
    def _do_step(self):
        """Perform one step of the animation logic."""
        pass

    def step(self):
        """Wrapper to measure step time and perform the step."""
        start = time.time()
        self._do_step()
        elapsed = time.time() - start
        
        # Determine threshold: requested speed or safety limit, plus 50ms buffer
        target_delay = max(getattr(self, 'speed', 0.1), getattr(self, 'min_relay_delay', 0.05))
        threshold = target_delay + 0.05
        
        if elapsed > threshold:
            logger.warning(f"Animation step took {elapsed*1000:.1f}ms in {self.__class__.__name__} (threshold: {threshold*1000:.1f}ms)")

    def safe_wait(self, duration):
        """
        Waits for the specified duration OR the safe limit, whichever is longer.
        Also accounts for processing time since last update.
        """
        now = time.time()
        # Ensure we don't switch faster than configured minimum delay
        # If the requested duration is shorter than safety limit, extend it.

        target_delay = max(duration, self.min_relay_delay)

        # Calculate how much we really need to sleep
        time_since_last = now - self.last_update_time
        remaining = target_delay - time_since_last

        if remaining > 0:
            time.sleep(remaining)

        self.last_update_time = time.time()

class RandomTwinkle(Animation):
    def __init__(self, display_manager, speed=0.1, density=0.05):
        super().__init__(display_manager)
        self.speed = speed
        self.density = density  # Should be low for relays! 

    def _do_step(self):
        self.dm.clear()
        # RandomTwinkle on relays is 'expensive' mechanically.
        # We limit the number of changes per frame to be safe.
        change_count = 0
        for i in range(self.dm.total_leds):
            if random.random() < self.density:
                self.dm.set_led(i, 1)
                change_count += 1
                
        self.dm.show()
        self.safe_wait(self.speed)

class ScanningChase(Animation):
    def __init__(self, display_manager, speed=0.1, width=1):
        super().__init__(display_manager)
        self.speed = speed  # Default slower for relays
        self.width = width
        self.position = 0

    def _do_step(self):
        self.dm.clear()
        for i in range(self.width):
            idx = (self.position + i) % self.dm.total_leds
            self.dm.set_led(idx, 1)
        self.dm.show()
        
        self.position = (self.position + 1) % self.dm.total_leds
        self.safe_wait(self.speed)
        
class CircleAnimation(Animation):
    """Loops through all LEDs sequentially in a circle."""
    def __init__(self, display_manager, speed=0.1):
        super().__init__(display_manager)
        self.speed = speed
        self.position = 0

    def _do_step(self):
        self.dm.clear()
        # Set only the current LED
        self.dm.set_led(self.position, 1)
        self.dm.show()
        
        # Increment and wrap around
        self.position = (self.position + 1) % self.dm.total_leds
        self.safe_wait(self.speed)
        
class LarsonScanner(Animation):
    """KITT / Cylon effect - Adapted for Relays (Slower)"""
    def __init__(self, display_manager, speed=0.08, width=3):
        super().__init__(display_manager)
        self.speed = speed
        self.width = width
        self.pos = 0
        self.direction = 1
        
    def _do_step(self):
        self.dm.clear()
        for i in range(self.width):
            idx = self.pos + i
            if 0 <= idx < self.dm.total_leds:
                self.dm.set_led(idx, 1)
        self.dm.show()
        
        self.pos += self.direction
        if self.pos > self.dm.total_leds - self.width or self.pos < 0:
            self.direction *= -1
            
        self.safe_wait(self.speed)

class RelayTest(Animation):
    """Diagnostic pattern: Toggles blocks slowly."""
    def __init__(self, display_manager, speed=1.0):
        super().__init__(display_manager)
        self.speed = speed
        self.state = 0
        
    def _do_step(self):
        print(f"Relay Test State: {self.state}")
        self.dm.clear()
        if self.state == 0:
            # All OFF
            pass
        elif self.state == 1:
            # First half ON
            for i in range(self.dm.total_leds // 2):
                self.dm.set_led(i, 1)
        elif self.state == 2:
            # Second half ON
            for i in range(self.dm.total_leds // 2, self.dm.total_leds):
                self.dm.set_led(i, 1)
        
        self.dm.show()
        self.state = (self.state + 1) % 3
        self.safe_wait(self.speed)
