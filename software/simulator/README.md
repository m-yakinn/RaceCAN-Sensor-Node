# RaceCAN Simulator

This folder will contain the Python simulator for RaceCAN Digital Kit.

## Purpose

The simulator generates fake low voltage vehicle telemetry data and formats it into CAN style messages.

It allows users to test the system without physical hardware.

## Planned Features

1. Random telemetry generation
2. Normal mode
3. Warning mode
4. Fault mode
5. Fault detection logic
6. CAN style message formatting
7. Terminal output
8. Connection to dashboard
9. CSV logging support

## Planned Files

```text
simulator.py
message_encoder.py
fault_logic.py
config.py
