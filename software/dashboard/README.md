# RaceCAN Dashboard

This folder contains the terminal dashboard and CSV logging tools for RaceCAN Digital Kit.

## Purpose

The dashboard displays live telemetry values, active faults, and recent CAN style messages from the simulator.

## Current Features

1. Live voltage display
2. Live temperature display
3. Live throttle display
4. Live brake display
5. Live current display
6. System state display
7. Active fault display
8. Recent CAN style message display
9. CSV logging
10. Command line mode selection
11. Fixed cycle runs

## Files

| File | Purpose |
|---|---|
| dashboard.py | Main terminal dashboard |
| csv_logger.py | Saves telemetry data to CSV |
| README.md | Dashboard documentation |

## How to Run

From the root project folder, run:

```bash
cd software/dashboard
python dashboard.py
