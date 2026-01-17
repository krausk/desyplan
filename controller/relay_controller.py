import time
import math
import os
import threading
import logging
from config_loader import Config

logger = logging.getLogger(__name__)

# Mock Serial for development/testing without hardware
class MockSerial:
    def __init__(self, port, baudrate, timeout):
        print(f"[MOCK MODE] Using MockSerial for port {port} at {baudrate} baud")

    def write(self, data):
        pass  # Silently ignore writes in mock mode

    def read(self, size=1):
        return b'\x00' * size

    def readline(self):
        return b''

    def close(self):
        pass

    @property
    def in_waiting(self):
        return 0

    @property
    def is_open(self):
        return True

# Try to import real pyserial
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    print("Warning: pyserial not found. Using MockSerial.")
    SERIAL_AVAILABLE = False
    serial = None

class RelayController:
    """
    Manages communication with Arduino slaves via USB Serial.
    Supports multiple environments via config.yaml.
    Enforces relay safety timings and maps logical LED indices to physical serial ports.
    """

    def __init__(self, config=None, mock_mode=None):
        # Load configuration
        self.config = config if config else Config()

        # Set hardware parameters from config
        self.SERIAL_PORTS = self.config.serial_ports
        self.BAUDRATE = self.config.serial_baudrate
        self.LEDS_PER_SLAVE = self.config.leds_per_slave
        self.BYTES_PER_SLAVE = math.ceil(self.LEDS_PER_SLAVE / 8)

        # Determine if we should use mock mode
        if mock_mode is None:
            # Auto-detect: use mock if any serial port doesn't exist
            mock_mode = not SERIAL_AVAILABLE
            if not mock_mode:
                for port in self.SERIAL_PORTS:
                    if not os.path.exists(port):
                        mock_mode = True
                        break

        # Initialize serial connections
        self.serial_connections = []
        self.slave_online = []
        self.mock_mode = mock_mode
        self._lock = threading.Lock()

        for port in self.SERIAL_PORTS:
            try:
                if mock_mode or not SERIAL_AVAILABLE:
                    conn = MockSerial(port, self.BAUDRATE, timeout=1)
                else:
                    conn = serial.Serial(port, self.BAUDRATE, timeout=1, write_timeout=0.05)
                    # Wait for Arduino to reset after serial connection
                    time.sleep(2)
                    # Flush any startup messages
                    conn.reset_input_buffer()
                    conn.reset_output_buffer()

                self.serial_connections.append(conn)
                self.slave_online.append(True)
                print(f"Connected to {port} at {self.BAUDRATE} baud")
            except Exception as e:
                print(f"Warning: Cannot connect to {port}: {e}")
                if mock_mode:
                    conn = MockSerial(port, self.BAUDRATE, timeout=1)
                    self.serial_connections.append(conn)
                    self.slave_online.append(True)
                else:
                    print(f"Falling back to MockSerial for {port}")
                    conn = MockSerial(port, self.BAUDRATE, timeout=1)
                    self.serial_connections.append(conn)
                    self.slave_online.append(False) # Mark as offline if failed to open real serial
                    self.mock_mode = True

        self.total_relays = self.config.total_leds

        mode_str = "MOCK" if self.mock_mode else "HARDWARE"
        print(f"RelayController initialized ({self.config.environment} mode, {mode_str})")
        print(f"Managing {self.total_relays} outputs across {len(self.SERIAL_PORTS)} slave(s).")

    def scan_bus(self):
        """Checks for presence of all expected serial connections. Attempts reconnection for offline slaves."""
        logger.info("Scanning Serial Ports for Slaves...")
        found = []
        for i, port in enumerate(self.SERIAL_PORTS):
            try:
                # Try to re-open if marked offline or connection is lost
                if not self.slave_online[i]:
                    logger.info(f"  Attempting to reconnect to {port}...")
                    try:
                        # Close old handle if it exists
                        if i < len(self.serial_connections) and self.serial_connections[i]:
                            try:
                                self.serial_connections[i].close()
                            except:
                                pass
                                
                        if self.mock_mode or not SERIAL_AVAILABLE:
                            self.serial_connections[i] = MockSerial(port, self.BAUDRATE, timeout=1)
                            self.slave_online[i] = True
                        else:
                            conn = serial.Serial(port, self.BAUDRATE, timeout=1, write_timeout=0.05)
                            time.sleep(2)
                            conn.reset_input_buffer()
                            conn.reset_output_buffer()
                            self.serial_connections[i] = conn
                            self.slave_online[i] = True
                    except Exception as e:
                        logger.error(f"  Reconnection failed for {port}: {e}")
                
                conn = self.serial_connections[i]
                # Check is_open (pyserial property)
                if self.mock_mode or (hasattr(conn, 'is_open') and conn.is_open):
                    found.append(port)
                    logger.info(f"  [OK] Slave at {port} is ONLINE")
                else:
                    self.slave_online[i] = False
                    logger.warning(f"  [FAIL] Port {port} is closed")
            except Exception as e:
                self.slave_online[i] = False
                logger.error(f"  [FAIL] Error checking/reconnecting {port}: {e}")
        return found

    def dispatch_frame(self, frame_data):
        """
        Sends a full frame (up to 576 bits) to all slaves.

        Args:
            frame_data (list/bytearray): 1D array of 1s and 0s, or packed bytes.
                                         Here assuming flat list of ints (0/1).
        """
        with self._lock:
            # Split flat bit array into chunks for each slave

            if len(frame_data) < self.total_relays:
                # Pad with zeros if short
                frame_data += [0] * (self.total_relays - len(frame_data))

            for i, conn in enumerate(self.serial_connections):
                if not self.slave_online[i]:
                    continue

                start_idx = i * self.LEDS_PER_SLAVE
                end_idx = start_idx + self.LEDS_PER_SLAVE
                slave_chunk = frame_data[start_idx:end_idx]

                # Pack bits into bytes
                packed_bytes = self._pack_bits(slave_chunk)

                try:
                    # Clear any unread messages from Arduino to prevent buffer choking
                    if not self.mock_mode:
                        conn.reset_input_buffer()

                    # Serial protocol: Send start marker, length, data, end marker
                    packet = bytearray([0xFF, 0xAA, len(packed_bytes)])
                    packet.extend(packed_bytes)
                    packet.extend([0x55, 0xFF])

                    start_write = time.time()
                    conn.write(packet)
                    # Ensure data is transmitted
                    if not self.mock_mode:
                        conn.flush()
                    
                    elapsed = time.time() - start_write
                    if elapsed > 0.05: # Log slow writes (>50ms)
                        logger.warning(f"Slow serial write to {self.SERIAL_PORTS[i]}: {elapsed*1000:.1f}ms")

                except Exception as e:
                    port = self.SERIAL_PORTS[i]
                    logger.error(f"Error writing to {port}: {e}. Marking slave as OFFLINE.")
                    self.slave_online[i] = False

    def reset_buffers(self):
        """Clears serial input/output buffers for all slaves."""
        if self.mock_mode:
            return
            
        with self._lock:
            for i, conn in enumerate(self.serial_connections):
                if not self.slave_online[i]:
                    continue
                try:
                    conn.reset_input_buffer()
                    conn.reset_output_buffer()
                except Exception as e:
                    print(f"Error resetting serial buffers for {self.SERIAL_PORTS[i]}: {e}")
                    self.slave_online[i] = False

    def _pack_bits(self, bits):
        """Converts a list of bits (0/1) into bytes."""
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
        """Close all serial connections."""
        for conn in self.serial_connections:
            try:
                conn.close()
            except Exception as e:
                print(f"Error closing serial connection: {e}")
