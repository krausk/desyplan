/**
 * LED Matrix Retrofit - Slave Firmware
 * Target: Arduino Mega 2560
 * 
 * Logic:
 * - Configurable I2C Address (0x08 - 0x0D)
 * - Receives 12 bytes of data (96 bits) via I2C
 * - Maps bits to physical pins and updates them
 * 
 * Wiring:
 * - SDA: Pin 20
 * - SCL: Pin 21
 * - GND: Common Ground with Master
 */

#include <Wire.h>

// --- CONFIGURATION ---
// CHANGE THIS ID FOR EACH BOARD: 0 to 5
#define BOARD_ID 0

// Base address is 0x08. Board 0->0x08, Board 1->0x09, etc.
const int SLAVE_ADDRESS = 0x08 + BOARD_ID;
const int NUM_LEDS = 96;
const int BYTES_PER_FRAME = 12; // 96 bits / 8

// --- PIN MAPPING ---
// Map logical LED index (0-95) to physical Mega Pin
// TODO: USER MUST FILL THIS WITH ACTUAL WIRING
const int PROGMEM PIN_MAP[NUM_LEDS] = {
  // Example placeholder mapping (Pins 2-53, then A0-A15 mixed)
  // 0-9
  2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
  // 10-19
  12, 13, 22, 23, 24, 25, 26, 27, 28, 29,
  // 20-29
  30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
  // 30-39
  40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
  // 40-49
  50, 51, 52, 53, A0, A1, A2, A3, A4, A5,
  // 50-59 (Extended placeholders)
  A6, A7, A8, A9, A10, A11, A12, A13, A14, A15,
  // 60-95 (Fill with valid digital pins not used by I2C)
  // Repeating for placeholder purposes - REPLACE THESE
  2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 22, 23, 24, 25, 26, 27, 28, 29,
  30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45
};

// Buffer to store received data
volatile uint8_t ledBuffer[BYTES_PER_FRAME];
volatile bool newDataAvailable = false;

void setup() {
  // Initialize Pins
  for (int i = 0; i < NUM_LEDS; i++) {
    int pin = pgm_read_word_near(PIN_MAP + i);
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW); // Start OFF
  }

  // Initialize I2C
  Wire.begin(SLAVE_ADDRESS);
  Wire.onReceive(receiveEvent);

  // Debug Serial
  Serial.begin(115200);
  Serial.print("Slave Initialized. Address: 0x");
  Serial.println(SLAVE_ADDRESS, HEX);
}

void loop() {
  if (newDataAvailable) {
    updateLEDs();
    newDataAvailable = false;
  }
}

// Interrupt Handler for I2C Receive
void receiveEvent(int howMany) {
  if (howMany >= BYTES_PER_FRAME) {
    for (int i = 0; i < BYTES_PER_FRAME; i++) {
      ledBuffer[i] = Wire.read();
    }
    // Discard any extra bytes
    while (Wire.available()) {
      Wire.read();
    }
    newDataAvailable = true;
  }
}

void updateLEDs() {
  for (int i = 0; i < NUM_LEDS; i++) {
    int byteIndex = i / 8;
    int bitIndex = i % 8;
    
    // Check if bit is set
    bool state = (ledBuffer[byteIndex] >> bitIndex) & 0x01;
    
    int pin = pgm_read_word_near(PIN_MAP + i);
    digitalWrite(pin, state ? HIGH : LOW);
  }
}
