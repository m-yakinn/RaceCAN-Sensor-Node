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


UPDATE:
# RaceCAN Simulator

This folder contains the Python simulator for RaceCAN Digital Kit.

## Purpose

The simulator generates fake low voltage vehicle telemetry data and formats it into CAN style messages.

It allows users to test the RaceCAN system without physical hardware.

## Current Features

1. Normal simulation mode
2. Warning simulation mode
3. Fault simulation mode
4. Battery voltage generation
5. Temperature generation
6. Throttle and brake generation
7. Current draw generation
8. External fault generation
9. Fault detection logic
10. CAN style JSON message formatting
11. Terminal output

## Files

| File | Purpose |
|---|---|
| simulator.py | Main simulator program |
| config.py | Thresholds, timing, and CAN IDs |
| fault_logic.py | Warning and fault detection |
| message_encoder.py | Converts telemetry into CAN style messages |
| requirements.txt | Python package requirements |

## How to Run

From the `software/simulator` folder, run:

```bash
python simulator.py
