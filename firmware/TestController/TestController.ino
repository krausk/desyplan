/**
 * Simplified Test Controller Firmware
 * Target: Arduino UNO
 * Role: USB Serial Slave
 *
 * Purpose: Simple 3-LED test setup for development and testing
 * Controls 3 LEDs on pins 13, 12, and 8
 *
 * Logic:
 * - Receives data from Master via USB Serial
 * - Protocol: [0xFF 0xAA] [LENGTH] [DATA...] [0x55 0xFF]
 * - Updates LED states with optional rate limiting
 */

// --- Configuration ---
#define NUM_LEDS 3
#define MIN_TOGGLE_INTERVAL_MS 10 // Faster for LEDs vs mechanical relays

// Pin mapping for the 3 LEDs
const int ledPins[NUM_LEDS] = {13, 12, 8};

// State tracking
bool currentLedState[NUM_LEDS];
unsigned long lastToggleTime[NUM_LEDS];

// Serial communication state machine
enum SerialState {
  WAITING_START1, // Waiting for 0xFF
  WAITING_START2, // Waiting for 0xAA
  WAITING_LENGTH, // Waiting for length byte
  READING_DATA,   // Reading data bytes
  WAITING_END1,   // Waiting for 0x55
  WAITING_END2    // Waiting for 0xFF
};

SerialState serialState = WAITING_START1;
byte dataLength = 0;
byte dataBuffer[16]; // Buffer for incoming data (max 16 bytes)
byte dataIndex = 0;

void setup() {
  // Initialize pins
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
    currentLedState[i] = false;
    lastToggleTime[i] = 0;
  }

  // Initialize Serial
  Serial.begin(115200);

  // Startup message
  Serial.println("Test Controller Initialized (USB Serial)");
  Serial.print("Controlling ");
  Serial.print(NUM_LEDS);
  Serial.println(" LEDs on pins: 13, 12, 8");
  Serial.println("Ready to receive commands...");
}

void loop() {
  // Process ALL available incoming serial data
  while (Serial.available() > 0) {
    byte incomingByte = Serial.read();
    processSerialByte(incomingByte);
  }
}

void processSerialByte(byte b) {
  switch (serialState) {
  case WAITING_START1:
    if (b == 0xFF) {
      serialState = WAITING_START2;
    }
    break;

  case WAITING_START2:
    if (b == 0xAA) {
      serialState = WAITING_LENGTH;
    } else {
      serialState = WAITING_START1; // Reset on error
    }
    break;

  case WAITING_LENGTH:
    dataLength = b;
    dataIndex = 0;
    if (dataLength > 0 && dataLength <= 16) {
      serialState = READING_DATA;
    } else {
      serialState = WAITING_START1; // Invalid length, reset
    }
    break;

  case READING_DATA:
    dataBuffer[dataIndex++] = b;
    if (dataIndex >= dataLength) {
      serialState = WAITING_END1;
    }
    break;

  case WAITING_END1:
    if (b == 0x55) {
      serialState = WAITING_END2;
    } else {
      serialState = WAITING_START1; // Reset on error
    }
    break;

  case WAITING_END2:
    if (b == 0xFF) {
      // Valid packet received! Process it.
      processLedData();
    }
    serialState = WAITING_START1; // Always reset state
    break;
  }
}

// Update LED states based on received data
void processLedData() {
  unsigned long now = millis();

  // For test controller, we only need 1 byte (3 bits for 3 LEDs)
  if (dataLength >= 1) {
    byte ledData = dataBuffer[0];

    for (int i = 0; i < NUM_LEDS; i++) {
      bool desiredState = (ledData >> i) & 0x01;

      if (desiredState != currentLedState[i]) {
        // State change requested
        if (now - lastToggleTime[i] >= MIN_TOGGLE_INTERVAL_MS) {
          digitalWrite(ledPins[i], desiredState ? HIGH : LOW);
          currentLedState[i] = desiredState;
          lastToggleTime[i] = now;

          // Debug output removed to prevent serial buffer choking
        }
      }
    }
  }
}
