# Wiring

Detailed Wiring Breakdown

## 1. The Serial Communication Bus (USB)

Instead of a complex I2C daisy-chain, all six Arduino Mega 2560 controllers are connected to the Raspberry Pi via standard USB Serial.

- **USB Connection**: Connect each Arduino Mega to the Raspberry Pi using a USB Type-A to Type-B cable.
- **USB Hub**: Since the Raspberry Pi has limited USB ports, a **powered USB 2.0/3.0 Hub** is required to connect all 6 Arduinos.
- **Port Mapping**: The system identifies slaves by their serial port (e.g., `/dev/ttyUSB0` through `/dev/ttyUSB5`).

## 2. Power Management (The "Common Ground" Rule)

The most common cause of failure in large LED projects is grounding issues.

- **Logic Power**: The Arduinos receive logic power directly through their USB cables. Ensure the USB hub is powered to avoid overloading the Raspberry Pi's power supply.
- **LED Load Power**: Keep the original heavy-duty power supplies for the beige driver boards.
- **Common Ground**: You **MUST** connect the Ground (GND) of the Raspberry Pi (or the USB Hub's power supply ground), the Ground of every Arduino, and the Ground of the original LED power supplies together. If they don't share a ground, the signal from the Arduino won't have a reference, and the LEDs will flicker or stay off.

## 3. Connecting to the Beige Driver Boards

Each Esser board you removed had ribbon cables leading to the beige boards.

- The Arduinos should be fitted with **Screw Terminal Shields**.
- The wires that used to go into the Esser terminal blocks now go into the Arduino digital pins (D22, D23, etc.).
- Since you have 576 drivers and 6 Arduinos, each Arduino is responsible for exactly 96 wires.

```
RASPBERRY PI (MASTER)               5V POWERED USB HUB
      +---------------------+              +-----------------------+
      |      [ USB Port ]---|------------->| [Port 1] <---[USB]--->| Arduino #1
      |      [  GND/PWR ]   |              | [Port 2] <---[USB]--->| Arduino #2
      +----------|----------+              | [Port 3] <---[USB]--->| Arduino #3
                 |                         | [Port 4] <---[USB]--->| Arduino #4
                 |                         | [Port 5] <---[USB]--->| Arduino #5
                 |                         | [Port 6] <---[USB]--->| Arduino #6
                 |                         +-----------|-----------+
                 |                                     |
                 |                                     |          ARDUINO MEGA (Example)
                 |                                     |        +-----------------------+
                 |                                     +------->| USB Port (Data/Power) |
                 |                                              | GND                   |
                 |               +----------------------------->| [Digital Pins 22-53]--+
                 |               |                              +-----------|-----------+
                 |               |                                          |
                 |               |                                  TO DRIVER BOARDS
                 |               |
                 |      ORIGINAL LED POWER SUPPLY (HIGH CURRENT)
                 |      +--------------------------------------+
                 +----->| [-] GROUND (V-)                      |
                        | [+] 5V DC   (V+) --------------------+-----> TO ALL 12
                        +--------------------------------------+       DRIVER BOARDS
```