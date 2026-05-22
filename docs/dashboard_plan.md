# Dashboard Plan

This document describes the RaceCAN Digital Kit V1 dashboard.

## Purpose

The dashboard will display live telemetry from the simulated sensor node.

It should help users understand how low voltage sensor data, warnings, faults, and CAN messages are monitored in a vehicle style system.

## Dashboard Responsibilities

The dashboard must:

1. Show live battery voltage
2. Show live temperature
3. Show live throttle position
4. Show live brake position
5. Show live current draw
6. Show current system state
7. Show active faults
8. Show recent CAN style messages
9. Save data to CSV

## First Dashboard Version

The first version can be a simple terminal dashboard.

It should print:

```text
RaceCAN Digital Kit Live Telemetry

Battery Voltage: 12.1 V
Temperature: 38.5 C
Throttle: 42 percent
Brake: 0 percent
Current: 7.4 A
System State: NORMAL
Active Faults: NONE
