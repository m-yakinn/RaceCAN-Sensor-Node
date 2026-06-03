/*
  RaceCAN Digital Kit
  Firmware Template

  Purpose:
  This template models the firmware that would run on a CAN based low voltage
  telemetry sensor node.

  This code is designed for learning and documentation first. It shows the
  structure of a real embedded system, including sensor reads, fault detection,
  message formatting, and telemetry transmission.

  Hardware note:
  This template uses placeholder CAN transmit functions. A real version would
  connect these functions to an MCP2515 CAN module, built in CAN peripheral,
  or another CAN controller.
*/

// ----------------------------
// Pin Definitions
// ----------------------------

const int THROTTLE_PIN = A0;
const int BRAKE_PIN = A1;
const int VOLTAGE_PIN = A2;
const int TEMPERATURE_PIN = A3;
const int CURRENT_PIN = A4;
const int EXTERNAL_FAULT_PIN = 2;

const int STATUS_LED_PIN = 13;
const int FAULT_LED_PIN = 12;
const int SHUTDOWN_OUTPUT_PIN = 11;

// ----------------------------
// CAN Message IDs
// ----------------------------

const unsigned int CAN_ID_HEARTBEAT = 0x100;
const unsigned int CAN_ID_VOLTAGE = 0x101;
const unsigned int CAN_ID_TEMPERATURE = 0x102;
const unsigned int CAN_ID_DRIVER_INPUTS = 0x103;
const unsigned int CAN_ID_CURRENT = 0x104;
const unsigned int CAN_ID_FAULTS = 0x105;

// ----------------------------
// Timing
// ----------------------------

const unsigned long SENSOR_UPDATE_INTERVAL_MS = 100;
const unsigned long HEARTBEAT_INTERVAL_MS = 500;

unsigned long previousSensorUpdateTime = 0;
unsigned long previousHeartbeatTime = 0;

// ----------------------------
// Thresholds
// ----------------------------

const float VOLTAGE_WARNING_THRESHOLD = 11.0;
const float UNDERVOLTAGE_FAULT_THRESHOLD = 10.5;

const float TEMPERATURE_WARNING_THRESHOLD = 50.0;
const float OVERTEMPERATURE_FAULT_THRESHOLD = 60.0;

const float CURRENT_WARNING_THRESHOLD = 12.0;
const float OVERCURRENT_FAULT_THRESHOLD = 15.0;

// ----------------------------
// Telemetry Values
// ----------------------------

float batteryVoltage = 0.0;
float temperatureC = 0.0;
float throttlePercent = 0.0;
float brakePercent = 0.0;
float currentA = 0.0;

bool externalFault = false;

// ----------------------------
// Fault Flags
// ----------------------------

bool voltageWarning = false;
bool undervoltageFault = false;

bool temperatureWarning = false;
bool overtemperatureFault = false;

bool currentWarning = false;
bool overcurrentFault = false;

bool sensorRangeFault = false;
bool communicationFault = false;

bool anyWarning = false;
bool anyCriticalFault = false;

// ----------------------------
// Setup
// ----------------------------

void setup() {
  Serial.begin(115200);

  pinMode(EXTERNAL_FAULT_PIN, INPUT_PULLUP);

  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(FAULT_LED_PIN, OUTPUT);
  pinMode(SHUTDOWN_OUTPUT_PIN, OUTPUT);

  digitalWrite(STATUS_LED_PIN, LOW);
  digitalWrite(FAULT_LED_PIN, LOW);
  digitalWrite(SHUTDOWN_OUTPUT_PIN, LOW);

  Serial.println("RaceCAN firmware template starting...");
  initializeCAN();
}

// ----------------------------
// Main Loop
// ----------------------------

void loop() {
  unsigned long currentTime = millis();

  if (currentTime - previousSensorUpdateTime >= SENSOR_UPDATE_INTERVAL_MS) {
    previousSensorUpdateTime = currentTime;

    readSensors();
    checkFaults();
    updateOutputs();

    sendVoltageMessage();
    sendTemperatureMessage();
    sendDriverInputsMessage();
    sendCurrentMessage();
    sendFaultMessage();

    printDebugData();
  }

  if (currentTime - previousHeartbeatTime >= HEARTBEAT_INTERVAL_MS) {
    previousHeartbeatTime = currentTime;
    sendHeartbeatMessage();
  }
}

// ----------------------------
// Sensor Reading
// ----------------------------

void readSensors() {
  int throttleRaw = analogRead(THROTTLE_PIN);
  int brakeRaw = analogRead(BRAKE_PIN);
  int voltageRaw = analogRead(VOLTAGE_PIN);
  int temperatureRaw = analogRead(TEMPERATURE_PIN);
  int currentRaw = analogRead(CURRENT_PIN);

  throttlePercent = convertAnalogToPercent(throttleRaw);
  brakePercent = convertAnalogToPercent(brakeRaw);

  batteryVoltage = convertAnalogToVoltage(voltageRaw);
  temperatureC = convertAnalogToTemperature(temperatureRaw);
  currentA = convertAnalogToCurrent(currentRaw);

  externalFault = digitalRead(EXTERNAL_FAULT_PIN) == LOW;
}

float convertAnalogToPercent(int rawValue) {
  return (rawValue / 1023.0) * 100.0;
}

float convertAnalogToVoltage(int rawValue) {
  float analogVoltage = (rawValue / 1023.0) * 5.0;

  /*
    Placeholder scaling:
    This assumes the measured voltage was divided down before reaching the
    microcontroller. If the divider ratio is 4 to 1, then 3.0 V at the analog
    pin represents 12.0 V at the source.
  */

  float dividerRatio = 4.0;
  return analogVoltage * dividerRatio;
}

float convertAnalogToTemperature(int rawValue) {
  /*
    Placeholder conversion:
    A real version would use a thermistor equation or lookup table.
  */

  return (rawValue / 1023.0) * 100.0;
}

float convertAnalogToCurrent(int rawValue) {
  /*
    Placeholder conversion:
    A real version would use the sensitivity of the current sensor.
  */

  return (rawValue / 1023.0) * 20.0;
}

// ----------------------------
// Fault Logic
// ----------------------------

void checkFaults() {
  voltageWarning = batteryVoltage < VOLTAGE_WARNING_THRESHOLD;
  undervoltageFault = batteryVoltage < UNDERVOLTAGE_FAULT_THRESHOLD;

  temperatureWarning = temperatureC > TEMPERATURE_WARNING_THRESHOLD;
  overtemperatureFault = temperatureC > OVERTEMPERATURE_FAULT_THRESHOLD;

  currentWarning = currentA > CURRENT_WARNING_THRESHOLD;
  overcurrentFault = currentA > OVERCURRENT_FAULT_THRESHOLD;

  sensorRangeFault =
    throttlePercent < 0.0 ||
    throttlePercent > 100.0 ||
    brakePercent < 0.0 ||
    brakePercent > 100.0;

  communicationFault = false;

  anyWarning =
    voltageWarning ||
    temperatureWarning ||
    currentWarning;

  anyCriticalFault =
    undervoltageFault ||
    overtemperatureFault ||
    overcurrentFault ||
    sensorRangeFault ||
    externalFault ||
    communicationFault;
}

// ----------------------------
// Outputs
// ----------------------------

void updateOutputs() {
  digitalWrite(STATUS_LED_PIN, HIGH);

  if (anyCriticalFault) {
    digitalWrite(FAULT_LED_PIN, HIGH);
    digitalWrite(SHUTDOWN_OUTPUT_PIN, HIGH);
  } else {
    digitalWrite(FAULT_LED_PIN, LOW);
    digitalWrite(SHUTDOWN_OUTPUT_PIN, LOW);
  }
}

// ----------------------------
// CAN Setup Placeholder
// ----------------------------

void initializeCAN() {
  /*
    Placeholder:
    A physical implementation would initialize an MCP2515 CAN controller
    or a microcontroller CAN peripheral here.
  */

  Serial.println("CAN initialization placeholder complete.");
}

// ----------------------------
// CAN Message Functions
// ----------------------------

void sendHeartbeatMessage() {
  byte data[8];

  data[0] = 1;
  data[1] = getSystemStateCode();
  data[2] = lowByte(millis() / 1000);
  data[3] = highByte(millis() / 1000);
  data[4] = 0;
  data[5] = 0;
  data[6] = 0;
  data[7] = 0;

  sendCANMessage(CAN_ID_HEARTBEAT, data, 8);
}

void sendVoltageMessage() {
  int voltageScaled = batteryVoltage * 100;

  byte data[8];

  data[0] = lowByte(voltageScaled);
  data[1] = highByte(voltageScaled);
  data[2] = voltageWarning;
  data[3] = undervoltageFault;
  data[4] = 0;
  data[5] = 0;
  data[6] = 0;
  data[7] = 0;

  sendCANMessage(CAN_ID_VOLTAGE, data, 8);
}

void sendTemperatureMessage() {
  int temperatureScaled = temperatureC * 100;

  byte data[8];

  data[0] = lowByte(temperatureScaled);
  data[1] = highByte(temperatureScaled);
  data[2] = temperatureWarning;
  data[3] = overtemperatureFault;
  data[4] = 0;
  data[5] = 0;
  data[6] = 0;
  data[7] = 0;

  sendCANMessage(CAN_ID_TEMPERATURE, data, 8);
}

void sendDriverInputsMessage() {
  int throttleScaled = throttlePercent * 100;
  int brakeScaled = brakePercent * 100;

  byte data[8];

  data[0] = lowByte(throttleScaled);
  data[1] = highByte(throttleScaled);
  data[2] = lowByte(brakeScaled);
  data[3] = highByte(brakeScaled);
  data[4] = sensorRangeFault;
  data[5] = 0;
  data[6] = 0;
  data[7] = 0;

  sendCANMessage(CAN_ID_DRIVER_INPUTS, data, 8);
}

void sendCurrentMessage() {
  int currentScaled = currentA * 100;

  byte data[8];

  data[0] = lowByte(currentScaled);
  data[1] = highByte(currentScaled);
  data[2] = currentWarning;
  data[3] = overcurrentFault;
  data[4] = 0;
  data[5] = 0;
  data[6] = 0;
  data[7] = 0;

  sendCANMessage(CAN_ID_CURRENT, data, 8);
}

void sendFaultMessage() {
  byte data[8];

  data[0] = voltageWarning;
  data[1] = undervoltageFault;
  data[2] = temperatureWarning;
  data[3] = overtemperatureFault;
  data[4] = currentWarning;
  data[5] = overcurrentFault;
  data[6] = sensorRangeFault;
  data[7] = externalFault || communicationFault;

  sendCANMessage(CAN_ID_FAULTS, data, 8);
}

void sendCANMessage(unsigned int canId, byte data[], int length) {
  /*
    Placeholder:
    Replace this function with real CAN transmission code when hardware is used.
  */

  Serial.print("CAN TX 0x");
  Serial.print(canId, HEX);
  Serial.print(" Data: ");

  for (int i = 0; i < length; i++) {
    Serial.print(data[i]);
    Serial.print(" ");
  }

  Serial.println();
}

// ----------------------------
// System State
// ----------------------------

byte getSystemStateCode() {
  if (anyCriticalFault) {
    return 2;
  }

  if (anyWarning) {
    return 1;
  }

  return 0;
}

// ----------------------------
// Debug Output
// ----------------------------

void printDebugData() {
  Serial.println();
  Serial.println("RaceCAN Firmware Debug");
  Serial.println("----------------------");

  Serial.print("Battery Voltage: ");
  Serial.print(batteryVoltage);
  Serial.println(" V");

  Serial.print("Temperature: ");
  Serial.print(temperatureC);
  Serial.println(" C");

  Serial.print("Throttle: ");
  Serial.print(throttlePercent);
  Serial.println(" percent");

  Serial.print("Brake: ");
  Serial.print(brakePercent);
  Serial.println(" percent");

  Serial.print("Current: ");
  Serial.print(currentA);
  Serial.println(" A");

  Serial.print("System State: ");

  if (anyCriticalFault) {
    Serial.println("FAULT");
  } else if (anyWarning) {
    Serial.println("WARNING");
  } else {
    Serial.println("NORMAL");
  }
}
