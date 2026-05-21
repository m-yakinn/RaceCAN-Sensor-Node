# System Architecture

RaceCAN Digital Kit models a low voltage telemetry system with four main layers.

## 1. Sensor Layer

The sensor layer represents vehicle style sensor inputs.

V1 simulated sensors:

1. Battery voltage
2. Temperature
3. Throttle position
4. Brake position
5. Current draw
6. Digital fault input

## 2. Firmware Layer

The firmware layer reads sensor values, checks for faults, formats telemetry messages, and sends data using a CAN style protocol.

Main firmware responsibilities:

1. Read sensor values
2. Filter noisy data
3. Convert raw values into engineering units
4. Detect unsafe conditions
5. Set fault flags
6. Send heartbeat messages
7. Send telemetry messages

## 3. Communication Layer

The communication layer uses a CAN style message structure.

Each message has:

1. CAN ID
2. Message name
3. Data fields
4. Update rate
5. Fault relevance

## 4. Dashboard Layer

The dashboard layer receives telemetry messages and displays system status.

Dashboard features:

1. Live battery voltage
2. Live temperature
3. Throttle and brake values
4. Fault status
5. Message log
6. CSV export

## V1 Data Flow

```text
Simulated Sensors
        ↓
Firmware Logic
        ↓
CAN Style Message Format
        ↓
Python Simulator Output
        ↓
Python Dashboard
        ↓
CSV Log File
