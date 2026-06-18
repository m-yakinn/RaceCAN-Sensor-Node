/*
 * RaceCAN Dashboard Receiver Example
 * Day 18: Receiver-side implementation proving protocol is implementable
 * 
 * Purpose:
 *   Demonstrates how a secondary ECU (dashboard, telemetry logger, BMS) would
 *   receive and unpack RaceCAN CAN messages. This proves the protocol is
 *   unambiguous: an independent implementation produces identical results
 *   as the transmitter.
 * 
 * Hardware:
 *   - Arduino Uno / Nano with MCP2515 CAN module
 *   - SPI pins: MOSI (D11), MISO (D12), SCK (D13), CS (D10)
 *   - INT pin: D2 (optional, for interrupt-driven reception)
 * 
 * CAN Bus:
 *   - 500 kbit/s
 *   - 11-bit IDs (0x100–0x105)
 *   - 8-byte fixed-length frames
 * 
 * Compilation:
 *   Install libraries:
 *     - Arduino CAN library (by Sandeep Mistry) or mcp2515.h
 *   Compile and upload to board
 * 
 * Usage:
 *   Open Serial Monitor (115200 baud) to see parsed CAN messages
 *   Example output:
 *     HEARTBEAT: State=0 (NORMAL), Uptime=10s
 *     VOLTAGE: 12.34V, Warn=0, Crit=0
 *     TEMPERATURE: 45.67C, Warn=0, Crit=0
 *     DRIVER: Throttle=50.0%, Brake=0.0%, RangeFault=0
 *     CURRENT: 5.43A, Warn=0, Crit=0
 *     FAULT_SUMMARY: V_crit=0, T_crit=0, Range=0, External=0
 */

#include <SPI.h>
#include <Wire.h>

// Mock MCP2515 driver (replace with real library for actual hardware)
// For this example, we'll use a simplified version
struct CANMessage {
    uint16_t id;
    uint8_t dlc;
    uint8_t data[8];
};

// ============================================================================
// Little-Endian Unpackers
// ============================================================================

/**
 * Extract unsigned 16-bit little-endian integer from byte array.
 * Example: data[0]=0xD2, data[1]=0x04 → returns 0x04D2 = 1234
 */
uint16_t unpack_u16_le(const uint8_t *data, int offset) {
    uint16_t low = data[offset];
    uint16_t high = data[offset + 1];
    return low | (high << 8);
}

/**
 * Extract signed 16-bit little-endian integer from byte array.
 * Handles two's complement for negative values.
 * Example: data[0]=0x50, data[1]=0xFB → returns -1200 (discharge current)
 */
int16_t unpack_i16_le(const uint8_t *data, int offset) {
    int16_t val = (int16_t)unpack_u16_le(data, offset);
    return val;
}

/**
 * Extract unsigned 8-bit value from byte array.
 */
uint8_t unpack_u8(const uint8_t *data, int offset) {
    return data[offset];
}

// ============================================================================
// Message Unpacking Functions
// ============================================================================

/**
 * Unpack 0x100 Heartbeat message.
 * 
 * Payload:
 *   [0]   Alive flag (always 1)
 *   [1]   State code (0=normal, 1=warning, 2=critical)
 *   [2:3] Uptime in seconds (uint16 LE)
 *   [4:7] Reserved
 */
void unpack_heartbeat(const CANMessage *msg) {
    uint8_t alive = unpack_u8(msg->data, 0);
    uint8_t state = unpack_u8(msg->data, 1);
    uint16_t uptime_sec = unpack_u16_le(msg->data, 2);
    
    const char *state_name;
    switch (state) {
        case 0: state_name = "NORMAL"; break;
        case 1: state_name = "WARNING"; break;
        case 2: state_name = "CRITICAL"; break;
        default: state_name = "UNKNOWN"; break;
    }
    
    Serial.print("HEARTBEAT: State=");
    Serial.print(state);
    Serial.print(" (");
    Serial.print(state_name);
    Serial.print("), Uptime=");
    Serial.print(uptime_sec);
    Serial.println("s");
}

/**
 * Unpack 0x101 Voltage Telemetry message.
 * 
 * Payload:
 *   [0:1] Battery voltage (int16 LE, units: 0.01V)
 *   [2]   Voltage warning flag (0 or 1)
 *   [3]   Voltage critical fault flag (0 or 1)
 *   [4:7] Reserved
 */
void unpack_voltage(const CANMessage *msg) {
    int16_t voltage_raw = unpack_i16_le(msg->data, 0);
    float voltage_v = voltage_raw / 100.0f;
    uint8_t warn = unpack_u8(msg->data, 2);
    uint8_t crit = unpack_u8(msg->data, 3);
    
    Serial.print("VOLTAGE: ");
    Serial.print(voltage_v);
    Serial.print("V, Warn=");
    Serial.print(warn);
    Serial.print(", Crit=");
    Serial.println(crit);
}

/**
 * Unpack 0x102 Temperature Telemetry message.
 * 
 * Payload:
 *   [0:1] Temperature (int16 LE, units: 0.01°C)
 *   [2]   Temperature warning flag (0 or 1)
 *   [3]   Temperature critical fault flag (0 or 1)
 *   [4:7] Reserved
 */
void unpack_temperature(const CANMessage *msg) {
    int16_t temp_raw = unpack_i16_le(msg->data, 0);
    float temp_c = temp_raw / 100.0f;
    uint8_t warn = unpack_u8(msg->data, 2);
    uint8_t crit = unpack_u8(msg->data, 3);
    
    Serial.print("TEMPERATURE: ");
    Serial.print(temp_c);
    Serial.print("C, Warn=");
    Serial.print(warn);
    Serial.print(", Crit=");
    Serial.println(crit);
}

/**
 * Unpack 0x103 Driver Inputs message.
 * 
 * Payload:
 *   [0:1] Throttle position (int16 LE, units: 0.01%)
 *   [2:3] Brake position (int16 LE, units: 0.01%)
 *   [4]   Throttle sensor fault flag (0 or 1)
 *   [5]   Brake sensor fault flag (0 or 1)
 *   [6:7] Reserved
 */
void unpack_driver_inputs(const CANMessage *msg) {
    int16_t throttle_raw = unpack_i16_le(msg->data, 0);
    int16_t brake_raw = unpack_i16_le(msg->data, 2);
    float throttle_pct = throttle_raw / 100.0f;
    float brake_pct = brake_raw / 100.0f;
    uint8_t throttle_fault = unpack_u8(msg->data, 4);
    uint8_t brake_fault = unpack_u8(msg->data, 5);
    
    Serial.print("DRIVER: Throttle=");
    Serial.print(throttle_pct);
    Serial.print("%, Brake=");
    Serial.print(brake_pct);
    Serial.print("%, ThrottleFault=");
    Serial.print(throttle_fault);
    Serial.print(", BrakeFault=");
    Serial.println(brake_fault);
}

/**
 * Unpack 0x104 Current Telemetry message.
 * 
 * Payload:
 *   [0:1] Pack current (int16 LE, units: 0.01A, signed for bidirectional)
 *   [2]   Current warning flag (0 or 1)
 *   [3]   Current critical fault flag (0 or 1)
 *   [4:7] Reserved
 */
void unpack_current(const CANMessage *msg) {
    int16_t current_raw = unpack_i16_le(msg->data, 0);
    float current_a = current_raw / 100.0f;
    uint8_t warn = unpack_u8(msg->data, 2);
    uint8_t crit = unpack_u8(msg->data, 3);
    
    Serial.print("CURRENT: ");
    Serial.print(current_a);
    Serial.print("A, Warn=");
    Serial.print(warn);
    Serial.print(", Crit=");
    Serial.println(crit);
}

/**
 * Unpack 0x105 Fault Summary message.
 * 
 * Payload:
 *   [0] Bit 0: Voltage critical fault
 *   [0] Bit 1: Temperature critical fault
 *   [0] Bit 2: Throttle sensor fault
 *   [0] Bit 3: Brake sensor fault
 *   [0] Bit 4: Current critical fault
 *   [0] Bit 5: External fault / Communication fault
 *   [0] Bit 6–7: Reserved
 *   [1:7] Reserved
 */
void unpack_fault_summary(const CANMessage *msg) {
    uint8_t fault_byte = unpack_u8(msg->data, 0);
    
    uint8_t v_crit = (fault_byte >> 0) & 1;
    uint8_t t_crit = (fault_byte >> 1) & 1;
    uint8_t throttle = (fault_byte >> 2) & 1;
    uint8_t brake = (fault_byte >> 3) & 1;
    uint8_t i_crit = (fault_byte >> 4) & 1;
    uint8_t external = (fault_byte >> 5) & 1;
    
    Serial.print("FAULT_SUMMARY: V_crit=");
    Serial.print(v_crit);
    Serial.print(", T_crit=");
    Serial.print(t_crit);
    Serial.print(", Throttle=");
    Serial.print(throttle);
    Serial.print(", Brake=");
    Serial.print(brake);
    Serial.print(", I_crit=");
    Serial.print(i_crit);
    Serial.print(", External=");
    Serial.println(external);
}

// ============================================================================
// Main Dispatcher
// ============================================================================

/**
 * Route received CAN message to appropriate unpacker.
 */
void process_can_message(const CANMessage *msg) {
    switch (msg->id) {
        case 0x100:
            unpack_heartbeat(msg);
            break;
        case 0x101:
            unpack_voltage(msg);
            break;
        case 0x102:
            unpack_temperature(msg);
            break;
        case 0x103:
            unpack_driver_inputs(msg);
            break;
        case 0x104:
            unpack_current(msg);
            break;
        case 0x105:
            unpack_fault_summary(msg);
            break;
        default:
            Serial.print("Unknown message ID: 0x");
            Serial.println(msg->id, HEX);
            break;
    }
}

// ============================================================================
// Arduino Setup & Loop (Stub for Simulation)
// ============================================================================

void setup() {
    Serial.begin(115200);
    // TODO: Initialize MCP2515 CAN controller
    // TODO: Set CAN bus speed to 500 kbit/s
    // TODO: Set up interrupt handler for message reception (optional)
    Serial.println("RaceCAN Dashboard Receiver initialized");
}

void loop() {
    // TODO: Poll MCP2515 for new messages (or wait for interrupt)
    // CANMessage msg = can_read();
    // if (msg.dlc > 0) {
    //     process_can_message(&msg);
    // }
    delay(10);
}

/*
 * Integration with Real Hardware:
 * 
 * To use this on actual hardware with an MCP2515 module:
 * 
 * 1. Install the mcp2515 library:
 *    - Arduino IDE: Sketch → Include Library → Manage Libraries
 *    - Search for "MCP2515" and install by Corrado Smerieri
 * 
 * 2. Replace the stub setup() with real initialization:
 *    #include <mcp2515.h>
 *    
 *    MCP2515 mcp2515(10);  // CS pin 10
 *    
 *    void setup() {
 *        Serial.begin(115200);
 *        SPI.begin();
 *        mcp2515.reset();
 *        mcp2515.setBitrate(CAN_500KBPS, MCP_8MHZ);
 *        mcp2515.setNormalMode();
 *        Serial.println("CAN bus initialized");
 *    }
 * 
 * 3. Replace loop() with real message reception:
 *    void loop() {
 *        struct can_frame canMsg;
 *        if (mcp2515.readMessage(&canMsg) == MCP2515::ERROR_OK) {
 *            CANMessage msg;
 *            msg.id = canMsg.can_id;
 *            msg.dlc = canMsg.can_dlc;
 *            memcpy(msg.data, canMsg.data, 8);
 *            process_can_message(&msg);
 *        }
 *    }
 * 
 * Wiring (Arduino Uno):
 *   MCP2515 Module → Arduino
 *   VCC → 5V
 *   GND → GND
 *   CS → D10
 *   MOSI → D11
 *   MISO → D12
 *   SCK → D13
 *   INT → D2 (optional, for interrupt-driven mode)
 */
