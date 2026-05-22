# V1 Requirements

This document defines the required behavior for RaceCAN Digital Kit V1.

## Project Goal

RaceCAN Digital Kit V1 will simulate a low voltage telemetry sensor node used in motorsports, robotics, and Formula SAE style systems.

The system will generate vehicle style sensor data, detect fault conditions, encode data into CAN style messages, display the data on a dashboard, and save logs to a CSV file.

## Functional Requirements

RaceCAN V1 must:

1. Generate simulated battery voltage data
2. Generate simulated temperature data
3. Generate simulated throttle position data
4. Generate simulated brake position data
5. Generate simulated current draw data
6. Generate heartbeat messages
7. Detect warning and fault conditions
8. Encode telemetry into CAN style messages
9. Display live telemetry values
10. Display active warnings and faults
11. Save telemetry data to CSV
12. Include documentation explaining the system

## Non Functional Requirements

RaceCAN V1 should be:

1. Easy to run on a normal laptop
2. Clear enough for beginners to understand
3. Modular enough to later connect to real hardware
4. Documented like an engineering product
5. Useful for Formula SAE, robotics, and embedded systems learners

## V1 Inputs

The simulated system will generate these inputs:

| Signal | Unit | Normal Range |
|---|---|---|
| Battery voltage | V | 11.0 to 12.6 |
| Temperature | C | 25 to 50 |
| Throttle position | Percent | 0 to 100 |
| Brake position | Percent | 0 to 100 |
| Current draw | A | 0 to 12 |
| External fault | Boolean | False or True |

## V1 Outputs

The system will output:

1. CAN style message stream
2. Live dashboard values
3. Active fault states
4. CSV telemetry log
5. Example logs for documentation

## Completion Criteria

V1 is complete when:

1. The simulator runs
2. The dashboard displays live values
3. Faults are detected correctly
4. A CSV log is created
5. Documentation explains how everything works
