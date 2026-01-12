import time
from smbus2 import SMBus

class DisplayManager:
    """
    Manages the 576-LED display across 6 Arduino Mega Slaves.
    """
    def __init__(self, bus_id=1):
        self.bus_id = bus_id
        # 6 Slaves * 96 LEDs = 576 LEDs total
        # Buffer stores the state of each LED (0 or 1)
        # We use a bytearray for efficiency in packing
        self.total_leds = 576
        self.leds_per_slave = 96
        self.bytes_per_slave = 12
        self.num_slaves = 6
        self.base_address = 0x08
        
        # Internal state buffer: False (off), True (on)
        self.buffer = [0] * self.total_leds
        
        try:
            self.bus = SMBus(self.bus_id)
            print(f"I2C Bus {self.bus_id} initialized.")
        except Exception as e:
            print(f"Error initializing I2C Bus: {e}")
            self.bus = None

    def set_led(self, index, state):
        """Set a specific LED index (0-575) to state (0 or 1)."""
        if 0 <= index < self.total_leds:
            self.buffer[index] = 1 if state else 0

    def clear(self):
        """Turn off all LEDs."""
        self.buffer = [0] * self.total_leds

    def fill(self):
        """Turn on all LEDs."""
        self.buffer = [1] * self.total_leds

    def show(self):
        """Pack buffer and send to slaves via I2C."""
        if not self.bus:
            # print("Simulating I2C write (No Bus Detected)")
            return

        for slave_idx in range(self.num_slaves):
            address = self.base_address + slave_idx
            start_led = slave_idx * self.leds_per_slave
            end_led = start_led + self.leds_per_slave
            
            # Slice the buffer for this slave
            slave_chunk = self.buffer[start_led:end_led]
            
            # Pack 96 bools into 12 bytes
            packed_data = []
            for i in range(0, 96, 8):
                byte_val = 0
                for bit in range(8):
                    if slave_chunk[i + bit]:
                        byte_val |= (1 << bit)
                packed_data.append(byte_val)
            
            try:
                # Write block data
                # cmd is the first byte, often used as register address
                # Here we just treat the whole block as raw data.
                # SMBus write_i2c_block_data(addr, cmd, [vals])
                # We interpret the first byte of payload as 'cmd' or send a dummy cmd if needed.
                # However, Arduino Wire.onReceive just reads bytes.
                # Standard smbus2 write_i2c_block_data sends [addr] [cmd] [len] [data...]
                # To simplify, we can just write bytes.
                # Let's use write_i2c_block_data with cmd=0
                self.bus.write_i2c_block_data(address, 0, packed_data)
            except OSError as e:
                print(f"Error writing to slave 0x{address:02X}: {e}")

    def close(self):
        """Clean up resources."""
        if self.bus:
            self.clear()
            self.show()
            self.bus.close()
