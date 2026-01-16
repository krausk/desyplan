# Relay Controller Retrofit Project

A modular I2C-based controller system with support for multiple environments.

## Environments

### Production
- **Master**: Raspberry Pi (Python)
- **Slaves**: 6x Arduino Mega 2560
- **Outputs**: 576 mechanical relays
- **Purpose**: Full fire alarm panel retrofit

### Test (NEW!)
- **Master**: Raspberry Pi (Python)
- **Slave**: 1x Arduino UNO
- **Outputs**: 3 LEDs (pins 13, 12, 8)
- **Purpose**: Development and testing without full hardware

Switch environments by editing `config.yaml` or using the `--env` flag.

## Directory Structure
- `controller/`: Python source code for the Raspberry Pi
- `firmware/`: Arduino C++ sketches (production and test)
- `docs/`: Hardware wiring and setup guides
- `config.yaml`: Environment configuration
- `build.sh`: Firmware deployment script

## Quick Start

### Test Environment (Recommended for first-time setup)

See **[TEST_SETUP.md](TEST_SETUP.md)** for detailed instructions.

Quick steps:
1. Set `active_environment: test` in `config.yaml`
2. Wire 3 LEDs to Arduino UNO (pins 13, 12, 8)
3. Connect UNO to Raspberry Pi via I2C (with level shifter!)
4. Flash firmware: `./build.sh --port /dev/ttyUSB0`
5. Run test: `python3 controller/simple_test.py`

### Production Environment

#### 1. Configure Environment
Edit `config.yaml` and set:
```yaml
active_environment: production
```

#### 2. Flash Firmware to All 6 Arduinos
Use the build script:
```bash
./build.sh --compile-only  # Verify compilation
```

For each Arduino Mega, update the I2C address in `firmware/SlaveController/SlaveController.ino`:
```cpp
#define I2C_ADDRESS 0x08  // Change to 0x08, 0x09, 0x0A, 0x0B, 0x0C, or 0x0D
```

Then flash:
```bash
./build.sh --port /dev/ttyUSB0 --env production
```

#### 3. Raspberry Pi Setup
1. Enable I2C: `sudo raspi-config` → Interface Options → I2C
2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
3. Verify I2C: `i2cdetect -y 1` (should show 0x08-0x0D)

#### 4. Run Controller
```bash
# Run main animation loop
python3 controller/main.py

# Or run diagnostic test
python3 controller/main.py --test

# Or scan I2C bus
python3 controller/main.py --scan
```

## Documentation

- **[TEST_SETUP.md](TEST_SETUP.md)** - Complete guide for 3-LED test setup
- **[CLAUDE.md](CLAUDE.md)** - Developer reference and architecture details
- **docs/hardware_logic.md** - Hardware wiring and specifications

## Configuration

The system is configured via `config.yaml`. Key parameters:
- `active_environment`: Switch between `test` and `production`
- Hardware settings: slave count, I2C addresses, pin mappings
- Timing parameters: relay delays, toggle intervals
- Firmware paths: source files and board types

Override environment at runtime:
```bash
python3 controller/main.py --env test
```

## Troubleshooting

- **No response from slaves?**
  - Check I2C wiring and level shifter (3.3V ↔ 5V)
  - Run `i2cdetect -y 1` to verify addresses
  - Ensure common ground between Pi and Arduinos

- **Flickering or erratic behavior?**
  - Verify power supply is adequate
  - Check I2C pull-up resistors (4.7kΩ recommended)
  - Ensure MIN_TOGGLE_INTERVAL timing is respected

- **Firmware upload fails?**
  - Check USB cable and port (`ls /dev/tty{USB,ACM}*`)
  - Verify user is in `dialout` group: `sudo usermod -a -G dialout $USER`
  - Try different USB port or cable