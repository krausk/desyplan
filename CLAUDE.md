# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a retrofit project replacing the original controller of a fire alarm panel with a **Raspberry Pi (Master)** controlling **6x Arduino Mega 2560s (Slaves)** via USB Serial. The system drives 576 electromechanical relays (Panasonic TN2-12V) through WAS-DA2 driver boards to create LED-like visual animations.

**Key Safety Constraint**: The output devices are mechanical relays, NOT LEDs. They have physical limitations:
- **Mechanical switching time**: ~2-3ms
- **Contact bounce and arcing**: Rapid toggling destroys relays
- **Minimum safe interval**: 20ms-50ms between state changes

## Configuration System

The project supports multiple environments through `config.yaml`:

- **Production**: Full system with 6 Arduino Mega 2560s and 576 relays
- **Test**: Simplified setup with 1 Arduino UNO and 3 LEDs

Change the active environment by editing `active_environment` in `config.yaml` or using the `--env` flag:

```bash
# Use test environment
python3 controller/main.py --env test

# Use production environment
python3 controller/main.py --env production
```

The configuration system controls:
- Number of slaves and USB serial ports
- Total number of outputs (LEDs/relays)
- Timing parameters (delays for relay safety or LED visibility)
- Firmware source files and Arduino board types

**Key files**:
- `config.yaml` - Environment configuration
- `controller/config_loader.py` - Configuration parser
- `build.sh` or `deploy_firmware.py` - Automated firmware deployment

See `TEST_SETUP.md` for detailed instructions on the 3-LED test environment.

## Architecture

### Hardware Topology

**Production Environment**:
```
Raspberry Pi (Master, Python)
    ↓ USB Serial
    ↓
├─ Arduino Mega #1 (/dev/ttyUSB0) ─→ 96 relays via GPIO pins
├─ Arduino Mega #2 (/dev/ttyUSB1) ─→ 96 relays
├─ Arduino Mega #3 (/dev/ttyUSB2) ─→ 96 relays
├─ Arduino Mega #4 (/dev/ttyUSB3) ─→ 96 relays
├─ Arduino Mega #5 (/dev/ttyUSB4) ─→ 96 relays
└─ Arduino Mega #6 (/dev/ttyUSB5) ─→ 96 relays
```

Total: 576 independently controllable relays (treated as "LEDs" in code comments)

**Test Environment**:
```
Raspberry Pi (Master, Python)
    ↓ USB Serial
    ↓
└─ Arduino UNO (/dev/ttyUSB0) ─→ 3 LEDs (pins 13, 12, 8)
```

Total: 3 LEDs for development and testing

### Software Architecture

**Python Controller (Raspberry Pi)**:
- `controller/main.py` - Entry point, animation loop orchestration
- `controller/web_server.py` - Flask web interface with API endpoints
- `controller/config_loader.py` - Environment configuration loader (reads config.yaml)
- `controller/display_manager.py` - High-level display abstraction (buffer management)
- `controller/relay_controller.py` - USB Serial communication layer, frame dispatch to slaves
- `controller/animation.py` - Animation classes with relay-safe timing enforcement
- `controller/simple_test.py` - Simple test patterns for 3-LED setup
- `controller/templates/` - HTML templates for web interface
- `controller/static/` - CSS and JavaScript for web interface

**Arduino Firmware**:
- `firmware/SlaveController/SlaveController.ino` - USB Serial slave for production (Arduino Mega)
- `firmware/TestController/TestController.ino` - USB Serial slave for test (Arduino UNO, 3 LEDs)

**Build Tools**:
- `build.sh` - Shell wrapper for firmware deployment
- `deploy_firmware.py` - Python script to compile and upload firmware based on config

**Data Flow**:
1. Animation generates frame (576-bit array)
2. `DisplayManager` buffers state changes
3. `RelayController` splits frame into 6 chunks (96 bits each)
4. Each chunk packed into 12 bytes and sent via USB Serial to corresponding Arduino
5. Arduino receives packet via serial protocol, unpacks, enforces MIN_TOGGLE_INTERVAL (20ms), updates GPIO pins

## Common Commands

### Python Development (Raspberry Pi)

Install dependencies:
```bash
pip3 install -r requirements.txt
```

Run the main animation loop:
```bash
python3 controller/main.py

# Or specify environment
python3 controller/main.py --env production
python3 controller/main.py --env test
```

Run simple test patterns (recommended for test environment):
```bash
python3 controller/simple_test.py
```

Start web interface:
```bash
./start_web.sh

# Or with environment override
./start_web.sh --env test

# Direct Python invocation
python3 controller/web_server.py --host 0.0.0.0 --port 5000 --env test

# Access at http://raspberry-pi-ip:5000
```

Scan serial ports to verify slaves are detected:
```bash
python3 controller/main.py --scan
# Production: Should show /dev/ttyUSB0 through /dev/ttyUSB5
# Test: Should show /dev/ttyUSB0 only
```

Run diagnostic test pattern:
```bash
python3 controller/main.py --test
```

Verify serial devices on the Pi hardware:
```bash
ls -l /dev/ttyUSB*
# Should show all connected Arduino devices
```

### Firmware Deployment (Development Machine → Arduino)

**Using the build script (recommended)**:

```bash
# Compile only (verify it works)
./build.sh --compile-only

# Compile and upload (reads config.yaml for active environment)
./build.sh --port /dev/ttyUSB0

# Override environment
./build.sh --port /dev/ttyUSB0 --env test
./build.sh --port /dev/ttyUSB0 --env production
```

**Manual deployment**:

For production (Arduino Mega 2560):
```bash
# No configuration changes needed - all boards use the same firmware
arduino-cli compile --fqbn arduino:avr:mega firmware/SlaveController
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:mega firmware/SlaveController
```

For test (Arduino UNO):
```bash
arduino-cli compile --fqbn arduino:avr:uno firmware/TestController
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno firmware/TestController
```

## Critical Implementation Details

### Relay Safety Timing

**Firmware-level protection**:
- Production (`SlaveController.ino`): `MIN_TOGGLE_INTERVAL_MS = 20`
- Test (`TestController.ino`): `MIN_TOGGLE_INTERVAL_MS = 10` (LEDs can switch faster)
- Hard limit enforced per GPIO pin
- If a state change is requested before this interval has elapsed since the last toggle, it is silently ignored

**Software-level protection** (configured in `config.yaml`):
- Production: `min_relay_delay: 0.05` (50ms) - Soft limit for relay safety and aesthetics
- Test: `min_relay_delay: 0.1` (100ms) - Longer for visibility of LED changes during testing
- All `Animation` subclasses use `safe_wait()` to enforce this delay

**When modifying animations**:
- For production: Never reduce delays below 50ms without testing on actual relay hardware
- Limit the number of simultaneous relay changes per frame (mechanical stress)
- RandomTwinkle uses low `density` parameter for this reason
- Test environment has more relaxed timing since LEDs don't have mechanical constraints

### Pin Mapping

The Arduino firmware currently uses a simplified placeholder mapping (`SlaveController.ino:38-43`):
- Bits 0-67 → Digital pins 2-69
- Bits 68-95 → Unmapped (set to -1)

**If hardware requires custom mapping**, edit the `ledPins[]` initialization in `setup()` to match the physical ribbon cable connections.

### USB Serial Protocol

**Packet structure**:
- Start marker: `0xFF 0xAA` (2 bytes)
- Length: 1 byte (number of data bytes, typically 12 for production, 1 for test)
- Data: N bytes representing relay states (LSB-first bit packing)
- End marker: `0x55 0xFF` (2 bytes)

**Example packet (test environment - 3 LEDs)**:
`0xFF 0xAA 0x01 0x05 0x55 0xFF` - Sets LEDs 0 and 2 ON (binary 101)

**Bit packing** (`relay_controller.py:165-175`):
- Each byte stores 8 relay states
- Bit 0 (LSB) = first relay in that group of 8

**Arduino side**:
- State machine parses incoming bytes
- Validates packet structure before processing
- Resets to initial state on any error

### Power Requirements

**Critical wiring rules**:
- 5V USB power for Arduinos (from Raspberry Pi USB ports or powered hub)
- 12V supply for relay coils
- **Common ground between all power supplies is mandatory**
- Flyback diodes (1N4007) must be present on relay coils to prevent back-EMF damage

## Hardware Constraints

**DO NOT**:
- Create animations with frame rates faster than 20 FPS (50ms/frame)
- Toggle large numbers of relays simultaneously (mechanical/acoustic issue)
- Power relay coils from Arduino pins (use transistor driver boards)
- Connect more than one Arduino to a single USB port (use powered USB hub for production)

**DO**:
- Test new animations with `--test` flag first
- Verify serial connectivity with `--scan` before troubleshooting animation issues
- Use `ls -l /dev/ttyUSB*` on the Pi to verify hardware connections
- Ensure all Arduinos have unique, stable USB port assignments (use udev rules if needed)
