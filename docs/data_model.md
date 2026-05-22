# Data Model

This document defines the telemetry data used by RaceCAN Digital Kit V1.

## Telemetry Signals

| Field | Type | Unit | Description |
|---|---|---|---|
| timestamp | float | seconds | Time since simulator start |
| node_id | int | none | Sensor node identifier |
| battery_voltage | float | V | Simulated low voltage battery voltage |
| temperature_c | float | C | Simulated board or system temperature |
| throttle_percent | float | percent | Simulated throttle input |
| brake_percent | float | percent | Simulated brake input |
| current_a | float | A | Simulated current draw |
| external_fault | bool | none | Simulated external fault input |
| system_state | string | none | NORMAL, WARNING, or FAULT |

## Fault Fields

| Field | Type | Description |
|---|---|---|
| voltage_warning | bool | True when battery voltage is below warning threshold |
| undervoltage_fault | bool | True when battery voltage is below critical threshold |
| temperature_warning | bool | True when temperature is above warning threshold |
| overtemperature_fault | bool | True when temperature is above critical threshold |
| current_warning | bool | True when current is above warning threshold |
| overcurrent_fault | bool | True when current is above critical threshold |
| sensor_range_fault | bool | True when throttle or brake signal is out of range |
| communication_fault | bool | True when heartbeat is missing |
| external_fault | bool | True when external fault input is active |

## CAN Style Message Format

Each simulated CAN message will use this structure:

| Field | Type | Description |
|---|---|---|
| can_id | string | Message ID, such as 0x100 |
| name | string | Message name |
| timestamp | float | Time the message was generated |
| data | object | Message payload |

## Example Message

```json
{
  "can_id": "0x101",
  "name": "Voltage Status",
  "timestamp": 1.25,
  "data": {
    "battery_voltage": 12.1,
    "voltage_warning": false,
    "undervoltage_fault": false
  }
}
