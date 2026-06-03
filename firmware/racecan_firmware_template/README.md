# RaceCAN Firmware Template

This folder contains an Arduino style firmware template for the RaceCAN Digital Kit.

## Purpose

The firmware template shows how a low voltage telemetry sensor node would be structured on a microcontroller.

It is designed for learning and documentation first. The current version does not require hardware to understand the logic.

## What The Firmware Does

The template models the following behavior:

1. Reads simulated analog sensor inputs
2. Converts raw analog values into engineering units
3. Checks voltage, temperature, current, and sensor faults
4. Updates status and fault outputs
5. Formats CAN style messages
6. Sends placeholder CAN messages through serial output
7. Prints debug information

## Sensor Inputs

| Signal | Pin | Purpose |
|---|---|---|
| Throttle | A0 | Simulated throttle input |
| Brake | A1 | Simulated brake input |
| Voltage | A2 | Simulated battery voltage input |
| Temperature | A3 | Simulated thermistor input |
| Current | A4 | Simulated current sensor input |
| External fault | D2 | Simulated external fault input |

## Outputs

| Output | Pin | Purpose |
|---|---|---|
| Status LED | D13 | Indicates that firmware is running |
| Fault LED | D12 | Indicates active critical fault |
| Shutdown output | D11 | Simulates shutdown signal during critical fault |

## CAN Messages

The firmware template includes functions for:

1. Heartbeat message
2. Voltage status message
3. Temperature status message
4. Driver inputs message
5. Current status message
6. Fault status message

## Hardware Note

The current CAN transmit function is a placeholder.

A future physical implementation would replace `sendCANMessage()` with code for:

1. MCP2515 CAN module
2. Built in STM32 CAN peripheral
3. Built in ESP32 TWAI CAN controller
4. Other CAN controller hardware

## Why This Matters

This firmware template connects the software simulator to real embedded system thinking.

It shows how the same telemetry signals, fault logic, and CAN message structure could eventually run on real low voltage hardware.
