/**
 * Relay-Aware LED Retrofit Firmware
 * Target: Arduino Mega 2560
 * Role: USB Serial Slave
 *
 * Logic:
 * - Receives 12 bytes (96 bits) from Master via USB Serial.
 * - Protocol: [0xFF 0xAA] [LENGTH] [DATA...] [0x55 0xFF]
 * - Compares received state with current state.
 * - Enforces minimum settling time for mechanical relays.
 */

// --- Configuration ---
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

// Serial communication state machine
enum SerialState {
  WAITING_START1,    // Waiting for 0xFF
  WAITING_START2,    // Waiting for 0xAA
  WAITING_LENGTH,    // Waiting for length byte
  READING_DATA,      // Reading data bytes
  WAITING_END1,      // Waiting for 0x55
  WAITING_END2       // Waiting for 0xFF
};

SerialState serialState = WAITING_START1;
byte dataLength = 0;
byte dataBuffer[BYTES_PER_FRAME];
byte dataIndex = 0;

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
  memset(dataBuffer, 0, BYTES_PER_FRAME);

  // Initialize Serial
  Serial.begin(115200);

  // Startup message
  Serial.println("Slave Controller Initialized (USB Serial)");
  Serial.print("Managing ");
  Serial.print(NUM_LEDS);
  Serial.println(" relay outputs");
  Serial.println("Ready to receive commands...");
}

void loop() {
  // Process incoming serial data
  if (Serial.available() > 0) {
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
        serialState = WAITING_START1;  // Reset on error
      }
      break;

    case WAITING_LENGTH:
      dataLength = b;
      dataIndex = 0;
      if (dataLength > 0 && dataLength <= BYTES_PER_FRAME) {
        serialState = READING_DATA;
      } else {
        serialState = WAITING_START1;  // Invalid length, reset
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
        serialState = WAITING_START1;  // Reset on error
      }
      break;

    case WAITING_END2:
      if (b == 0xFF) {
        // Valid packet received! Process it.
        processLedState();
      }
      serialState = WAITING_START1;  // Always reset state
      break;
  }
}

// Main logic to update relays
void processLedState() {
  unsigned long now = millis();

  for (int byteIdx = 0; byteIdx < dataLength && byteIdx < BYTES_PER_FRAME; byteIdx++) {
    byte incomingByte = dataBuffer[byteIdx];

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
