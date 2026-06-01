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
12. Command line mode selection
13. Fixed cycle runs

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
