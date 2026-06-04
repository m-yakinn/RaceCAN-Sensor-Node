# Connector Plan

This document defines the planned connectors for the RaceCAN sensor node PCB.

## Purpose

Connectors make the board easier to wire, test, and document.

For a Formula SAE style low voltage electronics system, connector planning is important because incorrect wiring can cause sensor faults, communication issues, or power problems.

## Planned Connectors

| Connector | Pins | Purpose |
|---|---:|---|
| Power input | 2 | Low voltage power and ground |
| CAN bus | 3 | CAN High, CAN Low, Ground |
| Throttle input | 3 | Power, signal, ground |
| Brake input | 3 | Power, signal, ground |
| Temperature input | 2 | Thermistor signal pair |
| Current sensor input | 3 | Power, signal, ground |
| External fault input | 2 | Fault signal and ground |
| Shutdown output | 2 | Shutdown output and ground |
| Programming/debug | 4 to 6 | Serial, reset, power, ground |

## Connector Detail

### Power Input

| Pin | Signal |
|---|---|
| 1 | VIN |
| 2 | GND |

### CAN Bus

| Pin | Signal |
|---|---|
| 1 | CAN_H |
| 2 | CAN_L |
| 3 | GND |

### Throttle Input

| Pin | Signal |
|---|---|
| 1 | 5V_SENSOR |
| 2 | THROTTLE_SIGNAL |
| 3 | GND |

### Brake Input

| Pin | Signal |
|---|---|
| 1 | 5V_SENSOR |
| 2 | BRAKE_SIGNAL |
| 3 | GND |

### Temperature Input

| Pin | Signal |
|---|---|
| 1 | TEMP_SIGNAL |
| 2 | GND |

### Current Sensor Input

| Pin | Signal |
|---|---|
| 1 | 5V_SENSOR |
| 2 | CURRENT_SIGNAL |
| 3 | GND |

### External Fault Input

| Pin | Signal |
|---|---|
| 1 | EXTERNAL_FAULT |
| 2 | GND |

### Shutdown Output

| Pin | Signal |
|---|---|
| 1 | SHUTDOWN_OUT |
| 2 | GND |

## Design Notes

1. Connectors should be clearly labeled on the PCB silkscreen.
2. Signal and ground should be placed near each other when possible.
3. Sensor connectors should have consistent pin ordering.
4. CAN connector should include ground for reference.
5. The final connector type may be JST, screw terminal, or Molex-style depending on application.
