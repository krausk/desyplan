# Relay Controller Retrofit Project

A modular USB Serial-based controller system with support for multiple environments.

## Environments

### Production
- **Master**: Raspberry Pi (Python)
- **Slaves**: 6x Arduino Mega 2560
- **Outputs**: 576 mechanical relays
- **Purpose**: Full fire alarm panel retrofit

### Test
- **Master**: Raspberry Pi (Python)
- **Slave**: 1x Arduino UNO
- **Outputs**: 3 LEDs (pins 13, 12, 11)
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
2. Wire 3 LEDs to Arduino UNO (pins 13, 12, 11)
3. Connect UNO to Raspberry Pi via USB cable
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

All Arduino Megas use the same firmware (no address configuration needed).
Flash each one:
```bash
./build.sh --port /dev/ttyUSB0 --env production
```

#### 3. Raspberry Pi Setup
1. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
2. Connect all 6 Arduino Megas via USB (use powered USB hub if needed)
3. Verify connections: `ls -l /dev/ttyUSB*` (should show /dev/ttyUSB0 through /dev/ttyUSB5)

#### 4. Run Controller

**Option A: Web Interface (Recommended)**

```bash
# Start the web interface
./start_web.sh

# Or specify environment
./start_web.sh --env test
./start_web.sh --env production

# Access at http://raspberry-pi-ip:5000
```

The web interface provides:
- Individual LED on/off controls
- Animation selection dropdown
- Real-time status updates
- Simple, responsive UI

**Option B: Command Line**

```bash
# Run main animation loop
python3 controller/main.py

# Or run diagnostic test
python3 controller/main.py --test

# Or scan serial ports
python3 controller/main.py --scan
```

## Documentation

- **[WEB_INTERFACE.md](WEB_INTERFACE.md)** - Complete web interface documentation and API reference
- **[TEST_SETUP.md](TEST_SETUP.md)** - Complete guide for 3-LED test setup
- **[CLAUDE.md](CLAUDE.md)** - Developer reference and architecture details
- **docs/hardware_logic.md** - Hardware wiring and specifications
- **docs/led_assignments_implementation.md** - LED position system documentation

## Web Interface

The web interface provides an easy-to-use control panel accessible from any device on your network.

### Features
- **Manual Control**: Toggle individual LEDs/relays on and off
- **Animation Control**: Select and start animations from a dropdown menu
- **Real-time Updates**: Live status display and LED state visualization
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Environment Aware**: Automatically adapts to test or production configuration

### Starting the Web Interface

**Method 1: Simple Startup Script**
```bash
./start_web.sh
# Access at http://raspberry-pi-ip:5000
```

**Method 2: Direct Python**
```bash
python3 controller/web_server.py --host 0.0.0.0 --port 5000
```

**Method 3: Run as System Service (Auto-start on boot)**

1. Edit the service file to match your setup:
   ```bash
   nano relay-controller-web.service
   # Update User= and paths if needed
   ```

2. Install the service:
   ```bash
   sudo cp relay-controller-web.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable relay-controller-web
   sudo systemctl start relay-controller-web
   ```

3. Check status:
   ```bash
   sudo systemctl status relay-controller-web
   ```

### API Endpoints

The web server also provides a REST API:
- `GET /api/status` - Get current system status
- `POST /api/led/<index>` - Toggle specific LED
- `POST /api/all_leds` - Set all LEDs to same state
- `GET /api/animations` - List available animations
- `POST /api/animation/start` - Start an animation
- `POST /api/animation/stop` - Stop current animation

### LED Position System

The LED position system allows you to map LEDs to specific pins and manage multiple sets of position mappings.

**Access the LED Position Interface:**
```
http://raspberry-pi-ip:5000/led-position
```

**Key Features:**
- **Visual Map**: Click on the DESY plan to add new LEDs
- **Pin Assignment**: Assign each LED to a specific pin number
- **Multiple Sets**: Create and switch between different position sets
- **Trigger Mode**: Click on LEDs to trigger them via their assigned pins
- **Visual Indicators**: Green for LEDs with pins, blue for LEDs without pins

**How to Use:**

1. **Add a New LED:**
   - Navigate to `/led-position`
   - Click on the map to add a new LED
   - Enter the pin number in the popup panel
   - Click "Save" to persist the assignment

2. **Switch Position Sets:**
   - Use the dropdown menu to select a different set
   - The map and assignments will update automatically

3. **Trigger an LED:**
   - Navigate to `/led-position`
   - Switch to "Trigger" mode
   - Click on an LED on the map
   - The LED will be triggered via its assigned pin

**Configuration:**
- Assignments are stored in `config.yaml` under the `led_assignments` section
- Each set contains LED mappings with position (x, y) and pin number
- Pin mapping is independent of environment configuration

## Configuration

The system is configured via `config.yaml`. Key parameters:
- `active_environment`: Switch between `test` and `production`
- Hardware settings: slave count, serial ports, pin mappings
- Timing parameters: relay delays, toggle intervals
- Firmware paths: source files and board types

Override environment at runtime:
```bash
python3 controller/main.py --env test
```

## Troubleshooting

- **No response from slaves?**
  - Check USB connections: `ls -l /dev/ttyUSB*`
  - Run `python3 controller/main.py --scan` to verify connections
  - Ensure common ground between Pi and Arduinos (12V relay supply)
  - Check if Arduino is enumerated: `dmesg | grep ttyUSB`

- **Flickering or erratic behavior?**
  - Verify power supply is adequate (use powered USB hub for production)
  - Ensure MIN_TOGGLE_INTERVAL timing is respected
  - Check USB cable quality (bad cables cause communication errors)

- **Firmware upload fails?**
  - Check USB cable and port (`ls /dev/tty{USB,ACM}*`)
  - Verify user is in `dialout` group: `sudo usermod -a -G dialout $USER`
  - Try different USB port or cable

- **Serial port assignments change on reboot?**
  - Create udev rules to assign stable device names based on serial numbers
  - See `/etc/udev/rules.d/99-arduino.rules` for examples