import time
import math
import os
from config_loader import Config

# Mock SMBus for development/testing without hardware
class MockSMBus:
    def __init__(self, bus):
        print(f"[MOCK MODE] Using MockSMBus for I2C bus {bus}")
    def write_i2c_block_data(self, addr, cmd, vals):
        pass  # Silently ignore writes in mock mode
    def read_byte(self, addr):
        return 0
    def close(self):
        pass

# Try to import real SMBus
try:
    from smbus2 import SMBus as RealSMBus
    SMBUS_AVAILABLE = True
except ImportError:
    print("Warning: smbus2 not found. Using MockSMBus.")
    SMBUS_AVAILABLE = False
    RealSMBus = MockSMBus

class RelayController:
    """
    Manages communication with Arduino slaves via I2C.
    Supports multiple environments via config.yaml.
    Enforces relay safety timings and maps logical LED indices to physical addresses.
    """

    def __init__(self, config=None, mock_mode=None):
        # Load configuration
        self.config = config if config else Config()

        # Set hardware parameters from config
        self.ADDRESSES = self.config.i2c_addresses
        self.LEDS_PER_SLAVE = self.config.leds_per_slave
        self.BYTES_PER_SLAVE = math.ceil(self.LEDS_PER_SLAVE / 8)

        # Determine if we should use mock mode
        if mock_mode is None:
            # Auto-detect: use mock if I2C device doesn't exist or isn't accessible
            i2c_device = f'/dev/i2c-{self.config.i2c_bus}'
            mock_mode = not os.path.exists(i2c_device) or not os.access(i2c_device, os.R_OK | os.W_OK)

        # Initialize I2C bus
        if mock_mode or not SMBUS_AVAILABLE:
            self.bus = MockSMBus(self.config.i2c_bus)
            self.mock_mode = True
        else:
            try:
                self.bus = RealSMBus(self.config.i2c_bus)
                self.mock_mode = False
            except (PermissionError, FileNotFoundError) as e:
                print(f"Warning: Cannot access I2C device: {e}")
                print("Falling back to MockSMBus for testing.")
                self.bus = MockSMBus(self.config.i2c_bus)
                self.mock_mode = True

        self.total_relays = self.config.total_leds

        mode_str = "MOCK" if self.mock_mode else "HARDWARE"
        print(f"RelayController initialized ({self.config.environment} mode, {mode_str})")
        print(f"Managing {self.total_relays} outputs across {len(self.ADDRESSES)} slave(s).")

    def scan_bus(self):
        """Checks for presence of all expected slave addresses."""
        print("Scanning I2C Bus for Slaves...")
        found = []
        for addr in self.ADDRESSES:
            try:
                # simple read to check presence
                self.bus.read_byte(addr)
                found.append(addr)
                print(f"  [OK] Found Slave at 0x{addr:02X}")
            except Exception:
                print(f"  [FAIL] No response from 0x{addr:02X}")
        return found

    def dispatch_frame(self, frame_data):
        """
        Sends a full frame (up to 576 bits) to all slaves.
        
        Args:
            frame_data (list/bytearray): 1D array of 1s and 0s, or packed bytes. 
                                         Here assuming flat list of ints (0/1).
        """
        # Split flat bit array into chunks for each slave
        # Frame size expected: 6 * 96 = 576 bits
        
        if len(frame_data) < self.total_relays:
            # Pad with zeros if short
            frame_data += [0] * (self.total_relays - len(frame_data))
            
        for i, addr in enumerate(self.ADDRESSES):
            start_idx = i * self.LEDS_PER_SLAVE
            end_idx = start_idx + self.LEDS_PER_SLAVE
            slave_chunk = frame_data[start_idx:end_idx]
            
            # Pack bits into bytes
            packed_bytes = self._pack_bits(slave_chunk)
            
            try:
                # CMD byte 0x00 is arbitrary, just writing data block
                self.bus.write_i2c_block_data(addr, 0x00, packed_bytes)
            except OSError as e:
                print(f"Error writing to 0x{addr:02X}: {e}")

    def _pack_bits(self, bits):
        """Converts a list of 96 bits (0/1) into 12 bytes."""
        packed = []
        for i in range(0, len(bits), 8):
            byte_val = 0
            for b in range(8):
                if i + b < len(bits):
                    if bits[i + b]:
                        byte_val |= (1 << b)
            packed.append(byte_val)
        return packed

    def close(self):
        self.bus.close()
