# Hardware Architecture

This document explains the planned hardware architecture for the RaceCAN Digital Kit sensor node.

## Purpose

The hardware layer models a low voltage telemetry sensor node used in motorsports, robotics, and Formula SAE style systems.

The board is designed to read sensor signals, protect inputs, regulate power, communicate over CAN, and provide debug access through LEDs and test points.

## Main Hardware Blocks

RaceCAN Sensor Node hardware will include:

1. Microcontroller
2. CAN transceiver
3. Power input protection
4. Voltage regulation
5. Analog sensor inputs
6. Digital fault input
7. Status LEDs
8. Shutdown output
9. Programming/debug connector
10. Test points

## High Level Data Flow

```text
Vehicle Style Sensors
        ↓
Input Protection and Filtering
        ↓
Microcontroller ADC and GPIO
        ↓
Fault Detection Firmware
        ↓
CAN Transceiver
        ↓
CAN Bus
        ↓
Dashboard or Receiver Node

Planned Sensor Inputs
Signal	Type	Purpose
Battery voltage	Analog	Monitor low voltage supply
Temperature	Analog	Monitor board or system temperature
Throttle position	Analog	Simulate driver input
Brake position	Analog	Simulate driver input
Current draw	Analog	Monitor electrical load
External fault	Digital	Simulate external shutdown/fault signal
Planned Outputs
Output	Type	Purpose
CAN High	Communication	CAN bus differential signal
CAN Low	Communication	CAN bus differential signal
Status LED	Digital	Indicates firmware running
Fault LED	Digital	Indicates active fault
Shutdown output	Digital	Indicates critical fault condition
Design Priorities

The board should be designed for:

Easy debugging
Clear signal routing
Protected inputs
Reliable power
Clear connector labeling
Testability
Beginner-friendly assembly
Future PCB manufacturing
