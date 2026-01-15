# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a retrofit project replacing the original controller of a fire alarm panel with a **Raspberry Pi (Master)** controlling **6x Arduino Mega 2560s (Slaves)** via I2C. The system drives 576 electromechanical relays (Panasonic TN2-12V) through WAS-DA2 driver boards to create LED-like visual animations.

**Key Safety Constraint**: The output devices are mechanical relays, NOT LEDs. They have physical limitations:
- **Mechanical switching time**: ~2-3ms
- **Contact bounce and arcing**: Rapid toggling destroys relays
- **Minimum safe interval**: 20ms-50ms between state changes

## Architecture

### Hardware Topology
```
Raspberry Pi (Master, Python)
    ↓ I2C (3.3V ↔ 5V via level shifter)
    ↓
├─ Arduino Mega #1 (0x08) ─→ 96 relays via GPIO pins
├─ Arduino Mega #2 (0x09) ─→ 96 relays
├─ Arduino Mega #3 (0x0A) ─→ 96 relays
├─ Arduino Mega #4 (0x0B) ─→ 96 relays
├─ Arduino Mega #5 (0x0C) ─→ 96 relays
└─ Arduino Mega #6 (0x0D) ─→ 96 relays
```

Total: 576 independently controllable relays (treated as "LEDs" in code comments)

### Software Architecture

**Python Controller (Raspberry Pi)**:
- `controller/main.py` - Entry point, animation loop orchestration
- `controller/display_manager.py` - High-level display abstraction (buffer management)
- `controller/relay_controller.py` - I2C communication layer, frame dispatch to slaves
- `controller/animation.py` - Animation classes with relay-safe timing enforcement

**Arduino Firmware**:
- `firmware/SlaveController/SlaveController.ino` - I2C slave receiver with rate limiting

**Data Flow**:
1. Animation generates frame (576-bit array)
2. `DisplayManager` buffers state changes
3. `RelayController` splits frame into 6 chunks (96 bits each)
4. Each chunk packed into 12 bytes and sent via I2C to corresponding Arduino
5. Arduino unpacks, enforces MIN_TOGGLE_INTERVAL (20ms), updates GPIO pins

## Common Commands

### Python Development (Raspberry Pi)

Install dependencies:
```bash
pip3 install -r requirements.txt
```

Run the main animation loop:
```bash
python3 controller/main.py
```

Scan I2C bus to verify all 6 slaves are detected:
```bash
python3 controller/main.py --scan
```

Run diagnostic relay test pattern:
```bash
python3 controller/main.py --test
```

Verify I2C devices on the Pi hardware:
```bash
i2cdetect -y 1
# Should show devices at 0x08 through 0x0D
```

### Arduino Firmware (Development Machine)

Firmware location: `firmware/SlaveController/SlaveController.ino`

**CRITICAL**: Before flashing each Arduino, update the I2C address in the firmware:
```cpp
#define I2C_ADDRESS 0x08  // Change to 0x08, 0x09, 0x0A, 0x0B, 0x0C, or 0x0D
```

Flash using Arduino IDE or `arduino-cli`:
```bash
# Compile and upload (adjust port and FQBN as needed)
arduino-cli compile --fqbn arduino:avr:mega firmware/SlaveController
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:mega firmware/SlaveController
```

## Critical Implementation Details

### Relay Safety Timing

**Firmware-level protection** (`SlaveController.ino:18`):
- `MIN_TOGGLE_INTERVAL_MS = 20` - Hard limit enforced per GPIO pin
- If a state change is requested before 20ms has elapsed since the last toggle, it is silently ignored

**Software-level protection** (`animation.py:6`):
- `MIN_RELAY_DELAY = 0.05` (50ms) - Soft limit for aesthetics and additional safety margin
- All `Animation` subclasses use `safe_wait()` to enforce this delay

**When modifying animations**:
- Never reduce delays below 50ms without testing on actual hardware
- Limit the number of simultaneous relay changes per frame (mechanical stress)
- RandomTwinkle uses low `density` parameter for this reason

### Pin Mapping

The Arduino firmware currently uses a simplified placeholder mapping (`SlaveController.ino:38-43`):
- Bits 0-67 → Digital pins 2-69
- Bits 68-95 → Unmapped (set to -1)

**If hardware requires custom mapping**, edit the `ledPins[]` initialization in `setup()` to match the physical ribbon cable connections.

### I2C Protocol

**Frame structure**:
- Command byte: `0x00` (arbitrary, not interpreted by firmware)
- Data: 12 bytes representing 96 bits (LSB-first bit packing)

**Bit packing** (`relay_controller.py:71-81`):
- Each byte stores 8 relay states
- Bit 0 (LSB) = first relay in that group of 8

### Power Requirements

**Critical wiring rules** (from `docs/hardware_logic.md`):
- 5V logic supply for Pi and Arduinos
- 12V supply for relay coils
- **Common ground between all power supplies is mandatory**
- Flyback diodes (1N4007) must be present on relay coils to prevent back-EMF damage

## Hardware Constraints

**DO NOT**:
- Create animations with frame rates faster than 20 FPS (50ms/frame)
- Toggle large numbers of relays simultaneously (mechanical/acoustic issue)
- Skip the level shifter on I2C lines (Pi uses 3.3V, Arduino uses 5V)
- Power relay coils from Arduino pins (use transistor driver boards)

**DO**:
- Test new animations with `--test` flag first
- Verify I2C connectivity with `--scan` before troubleshooting animation issues
- Use `i2cdetect` on the Pi to verify hardware before blaming code
