# Test Setup Guide - 3 LED Configuration

This guide explains how to use the simplified test setup with 1 Arduino UNO and 3 LEDs for development and testing.

## Hardware Setup

### Required Components
- 1x Raspberry Pi (any model with USB ports)
- 1x Arduino UNO
- 1x USB Cable (Type-A to Type-B for UNO)
- 3x LEDs (or use Arduino's built-in LED on pin 13)
- 3x 220Ω resistors (if using external LEDs)
- Jumper wires
- Breadboard (optional)

### Wiring Diagram

```
Raspberry Pi                Arduino UNO
-----------                -----------
USB Port 1 <──────────────> USB Port
                             (Serial)

Arduino UNO Pins:
- Pin 13 → LED1 (+ resistor) → GND  [Built-in LED also works]
- Pin 12 → LED2 (+ resistor) → GND
- Pin 11  → LED3 (+ resistor) → GND
```

**Note**: Direct USB connection provides both power and communication. No level shifter or separate power supply is needed for this test setup.

## Software Configuration

The system uses `config.yaml` to manage different environments. The test environment is already configured for Serial communication.

### 1. Verify Configuration

Check `config.yaml`:

```yaml
active_environment: test  # Should be set to 'test'

environments:
  test:
    description: "Test setup with 1 Arduino UNO controlling 3 LEDs"
    hardware:
      controller_type: "Arduino UNO"
      num_slaves: 1
      leds_per_slave: 3
      total_leds: 3
      serial_ports: ["/dev/ttyUSB0"]
      serial_baudrate: 115200
      pin_mapping:
        0: 13  # Built-in LED
        1: 12
        2: 11
    timing:
      min_relay_delay: 0.1  # 100ms for visible LED changes
      min_toggle_interval_ms: 10  # LEDs can switch faster
    firmware:
      source: "firmware/TestController/TestController.ino"
      board: "arduino:avr:uno"
      pins: [13, 12, 11]
```

### 2. Install Dependencies

On your **development machine** (for compiling Arduino firmware):

```bash
# Install arduino-cli
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Add to PATH if needed
export PATH=$PATH:$HOME/bin

# Install Arduino AVR core
arduino-cli core install arduino:avr
```

On the **Raspberry Pi** (for running Python controller):

```bash
cd /home/tino/Code/desyplan
pip3 install -r requirements.txt
```

## Deployment Steps

### Step 1: Compile and Flash Arduino Firmware

**Option A: Using the build script (recommended)**

```bash
# Compile only (verify it works)
./build.sh --compile-only

# Compile and upload to Arduino UNO on /dev/ttyUSB0
./build.sh --port /dev/ttyUSB0

# Or on /dev/ttyACM0 (common for UNO)
./build.sh --port /dev/ttyACM0
```

**Option B: Using Arduino IDE**

1. Open `firmware/TestController/TestController.ino`
2. Select Board: "Arduino UNO"
3. Select Port: (your Arduino's port)
4. Click Upload

**Option C: Manual arduino-cli**

```bash
cd firmware/TestController
arduino-cli compile --fqbn arduino:avr:uno .
arduino-cli upload --fqbn arduino:avr:uno --port /dev/ttyUSB0 .
```

### Step 2: Verify Serial Connection on Raspberry Pi

```bash
# List all serial ports to find your Arduino
ls -l /dev/tty* | grep -E 'USB|ACM'

# Or use arduino-cli to detect the board
arduino-cli board list
```

Expected output should show `/dev/ttyUSB0` or `/dev/ttyACM0` (or similar).

### Step 3: Test the Python Controller

**Option A: Web Interface (Recommended)**

```bash
# Start the web interface
./start_web.sh --env test

# Open in browser: http://raspberry-pi-ip:5000
```

The web interface lets you:
- Click individual LEDs to turn them on/off
- Select animations from the dropdown
- See real-time status updates

**Option B: Command Line**

```bash
cd controller

# Check serial connections
python3 main.py --scan

# Run simple test patterns (recommended for 3-LED setup)
python3 simple_test.py

# Or run the standard animation loop
python3 main.py --test
```

## Available Test Scripts

### `simple_test.py` - Recommended for 3 LEDs

Runs patterns optimized for 3 LEDs:
- All On/Off
- Sequential lighting
- Chase (Knight Rider style)
- Blink all
- Binary counting (0-7)
- Alternating pattern

```bash
python3 controller/simple_test.py
```

### `main.py` - Standard Controller

Works with both environments. For test setup:

```bash
# Scan serial ports
python3 controller/main.py --scan

# Run diagnostic test
python3 controller/main.py --test

# Run animations (RandomTwinkle, ScanningChase, LarsonScanner)
python3 controller/main.py
```

## Switching Between Environments

### Method 1: Edit config.yaml

Change the `active_environment` in `config.yaml`:

```yaml
active_environment: test  # or 'production'
```

### Method 2: Command-line Override

```bash
# Run in test mode
python3 controller/main.py --env test

# Run in production mode
python3 controller/main.py --env production
```

## Troubleshooting

### Arduino Not Detected

```bash
# List available serial ports
arduino-cli board list

# Or using ls
ls -l /dev/tty{USB,ACM}*

# Check permissions (add user to dialout group if needed)
sudo usermod -a -G dialout $USER
# Log out and back in for changes to take effect
```

### Serial Connection Issues

1. Check if the USB cable is securely connected.
2. Verify the port in `config.yaml` matches the one found with `arduino-cli board list`.
3. Check permissions:
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in for changes to take effect
   ```
4. Check for kernel errors:
   ```bash
   dmesg | grep -E 'tty|usb'
   ```

### LEDs Not Lighting Up

1. Check wiring (ensure LEDs are connected to the correct pins: 13, 12, 8).
2. Test with Arduino Serial Monitor:
   - Open Serial Monitor at 115200 baud.
   - You should see "Test Controller Initialized (USB Serial)".
   - LED changes should print "LED X (Pin Y): ON/OFF".
3. Check LED polarity (long leg = positive).
4. Verify resistor values (220Ω recommended).

### Python Import Errors

```bash
# Ensure all dependencies are installed
pip3 install -r requirements.txt

# Verify Python can find modules
cd controller
python3 -c "from config_loader import Config; print('OK')"
```

## Development Workflow

1. **Make changes to firmware** in `firmware/TestController/TestController.ino`
2. **Compile and upload**: `./build.sh --port /dev/ttyUSB0`
3. **Test on Raspberry Pi**: `python3 controller/simple_test.py`
4. **Iterate** as needed

When ready to deploy to production:
1. Change `active_environment: production` in `config.yaml`
2. Flash each of the 6 Arduino Megas with `firmware/SlaveController/SlaveController.ino`
3. Run on production hardware

## Next Steps

- Create custom animations by modifying `controller/animation.py`
- Add new patterns to `simple_test.py`
- Test timing constraints for relay-safe operation
- Monitor Serial output from Arduino for debugging

## Reference

- Main documentation: `README.md`
- Hardware details: `docs/hardware_logic.md`
- Claude Code instructions: `CLAUDE.md`
