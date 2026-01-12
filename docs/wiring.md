# Wiring

Detailed Wiring Breakdown
1. The I2C Communication Bus (Daisy-Chain)
All seven controllers (1 Pi + 6 Megas) share the same signal wires. This is called a bus.

SDA (Data Line): Connect Raspberry Pi GPIO 2 to Mega #1 Pin 20. From there, jump a wire to Mega #2 Pin 20, then Mega #3, and so on.

SCL (Clock Line): Connect Raspberry Pi GPIO 3 to Mega #1 Pin 21. Jump this to Mega #2 Pin 21, and continue the chain to Mega #6.

Pull-up Resistors: I2C is an "open-drain" bus. You must connect one 4.7kΩ resistor from the SDA line to 5V (Logic), and one 4.7kΩ resistor from the SCL line to 5V (Logic). Without these, the bus will stay "Low" and no data will move.

2. Power Management (The "Common Ground" Rule)
The most common cause of failure in large LED projects is grounding issues.

Logic Power: Power the Raspberry Pi and the 6 Arduino Megas from a stable 5V supply (or via USB).

LED Load Power: Keep the original heavy-duty power supplies for the beige driver boards.

Common Ground: You MUST connect the Ground (GND) of the Raspberry Pi, the Ground of every Arduino, and the Ground of the original LED power supplies together. If they don't share a ground, the signal from the Arduino won't have a reference, and the LEDs will flicker or stay off.

3. Connecting to the Beige Driver Boards
Each Esser board you removed had ribbon cables leading to the beige boards.

The Arduinos should be fitted with Screw Terminal Shields.

The wires that used to go into the Esser terminal blocks now go into the Arduino digital pins (D22, D23, etc.).

Since you have 576 drivers and 6 Arduinos, each Arduino is responsible for exactly 96 wires (if direct-driving) or a combination of Rows/Columns (if the beige boards are multiplexed).

```
RASPBERRY PI (MASTER)               5V LOGIC POWER SUPPLY
      +---------------------+              +-----------------------+
      |      [ GPIO 2 ] SDA |<-------------|--[ 4.7k Ohm Resistor ]|--+ 5V
      |      [ GPIO 3 ] SCL |<-------+-----|--[ 4.7k Ohm Resistor ]|--+
      |      [  GND   ] GND |<---+   |     +-----------------------+
      +----------|----------+    |   |
                 |               |   |          ARDUINO MEGA #1 (0x08)
                 |               |   |        +-----------------------+
                 +---------------|---|------->| SDA (Pin 20)          |
                 |               +---|------->| SCL (Pin 21)          |
                 |               |   +------->| GND                   |
                 |               |            | 5V IN (Logic) <-------+ 5V
                 |               |            | [Digital Pins 22-53]--+--> TO DRIVER
                 |               |            +-----------------------+    BOARD #1
                 |               |                       |
                 |               |             DAISY CHAIN CONTINUES...
                 |               |                       |
                 |               |              ARDUINO MEGA #6 (0x0D)
                 |               |            +-----------------------+
                 |               +----------->| SDA (Pin 20)          |
                 |               +----------->| SCL (Pin 21)          |
                 +--------------------------->| GND                   |
                 |                            | 5V IN (Logic) <-------+ 5V
                 |                            | [Digital Pins 22-53]--+--> TO DRIVER
                 |                            +-----------------------+    BOARD #6
                 |
                 |      ORIGINAL LED POWER SUPPLY (HIGH CURRENT)
                 |      +--------------------------------------+
                 +----->| [-] GROUND (V-)                      |
                        | [+] 5V DC   (V+) --------------------+-----> TO ALL 12
                        +--------------------------------------+       DRIVER BOARDS
```

See https://www.thegeekpub.com/18263/raspberry-pi-to-arduino-i2c-communication/