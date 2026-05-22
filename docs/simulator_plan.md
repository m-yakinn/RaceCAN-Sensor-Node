# Simulator Plan

This document describes the Python telemetry simulator for RaceCAN Digital Kit V1.

## Purpose

The simulator will generate fake vehicle style telemetry data to model a low voltage sensor node.

The goal is to let users understand CAN telemetry, fault detection, and dashboard behavior without needing physical hardware.

## Simulator Responsibilities

The simulator must:

1. Generate simulated sensor values
2. Apply fault detection logic
3. Package values into CAN style messages
4. Print messages to the terminal
5. Send data to the dashboard
6. Save or support CSV logging

## Simulated Signals

The simulator will generate:

1. Battery voltage
2. Temperature
3. Throttle position
4. Brake position
5. Current draw
6. External fault status
7. Heartbeat status

## Simulation Modes

V1 will support three modes.

### Normal Mode

All values stay within safe operating ranges.

Example:

| Signal | Range |
|---|---|
| Battery voltage | 11.5 to 12.6 V |
| Temperature | 25 to 45 C |
| Current draw | 0 to 10 A |
| Throttle | 0 to 90 percent |
| Brake | 0 to 80 percent |

### Warning Mode

Some values cross warning thresholds but not critical thresholds.

Example:

| Signal | Warning |
|---|---|
| Battery voltage | 10.5 to 11.0 V |
| Temperature | 50 to 60 C |
| Current draw | 12 to 15 A |

### Fault Mode

One or more values cross critical thresholds.

Example:

| Fault | Condition |
|---|---|
| Undervoltage | Battery voltage below 10.5 V |
| Overtemperature | Temperature above 60 C |
| Overcurrent | Current draw above 15 A |
| External fault | External fault equals true |

## Planned Python Files

The simulator will eventually include:

```text
software/simulator/
  simulator.py
  message_encoder.py
  fault_logic.py
  config.py
  README.md
