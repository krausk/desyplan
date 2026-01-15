/**
 * Relay-Aware LED Retrofit Firmware
 * Target: Arduino Mega 2560
 * Role: I2C Slave
 *
 * Logic:
 * - Receives 12 bytes (96 bits) from Master via I2C.
 * - Comparing received state with current state.
 * - Enforces minimum settling time for mechanical relays.
 */

#include <Wire.h>

// --- Configuration ---
#define I2C_ADDRESS 0x08 // CHANGE THIS for each board (0x08 - 0x0D)
#define NUM_LEDS 96
#define BYTES_PER_FRAME 12
#define MIN_TOGGLE_INTERVAL_MS 20

// --- Globals ---
// Placeholder pin mapping. Real hardware needs specific pin assignments.
// Using -1 for unassigned/overflow pins since Mega only has ~70 GPIOs.
// We map the first ~70 bits to valid digital pins 2-69 for demonstration.
int ledPins[NUM_LEDS];

byte currentLedState[BYTES_PER_FRAME];  // Helper to track bitset state
unsigned long lastToggleTime[NUM_LEDS]; // Timestamp for each relay

// Buffer for incoming I2C data
volatile byte incomingData[BYTES_PER_FRAME];
volatile bool newDataAvailable = false;

void setup() {
  // Initialize Pin Mapping
  // Simple map: bits 0-67 map to digital pins 2-69.
  // Bits 68-95 are ignored (-1) due to hardware limits.
  for (int i = 0; i < NUM_LEDS; i++) {
    if (i < 68) {
      ledPins[i] = i + 2;
    } else {
      ledPins[i] = -1;
    }
  }

  // Set Pin Modes
  for (int i = 0; i < NUM_LEDS; i++) {
    if (ledPins[i] != -1) {
      pinMode(ledPins[i], OUTPUT);
      digitalWrite(ledPins[i], LOW); // Start OFF
      lastToggleTime[i] = 0;
    }
  }

  // Clear state buffers
  memset(currentLedState, 0, BYTES_PER_FRAME);
  memset((void *)incomingData, 0, BYTES_PER_FRAME);

  // Initialize I2C
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveEvent);

  Serial.begin(115200);
  Serial.print("Slave Initialized on 0x");
  Serial.println(I2C_ADDRESS, HEX);
}

void loop() {
  if (newDataAvailable) {
    processLedState();
    newDataAvailable = false; // Acknowledgement
  }
}

// I2C Interrupt Handler
// Stores data into a buffer to keep ISR short.
void receiveEvent(int howMany) {
  if (howMany == BYTES_PER_FRAME) {
    for (int i = 0; i < BYTES_PER_FRAME; i++) {
      incomingData[i] = Wire.read();
    }
    newDataAvailable = true;
  } else {
    // Flush invalid packet
    while (Wire.available())
      Wire.read();
  }
}

// Main logic to update relays
void processLedState() {
  unsigned long now = millis();

  for (int byteIdx = 0; byteIdx < BYTES_PER_FRAME; byteIdx++) {
    byte incomingByte = incomingData[byteIdx];
    // Check if this byte has any changes compared to current known state
    // Optimization: if byte is same, skip bit checking
    // NOTE: We do bit checking anyway to enforce per-pin timing

    for (int bitIdx = 0; bitIdx < 8; bitIdx++) {
      int globalLedIndex = (byteIdx * 8) + bitIdx;

      // Safety check for array bounds
      if (globalLedIndex >= NUM_LEDS)
        continue;

      int pin = ledPins[globalLedIndex];
      if (pin == -1)
        continue;

      bool desiredState = (incomingByte >> bitIdx) & 0x01;
      bool currentState = digitalRead(pin); // Read actual pin state

      if (desiredState != currentState) {
        // Change requested
        if (now - lastToggleTime[globalLedIndex] >= MIN_TOGGLE_INTERVAL_MS) {
          digitalWrite(pin, desiredState ? HIGH : LOW);
          lastToggleTime[globalLedIndex] = now;
        } else {
          // Rate limited! We ignore this update to protect the relay.
          // The next frame will catch it if it persists.
        }
      }
    }
    // Update our shadow copy of state (optional, mainly for debugging logic)
    currentLedState[byteIdx] = incomingByte;
  }
}
