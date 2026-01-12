# LED Matrix Retrofit Project

Parameters:
- **Master**: Raspberry Pi (Python)
- **Slaves**: 6x Arduino Mega 2560
- **Display**: 576 LEDs

## Directory Structure
- `controller/`: Python source code for the Raspberry Pi.
- `firmware/`: Arduino C++ Sketch.
- `docs/`: Hardware wiring and setup guides.

## Quick Start

### 1. Firmware Setup
1.  Open `firmware/SlaveController/SlaveController.ino` in Arduino IDE.
2.  Update the `PIN_MAP` array to match your wiring.
3.  Flash each of the 6 Arduinos, changing the `#define BOARD_ID` for each (0 through 5).
    - Board ID 0 -> I2C Address 0x08
    - ...
    - Board ID 5 -> I2C Address 0x0D

### 2. Pi Setup
1.  Enable I2C on the Raspberry Pi (`sudo raspi-config`).
2.  Install dependencies:
    ```bash
    pip3 install -r requirements.txt
    ```

### 3. Run Controller
```bash
python3 controller/main.py
```
This will start the animation loop (Scanning Chase, Random Twinkle, etc.).

## Troubleshooting
- **No animate?** Check I2C wiring and addresses. Run `i2cdetect -y 1` on the Pi to see if the Slaves (0x08-0x0D) are detected.
- **Flickering?** Ensure common ground is solid and pull-up resistors are correct (4.7k).