from relay_controller import RelayController
from config_loader import Config

class DisplayManager:
    def __init__(self, config=None):
        self.config = config if config else Config()
        self.controller = RelayController(self.config)
        self.total_leds = self.controller.total_relays
        self.buffer = [0] * self.total_leds

    def clear(self):
        self.buffer = [0] * self.total_leds

    def set_led(self, index, state):
        if 0 <= index < self.total_leds:
            self.buffer[index] = 1 if state else 0

    def show(self):
        """Push buffer to physical relays"""
        self.controller.dispatch_frame(self.buffer)

    def reset_hardware(self):
        """Reset hardware state and clear buffers"""
        self.clear()
        self.show()
        self.controller.reset_buffers()

    def get_slave_status(self):
        """Returns list of online status for each slave"""
        return self.controller.slave_online

    def close(self):
        self.controller.close()
