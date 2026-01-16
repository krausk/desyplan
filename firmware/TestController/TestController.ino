/**
 * Simplified Test Controller Firmware
 * Target: Arduino UNO
 * Role: I2C Slave
 *
 * Purpose: Simple 3-LED test setup for development and testing
 * Controls 3 LEDs on pins 13, 12, and 8
 *
 * Logic:
 * - Receives 1 byte (3 bits) from Master via I2C
 * - Updates LED states with optional rate limiting
 */

#include <Wire.h>

// --- Configuration ---
#define I2C_ADDRESS 0x08
#define NUM_LEDS 3
#define MIN_TOGGLE_INTERVAL_MS 10  // Faster for LEDs vs mechanical relays

// Pin mapping for the 3 LEDs
const int ledPins[NUM_LEDS] = {13, 12, 8};

// State tracking
bool currentLedState[NUM_LEDS];
unsigned long lastToggleTime[NUM_LEDS];

// Buffer for incoming I2C data
volatile byte incomingData = 0;
volatile bool newDataAvailable = false;

void setup() {
  // Initialize pins
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
    currentLedState[i] = false;
    lastToggleTime[i] = 0;
  }

  // Initialize I2C
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveEvent);

  Serial.begin(115200);
  Serial.print("Test Controller Initialized on 0x");
  Serial.println(I2C_ADDRESS, HEX);
  Serial.print("Controlling ");
  Serial.print(NUM_LEDS);
  Serial.println(" LEDs on pins: 13, 12, 8");
}

void loop() {
  if (newDataAvailable) {
    processLedState();
    newDataAvailable = false;
  }
}

// I2C Interrupt Handler
void receiveEvent(int howMany) {
  if (howMany >= 1) {
    incomingData = Wire.read();
    newDataAvailable = true;

    // Flush any remaining bytes
    while (Wire.available()) {
      Wire.read();
    }
  }
}

// Update LED states based on received data
void processLedState() {
  unsigned long now = millis();

  for (int i = 0; i < NUM_LEDS; i++) {
    bool desiredState = (incomingData >> i) & 0x01;

    if (desiredState != currentLedState[i]) {
      // State change requested
      if (now - lastToggleTime[i] >= MIN_TOGGLE_INTERVAL_MS) {
        digitalWrite(ledPins[i], desiredState ? HIGH : LOW);
        currentLedState[i] = desiredState;
        lastToggleTime[i] = now;

        // Debug output
        Serial.print("LED ");
        Serial.print(i);
        Serial.print(" (Pin ");
        Serial.print(ledPins[i]);
        Serial.print("): ");
        Serial.println(desiredState ? "ON" : "OFF");
      }
    }
  }
}
