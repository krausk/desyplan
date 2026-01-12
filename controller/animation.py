import time
import random
import abc

class Animation(abc.ABC):
    def __init__(self, display_manager):
        self.dm = display_manager

    @abc.abstractmethod
    def step(self):
        """Perform one step of the animation."""
        pass

class RandomTwinkle(Animation):
    def __init__(self, display_manager, speed=0.1, density=0.05):
        super().__init__(display_manager)
        self.speed = speed
        self.density = density

    def step(self):
        self.dm.clear()
        for i in range(self.dm.total_leds):
            if random.random() < self.density:
                self.dm.set_led(i, 1)
        self.dm.show()
        time.sleep(self.speed)

class ScanningChase(Animation):
    def __init__(self, display_manager, speed=0.02, width=5):
        super().__init__(display_manager)
        self.speed = speed
        self.width = width
        self.position = 0

    def step(self):
        self.dm.clear()
        for i in range(self.width):
            idx = (self.position + i) % self.dm.total_leds
            self.dm.set_led(idx, 1)
        self.dm.show()
        self.position = (self.position + 1) % self.dm.total_leds
        time.sleep(self.speed)

class ScrollingText(Animation):
    def __init__(self, display_manager, text="HELLO", speed=0.1):
        super().__init__(display_manager)
        self.text = text
        self.speed = speed
        # NOTE: A real implementation would need a font map (5x7 or similar)
        # mapped to the specific physical layout of the LED panel (rows/cols).
        # Since the prompt implies a linear addressing or undefined geometry,
        # we will simulate scrolling by just filing generic blocks for this demo.
        print("Note: ScrollingText requires a valid Font and XY Mapping.")
    
    def step(self):
        # Placeholder for actual text scrolling
        pass

class LarsonScanner(Animation):
    """KITT / Cylon effect"""
    def __init__(self, display_manager, speed=0.03, width=10):
        super().__init__(display_manager)
        self.speed = speed
        self.width = width
        self.pos = 0
        self.direction = 1
        
    def step(self):
        self.dm.clear()
        for i in range(self.width):
            idx = self.pos + i
            if 0 <= idx < self.dm.total_leds:
                self.dm.set_led(idx, 1)
        self.dm.show()
        
        self.pos += self.direction
        if self.pos > self.dm.total_leds - self.width or self.pos < 0:
            self.direction *= -1
        time.sleep(self.speed)
