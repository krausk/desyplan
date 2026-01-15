# Hardware Logic & Wiring Guide

## System Overview
This retrofit replaces the original controller of a fire alarm panel with a Raspberry Pi (Master) and six Arduino Mega 2560s (Slaves). The output devices are **WAS-DA2 driver boards** controlling **Panasonic TN2-12V** electromechanical relays.

## Relay Logic & Safety
### The Relay: Panasonic TN2-12V
- **Type**: DPDT (Double Pole Double Throw) electromechanical relay.
- **Coil Voltage**: 12V DC.
- **Operating Time**: Approx 2-3ms mechanical switching time.
- **Chatter**: Mechanical contacts bounce upon closing. Rapid toggling causes arcing and premature failure.

### Protection Logic
To protect the relays and ensure reliability:
1. **Settling Time**: A minimum software dead-time of **20ms-50ms** is enforced between toggles.
2. **Flyback Diodes**: 
   > [!WARNING]
   > When the transistor turns off the relay coil, the collapsing magnetic field generates a high-voltage spike (back EMF). **Flyback diodes (e.g., 1N4007) MUST be installed** across the coil terminals (Cathode to +12V, Anode to Transistor Collector) if not already present on the WAS-DA2 board. Failure to do this will destroy the NPN transistors and potentially the Arduinos.

## Wiring Specification

### Power Distribution
- **Logic Power (5V)**: Powers the Arduino Mega logic and the base of the NPN transistors.
- **Relay Power (12V)**: Dedicated supply for the relay coils.
- **Common Ground**:
  > [!IMPORTANT]
  > The **Ground (GND)** of the 5V supply (Arduino/Pi) and the 12V supply (Relays) MUST be connected together. Without a common ground, the transistors cannot switch the 12V load reference.

### Signal Chain
1. **Raspberry Pi**: Sends 96-bit state via I2C to Arduino.
2. **Arduino Mega**: Receiving Slave (Addr 0x08-0x0D). Maps bits to GPIO pins.
3. **GPIO Pin**: Outputs 5V High/Low.
4. **NPN Transistor**: Base receives 5V (via resistor). Collector sinks relay coil to Ground.
5. **Relay Coil**: Energizes from 12V rail, switching the contact.

## I2C Addressing
| Device | Address | Role |
| :--- | :--- | :--- |
| Raspberry Pi | Master | Animation Controller |
| Mega 1 | 0x08 | Slave Driver |
| Mega 2 | 0x09 | Slave Driver |
| Mega 3 | 0x0A | Slave Driver |
| Mega 4 | 0x0B | Slave Driver |
| Mega 5 | 0x0C | Slave Driver |
| Mega 6 | 0x0D | Slave Driver |

## Firmware Guard Constraints
- **MIN_INTERVAL**: 20ms (Hard limit in firmware).
- **MIN_RELAY_DELAY**: 50ms (Soft limit in Python controller for audible aesthetics).
